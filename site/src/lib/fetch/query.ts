import type { QueryResponse, CreateQueryPayload } from '@appTypes/query';
import type { APICollectionResponse, APIResponse, APIErrorCollectionResponse, ValidationError } from '@appTypes/fetch';

type AsyncAPIQueryResponse = Promise<APIResponse<QueryResponse> | APIErrorCollectionResponse<ValidationError>>;
type APIMessageResponse = APIResponse<{ message: string; }>;

export async function GETQueries(): Promise<APICollectionResponse<QueryResponse>> {
  const response: Response = await fetch(`${import.meta.env.VITE_API_URL}/api/queries`, { method: 'GET' });

  return await response.json() as APICollectionResponse<QueryResponse>;
}

export async function GETQuery(id: string): AsyncAPIQueryResponse {
  const response: Response = await fetch(`${import.meta.env.VITE_API_URL}/api/queries/${id}`, { method: 'GET' });

  return await response.json() as APIResponse<QueryResponse>;
}

export async function POSTQuery(data: CreateQueryPayload): AsyncAPIQueryResponse {
  const response: Response = await fetch(`${import.meta.env.VITE_API_URL}/api/queries`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  });

  if (response.status === 422) return await response.json() as APIErrorCollectionResponse<ValidationError>;

  return await response.json() as APIResponse<QueryResponse>;
}

export async function PATCHQuery(id: string, status: string): AsyncAPIQueryResponse {
  const response: Response = await fetch(`${import.meta.env.VITE_API_URL}/api/queries/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ status: status })
  });

  return await response.json() as APIResponse<QueryResponse>;
}

export async function DELETEQuery(id: string): Promise<APIMessageResponse> {
  const response: Response = await fetch(`${import.meta.env.VITE_API_URL}/api/queries/${id}`, { method: 'DELETE' });

  return await response.json() as APIMessageResponse;
}
