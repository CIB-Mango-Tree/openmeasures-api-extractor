const RETRYABLE_STATUSES: Set<number> = new Set([502, 503, 504]);
const BASE_DELAY_MS = 300;
const MAX_DELAY_MS = 5000;
const DEFAULT_ATTEMPTS = 6;

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

export type ApiFetchOptions = {
  /** Defaults to true for GET/HEAD and false otherwise: POST /api/queries starts an extraction
   *  and consumes the request limit, so it must never be replayed automatically. */
  retry?: boolean;
  /** Statuses to return as a normal body instead of throwing (e.g. 422 validation errors). */
  allowStatuses?: Array<number>;
  attempts?: number;
};

function delay(ms: number): Promise<void> {
  return new Promise((resolve): void => {
    setTimeout(resolve, ms);
  });
}

function backoffDelay(attempt: number): number {
  const exponential: number = Math.min(BASE_DELAY_MS * 2 ** attempt, MAX_DELAY_MS);

  return exponential * (0.75 + Math.random() * 0.5);
}

// A failing Nitro proxy hop returns an HTML error page, so response.json() throws a SyntaxError
// that reads like a bug in our own code. Parse defensively and keep the raw text as the body.
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
  const retry: boolean = options.retry ?? (method === 'GET' || method === 'HEAD');
  const attempts: number = options.attempts ?? (retry ? DEFAULT_ATTEMPTS : 1);
  const allowStatuses: Array<number> = options.allowStatuses ?? [];

  let lastError: ApiError = new ApiError(`${method} ${path} was never attempted`, 0, null);

  for (let attempt = 0; attempt < attempts; attempt++) {
    if (attempt > 0) await delay(backoffDelay(attempt - 1));

    let response: Response;

    try {
      response = await fetch(path, init);

    } catch {
      // fetch only rejects on network-level failures. In the packaged app that means Nitro could
      // not reach the backend on 127.0.0.1:8000 yet - the cold-start race.
      lastError = new ApiError(`Could not reach ${path}`, 0, null);

      if (!retry) throw lastError;
      continue;
    }

    if (response.ok || allowStatuses.includes(response.status)) {
      return await parseBody(response) as T;
    }

    lastError = new ApiError(
      `${method} ${path} failed with status ${response.status}`,
      response.status,
      await parseBody(response)
    );

    if (!retry || !RETRYABLE_STATUSES.has(response.status)) throw lastError;
  }

  throw lastError;
}
