import type { APICollectionResponse } from '@appTypes/fetch';
import type { Platform } from '@appTypes/platform';

export async function GETPlatforms(): Promise<APICollectionResponse<Platform>> {
  const response: Response = await fetch('/api/platforms', { method: 'GET' });

  return await response.json() as APICollectionResponse<Platform>;
}
