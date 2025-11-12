import type { APICollectionResponse } from '@appTypes/fetch';
import type { Platform } from '@appTypes/platform';

export async function GETPlatforms(): Promise<APICollectionResponse<Platform>> {
  const response: Response = await fetch(`${import.meta.env.VITE_API_URL}/api/platforms`, { method: 'GET' });

  return await response.json() as APICollectionResponse<Platform>;
}
