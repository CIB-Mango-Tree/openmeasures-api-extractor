import type { Query } from '@appTypes/query';
import type { APICollectionResponse, APIResponse } from '@appTypes/fetch';

type AsyncAPIQueryResponse = Promise<APIResponse<Query>>;
type APIMessageResponse = APIResponse<{ message: string; }>;

export async function GETQueries(): Promise<APICollectionResponse<Query>> {
  const response: Response = await fetch(`${import.meta.env.VITE_API_URL}/api/queries`, { method: 'GET' });

  return await response.json() as APICollectionResponse<Query>;
}

export async function GETQuery(id: string): AsyncAPIQueryResponse {
  const response: Response = await fetch(`${import.meta.env.VITE_API_URL}/api/queries/${id}`, { method: 'GET' });

  return await response.json() as APIResponse<Query>;
}

export async function POSTQuery(data): AsyncAPIQueryResponse { }

export async function PATCHQuery(id: string, status: string): AsyncAPIQueryResponse {
  const response: Response = await fetch(`${import.meta.env.VITE_API_URL}/api/queries/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ status: status })
  });

  return await response.json() as APIResponse<Query>;
}

export async function DELETEQuery(id: string): Promise<APIMessageResponse> {
  const response: Response = await fetch(`${import.meta.env.VITE_API_URL}/api/queries/${id}`, { method: 'DELETE' });

  return await response.json() as APIMessageResponse;
}
