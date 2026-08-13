"""Exercises the HTTP failure modes around the fetch loop.

None of these paths had any coverage: previously a 429 mutated limit state that nothing verified,
and every other error hit a bare `except Exception: break` that abandoned the query mid-status.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Iterator

import httpx
import pytest

from src.services.openmeasures import MAX_ATTEMPTS, OpenMeasuresClient, RateLimited

BODY = {"hits": {"hits": [{"_id": "1", "_source": {"text": "hello"}}]}}


class _Stub:
    """Replays a scripted sequence of responses and counts the requests it received."""

    def __init__(self, script: list[int]) -> None:
        self.script = script
        self.requests = 0
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "_Stub":
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - name fixed by BaseHTTPRequestHandler
                index = min(stub.requests, len(stub.script) - 1)
                status = stub.script[index]
                stub.requests += 1

                payload = json.dumps(BODY).encode()

                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *_: Any) -> None:
                return

        self._server = HTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

        return self

    def __exit__(self, *_: Any) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()

    @property
    def url(self) -> str:
        assert self._server is not None
        return f"http://127.0.0.1:{self._server.server_address[1]}/content"


@pytest.fixture
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Backoff is real time; the tests only care that retries happen."""
    monkeypatch.setattr("src.services.openmeasures.sleep", lambda _: None)
    yield


def test_returns_payload_on_success() -> None:
    with _Stub([200]) as stub:
        client = OpenMeasuresClient(stub.url)

        assert client.fetch({}) == BODY
        assert stub.requests == 1

        client.close()


def test_raises_rate_limited_on_429_without_retrying() -> None:
    """429 means the quota is gone; retrying would only burn time and hit it again."""
    with _Stub([429]) as stub:
        client = OpenMeasuresClient(stub.url)

        with pytest.raises(RateLimited):
            client.fetch({})

        assert stub.requests == 1

        client.close()


def test_retries_5xx_then_succeeds(no_sleep: None) -> None:
    with _Stub([500, 503, 200]) as stub:
        client = OpenMeasuresClient(stub.url)

        assert client.fetch({}) == BODY
        assert stub.requests == 3

        client.close()


def test_gives_up_after_max_attempts(no_sleep: None) -> None:
    with _Stub([500]) as stub:
        client = OpenMeasuresClient(stub.url)

        with pytest.raises(httpx.HTTPStatusError):
            client.fetch({})

        assert stub.requests == MAX_ATTEMPTS

        client.close()


def test_does_not_retry_client_errors(no_sleep: None) -> None:
    with _Stub([400]) as stub:
        client = OpenMeasuresClient(stub.url)

        with pytest.raises(httpx.HTTPStatusError):
            client.fetch({})

        assert stub.requests == 1

        client.close()


def test_retries_transport_errors(no_sleep: None) -> None:
    """A connection failure used to abandon the whole query."""
    attempts = {"count": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        attempts["count"] += 1

        if attempts["count"] < 3:
            raise httpx.ConnectError("boom")

        return httpx.Response(200, json=BODY)

    transport = httpx.MockTransport(handler)
    client = OpenMeasuresClient(
        "http://example.invalid/content", client=httpx.Client(transport=transport)
    )

    assert client.fetch({}) == BODY
    assert attempts["count"] == 3

    client.close()


def test_timeout_is_explicit_not_the_httpx_default() -> None:
    """httpx defaults to 5s for everything, which would cut off a large page mid-download."""
    from src.services.openmeasures import TIMEOUT

    assert TIMEOUT.read is not None and TIMEOUT.read > 5.0
    assert TIMEOUT.connect is not None
