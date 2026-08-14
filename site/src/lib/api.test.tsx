import { describe, expect, test, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cacheQuery, queryKeys, useQueryByID } from '@lib/api';
import { QUERY_COMPLETE, PARSE_IN_PROGRESS } from '@constants/status';
import type { ReactElement, ReactNode } from 'react';
import type { Query } from '@appTypes/query';

function makeQuery(id: string, status: string): Query {
  return {
    id,
    createdAt: new Date(),
    updatedAt: new Date(),
    platform: 'bluesky',
    status,
    timezone: 'UTC',
    startDate: new Date(),
    endDate: new Date(),
    rowsFetched: 10,
    queriesUsed: 1,
    percentage: 0.4,
    terms: [],
  } as unknown as Query;
}

function makeClient(): QueryClient {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0 } },
  });
}

function wrapper(client: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }): ReactElement {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe('cacheQuery', (): void => {
  let client: QueryClient;

  beforeEach((): void => {
    client = makeClient();
  });

  test('replaces the matching query in the list, leaving order intact', (): void => {
    client.setQueryData(queryKeys.queries, [
      makeQuery('a', QUERY_COMPLETE),
      makeQuery('b', PARSE_IN_PROGRESS),
      makeQuery('c', QUERY_COMPLETE),
    ]);

    cacheQuery(client, makeQuery('b', QUERY_COMPLETE));

    const list = client.getQueryData<Array<Query>>(queryKeys.queries) as Array<Query>;

    expect(list.map((item: Query): string => item.id)).toEqual(['a', 'b', 'c']);
    expect(list[1].status).toBe(QUERY_COMPLETE);
  });

  test('prepends a query the list has not seen, so a new extraction shows up first', (): void => {
    // The list is ordered newest-first by the backend, which is what issue #15 fixed.
    client.setQueryData(queryKeys.queries, [makeQuery('a', QUERY_COMPLETE)]);

    cacheQuery(client, makeQuery('new', PARSE_IN_PROGRESS));

    const list = client.getQueryData<Array<Query>>(queryKeys.queries) as Array<Query>;

    expect(list.map((item: Query): string => item.id)).toEqual(['new', 'a']);
  });

  test('does not drop the update when nothing has been loaded yet', (): void => {
    cacheQuery(client, makeQuery('a', QUERY_COMPLETE));

    expect(client.getQueryData<Array<Query>>(queryKeys.queries)).toHaveLength(1);
  });
});

describe('useQueryByID', (): void => {
  test('reads the query out of the cached list rather than refetching it', async (): Promise<void> => {
    const client = makeClient();

    client.setQueryData(queryKeys.queries, [makeQuery('a', QUERY_COMPLETE), makeQuery('b', PARSE_IN_PROGRESS)]);

    const { result } = renderHook((): Query | null => useQueryByID('b'), { wrapper: wrapper(client) });

    await waitFor((): void => {
      expect(result.current?.id).toBe('b');
    });
    expect(result.current?.status).toBe(PARSE_IN_PROGRESS);
  });

  test('returns null for an id that is not in the list', async (): Promise<void> => {
    const client = makeClient();

    client.setQueryData(queryKeys.queries, [makeQuery('a', QUERY_COMPLETE)]);

    const { result } = renderHook((): Query | null => useQueryByID('missing'), { wrapper: wrapper(client) });

    await waitFor((): void => {
      expect(result.current).toBeNull();
    });
  });
});

describe('staleness', (): void => {
  test('an update older than what is cached is ignored', (): void => {
    const client = makeClient();
    const newer: Query = { ...makeQuery('a', QUERY_COMPLETE), updatedAt: new Date('2026-08-13T10:00:05') };
    const older: Query = { ...makeQuery('a', PARSE_IN_PROGRESS), updatedAt: new Date('2026-08-13T10:00:01') };

    client.setQueryData(queryKeys.queries, [newer]);
    cacheQuery(client, older);

    const list = client.getQueryData<Array<Query>>(queryKeys.queries) as Array<Query>;

    expect(list[0].status).toBe(QUERY_COMPLETE);
  });

  test('an update with no timestamp to compare is still applied', (): void => {
    const client = makeClient();
    const existing: Query = { ...makeQuery('a', PARSE_IN_PROGRESS), updatedAt: null };

    client.setQueryData(queryKeys.queries, [existing]);
    cacheQuery(client, { ...makeQuery('a', QUERY_COMPLETE), updatedAt: null });

    const list = client.getQueryData<Array<Query>>(queryKeys.queries) as Array<Query>;

    expect(list[0].status).toBe(QUERY_COMPLETE);
  });
});
