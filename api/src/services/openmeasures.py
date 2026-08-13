from random import uniform
from time import sleep
from typing import Any
import httpx
from ..log import logger

# The previous implementation called requests.get with no timeout at all, so a stalled socket
# blocked the extraction worker indefinitely. httpx applies a 5s default to everything, which is
# far too tight for a 10,000-hit page, so the values are set explicitly.
TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)

MAX_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 1.0
BACKOFF_MAX_SECONDS = 15.0

RETRYABLE_STATUSES = frozenset({500, 502, 503, 504})


class RateLimited(Exception):
    """The API reported the request quota is exhausted (HTTP 429)."""


def _backoff(attempt: int) -> float:
    delay = min(BACKOFF_BASE_SECONDS * 2**attempt, BACKOFF_MAX_SECONDS)

    return delay * uniform(0.75, 1.25)


class OpenMeasuresClient:
    """Thin wrapper over a long-lived httpx.Client.

    Deliberately synchronous: the fetch loop runs on a worker thread via asyncio.to_thread, and
    the repositories around it are blocking SQLAlchemy. Using AsyncClient would only move the
    blocking onto the event loop.
    """

    def __init__(self, base_url: str, client: httpx.Client | None = None) -> None:
        self._base_url = base_url
        # One client for the whole run: the old code opened a fresh TCP and TLS connection for
        # every page of every query.
        self._client = client or httpx.Client(timeout=TIMEOUT, follow_redirects=False)

    def close(self) -> None:
        self._client.close()

    def fetch(self, params: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None

        for attempt in range(MAX_ATTEMPTS):
            if attempt > 0:
                delay = _backoff(attempt - 1)

                logger.warning(
                    "retrying OpenMeasures request in %.1fs (attempt %d/%d)",
                    delay,
                    attempt + 1,
                    MAX_ATTEMPTS,
                )
                sleep(delay)

            try:
                response = self._client.get(self._base_url, params=params)

            except httpx.TransportError as error:
                # Connection reset, DNS blip, timeout. Previously any of these aborted the whole
                # query and left it stuck mid-status.
                last_error = error
                continue

            if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
                raise RateLimited("OpenMeasures request quota exhausted")

            if response.status_code in RETRYABLE_STATUSES:
                last_error = httpx.HTTPStatusError(
                    f"server returned {response.status_code}",
                    request=response.request,
                    response=response,
                )
                continue

            # Anything else non-2xx is a genuine error and is not worth retrying.
            response.raise_for_status()

            return dict(response.json())

        raise last_error if last_error is not None else RuntimeError("request failed")
