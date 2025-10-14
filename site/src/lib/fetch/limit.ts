import type { Limit } from '@appTypes/limit';
import type { APIResponse } from '@appTypes/fetch';

export async function GETLimit(): Promise<APIResponse<Limit>> {
  const response: Response = await fetch(`${import.meta.env.VITE_API_URL}/api/queries`, { method: 'GET' });

  return await response.json() as APIResponse<Limit>;
}
