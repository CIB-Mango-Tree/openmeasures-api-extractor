const RETRYABLE_STATUSES: Set<number> = new Set([502, 503, 504]);

export class ApiError extends Error {
  public readonly status: number;
  public readonly body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);

    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }

  // Distinguishes "the extractor service isn't up" from "the service said no", which is the
  // difference between a retry-able cold start and a real error worth showing the user.
  public get isUnreachable(): boolean {
    return this.status === 0;
  }
}

/**
 * Whether a failure is worth another attempt.
 *
 * Retrying is TanStack Query's job -- this only classifies the error, so the backoff policy lives
 * in one place (`query-client.ts`) instead of being duplicated per call site.
 */
export function isRetryableError(error: unknown): boolean {
  if (!(error instanceof ApiError)) return false;

  return error.isUnreachable || RETRYABLE_STATUSES.has(error.status);
}

export type ApiFetchOptions = {
  /** Statuses to return as a normal body instead of throwing (e.g. 422 validation errors). */
  allowStatuses?: Array<number>;
};

// A backend that returns an HTML error page would make response.json() throw a SyntaxError that
// reads like a bug in our own code. Parse defensively and keep the raw text as the body.
async function parseBody(response: Response): Promise<unknown> {
  const text: string = await response.text();

  if (text.length === 0) return null;

  try {
    return JSON.parse(text);

  } catch {
    return text;
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}, options: ApiFetchOptions = {}): Promise<T> {
  const method: string = (init.method ?? 'GET').toUpperCase();
  const allowStatuses: Array<number> = options.allowStatuses ?? [];

  let response: Response;

  try {
    response = await fetch(path, init);

  } catch {
    // fetch only rejects on network-level failures, which here means the local backend is not
    // listening yet -- the cold-start race on app launch.
    throw new ApiError(`Could not reach ${path}`, 0, null);
  }

  if (response.ok || allowStatuses.includes(response.status)) {
    return await parseBody(response) as T;
  }

  throw new ApiError(
    `${method} ${path} failed with status ${response.status}`,
    response.status,
    await parseBody(response)
  );
}
