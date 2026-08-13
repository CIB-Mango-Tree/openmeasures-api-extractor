import { apiFetch } from './client';
import type { QueryResponse, CreateQueryPayload } from '@appTypes/query';
import type { APICollectionResponse, APIResponse, APIErrorCollectionResponse, ValidationError } from '@appTypes/fetch';

type AsyncAPIQueryResponse = Promise<APIResponse<QueryResponse> | APIErrorCollectionResponse<ValidationError>>;
type APIMessageResponse = APIResponse<{ message: string; }>;

const JSON_HEADERS: Record<string, string> = { 'Content-Type': 'application/json' };

export async function GETQueries(): Promise<APICollectionResponse<QueryResponse>> {
  return await apiFetch<APICollectionResponse<QueryResponse>>('/api/queries', { method: 'GET' });
}

export async function GETQuery(id: string): AsyncAPIQueryResponse {
  return await apiFetch<APIResponse<QueryResponse>>(`/api/queries/${id}`, { method: 'GET' });
}

export async function POSTQuery(data: CreateQueryPayload): AsyncAPIQueryResponse {
  // No retry: this starts an extraction and consumes the request limit, so a replayed request
  // would create a duplicate query and burn quota.
  return await apiFetch<APIResponse<QueryResponse> | APIErrorCollectionResponse<ValidationError>>(
    '/api/queries',
    {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify(data)
    },
    { allowStatuses: [422] }
  );
}

export async function PATCHQuery(id: string, status: string): AsyncAPIQueryResponse {
  return await apiFetch<APIResponse<QueryResponse> | APIErrorCollectionResponse<ValidationError>>(
    `/api/queries/${id}`,
    {
      method: 'PATCH',
      headers: JSON_HEADERS,
      body: JSON.stringify({ status: status })
    },
    { allowStatuses: [422] }
  );
}

export async function DELETEQuery(id: string): Promise<APIMessageResponse> {
  return await apiFetch<APIMessageResponse>(`/api/queries/${id}`, { method: 'DELETE' });
}
