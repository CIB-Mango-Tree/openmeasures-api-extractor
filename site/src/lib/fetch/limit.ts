import { apiFetch } from './client';
import type { LimitResponse } from '@appTypes/limit';
import type { APIResponse } from '@appTypes/fetch';

export async function GETLimit(): Promise<APIResponse<LimitResponse>> {
  return await apiFetch<APIResponse<LimitResponse>>('/api/limit', { method: 'GET' });
}
