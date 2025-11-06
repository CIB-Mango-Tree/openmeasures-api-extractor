import type { LimitResponse } from '@appTypes/limit';
import type { APIResponse } from '@appTypes/fetch';

export async function GETLimit(): Promise<APIResponse<LimitResponse>> {
  const response: Response = await fetch(`${import.meta.env.VITE_API_URL}/api/limit`, { method: 'GET' });

  return await response.json() as APIResponse<LimitResponse>;
}
