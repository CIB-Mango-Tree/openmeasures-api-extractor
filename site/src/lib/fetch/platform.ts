import { apiFetch } from './client';
import type { APICollectionResponse } from '@appTypes/fetch';
import type { Platform } from '@appTypes/platform';

export async function GETPlatforms(): Promise<APICollectionResponse<Platform>> {
  return await apiFetch<APICollectionResponse<Platform>>('/api/platforms', { method: 'GET' });
}
