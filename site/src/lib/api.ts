import { useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { GETQueries, POSTQuery, PATCHQuery } from '@lib/fetch/query';
import { GETLimit } from '@lib/fetch/limit';
import { GETPlatforms } from '@lib/fetch/platform';
import { mapResponseToQuery, mapResponseToLimit } from '@lib/map';
import type { QueryClient, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import type { Query, QueryResponse, CreateQueryPayload } from '@appTypes/query';
import type { Limit } from '@appTypes/limit';
import type { Platform } from '@appTypes/platform';
import type { APIResponse, APIErrorCollectionResponse, ValidationError } from '@appTypes/fetch';

export type QueryMutationResponse = APIResponse<QueryResponse> | APIErrorCollectionResponse<ValidationError>;
export type UpdateStatusVariables = { id: string; status: string; };

export const queryKeys = {
  queries: ['queries'] as const,
  limit: ['limit'] as const,
  platforms: ['platforms'] as const,
};

/** Matches the daily allowance the backend enforces; shown before the first read resolves. */
const DEFAULT_LIMIT: Limit = { count: 39, previousRequestDate: null, limitRefreshDate: null };

async function fetchQueries(): Promise<Array<Query>> {
  const response = await GETQueries();

  return response.data.map(mapResponseToQuery);
}

/** Server-assigned timestamps, so this compares one clock against itself. */
function isStale(incoming: Query, existing: Query | undefined): boolean {
  if (existing == null || existing.updatedAt == null || incoming.updatedAt == null) return false;

  return new Date(incoming.updatedAt).getTime() < new Date(existing.updatedAt).getTime();
}

/**
 * Writes a single query into the cached list.
 *
 * This is the one place server-pushed updates land, so the table, the progress card and the
 * details dialog all re-render from the same object -- previously each held its own copy and
 * every WebSocket handler had to remember to update all three.
 *
 * Pushed events and HTTP responses race: a PATCH reply describes the query as it was when the
 * request was handled, while the socket may already have delivered a newer state. Dropping the
 * older of the two keeps a slow response from resurrecting a status the backend has moved past.
 */
export function cacheQuery(client: QueryClient, query: Query): void {
  client.setQueryData<Array<Query>>(queryKeys.queries, (current): Array<Query> => {
    if (current == null) return [query];

    const existing: Query | undefined = current.find((item: Query): boolean => item.id === query.id);

    if (existing == null) return [query, ...current];
    if (isStale(query, existing)) return current;

    return current.map((item: Query): Query => item.id === query.id ? query : item);
  });
}

export function cacheLimit(client: QueryClient, limit: Limit): void {
  client.setQueryData(queryKeys.limit, limit);
}

export function useQueryList(): UseQueryResult<Array<Query>> {
  return useQuery({ queryKey: queryKeys.queries, queryFn: fetchQueries });
}

/** Reads one query out of the cached list, so callers can hold an id rather than a stale copy. */
export function useQueryByID(id: string | null): Query | null {
  const select = useCallback(
    (queries: Array<Query>): Query | null => (
      queries.find((item: Query): boolean => item.id === id) ?? null
    ),
    [id]
  );
  const { data } = useQuery({ queryKey: queryKeys.queries, queryFn: fetchQueries, select });

  return id == null ? null : data ?? null;
}

export function useLimitQuery(): UseQueryResult<Limit> {
  return useQuery({
    queryKey: queryKeys.limit,
    queryFn: async (): Promise<Limit> => mapResponseToLimit((await GETLimit()).data),
  });
}

export function useLimit(): Limit {
  const { data } = useLimitQuery();

  return data ?? DEFAULT_LIMIT;
}

export function usePlatforms(): UseQueryResult<Array<Platform>> {
  return useQuery({
    queryKey: queryKeys.platforms,
    queryFn: async (): Promise<Array<Platform>> => (await GETPlatforms()).data,
    // The platform list is compiled into the backend, so it cannot change while the app runs.
    staleTime: Infinity,
  });
}

export function useCreateQuery(): UseMutationResult<QueryMutationResponse, Error, CreateQueryPayload> {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateQueryPayload): Promise<QueryMutationResponse> => POSTQuery(payload),
    onSuccess: (response: QueryMutationResponse): void => {
      // 422 comes back as a normal body rather than a throw, so it reaches here as a success.
      if (response.code !== 200) return;

      cacheQuery(client, mapResponseToQuery((response as APIResponse<QueryResponse>).data));
      // Starting an extraction spends at least one request from the daily allowance.
      void client.invalidateQueries({ queryKey: queryKeys.limit });
    },
  });
}

export function useUpdateQueryStatus(): UseMutationResult<QueryMutationResponse, Error, UpdateStatusVariables> {
  const client = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status }: UpdateStatusVariables): Promise<QueryMutationResponse> => PATCHQuery(id, status),
    onSuccess: (response: QueryMutationResponse): void => {
      if (response.code !== 200) return;

      cacheQuery(client, mapResponseToQuery((response as APIResponse<QueryResponse>).data));
    },
  });
}
