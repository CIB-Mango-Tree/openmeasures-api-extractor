import { QueryClient } from '@tanstack/react-query';
import { isRetryableError } from '@lib/fetch/client';

const MAX_RETRIES = 5;
const BASE_DELAY_MS = 300;
const MAX_DELAY_MS = 5000;

export const queryClient: QueryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // The backend is a local process launched alongside the window, so the first requests can
      // land before it is listening. Retry those and 5xx, never a 4xx -- the service said no.
      retry: (failureCount: number, error: Error): boolean => (
        failureCount < MAX_RETRIES && isRetryableError(error)
      ),
      retryDelay: (attempt: number): number => (
        Math.min(BASE_DELAY_MS * 2 ** attempt, MAX_DELAY_MS) * (0.75 + Math.random() * 0.5)
      ),
      // Progress arrives over the WebSocket and is written straight into the cache, so the cached
      // data is push-fresh rather than poll-fresh. Refetching on focus would mostly re-request
      // what we already hold, and could briefly clobber a newer pushed update with a slower read.
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
    mutations: {
      // POST /api/queries starts an extraction and consumes daily quota, so a replayed request
      // would create a duplicate query and burn a request the user cannot get back.
      retry: false,
    },
  },
});
