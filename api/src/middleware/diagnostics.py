from typing import Any, Callable, Awaitable
from ..log import diagnostics_logger

Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]

# Headers whose values pinpoint the localhost/127.0.0.1 origin mismatch we're chasing.
_HEADERS_OF_INTEREST = (b"origin", b"host", b"x-forwarded-for", b"x-forwarded-host")


def _address_family(host: str | None) -> str:
    if not host:
        return "unknown"
    if host == "::1" or ":" in host:
        return "IPv6"
    return "IPv4"


class DiagnosticsMiddleware:
    """Pure-ASGI middleware that logs the connection details of every HTTP request and
    WebSocket upgrade (origin/host headers, client address + family). Registered
    outermost so it observes traffic before any other middleware can short-circuit it.
    """

    def __init__(self, app: Callable[[Scope, Receive, Send], Awaitable[None]]) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope_type = scope.get("type")

        if scope_type in ("http", "websocket"):
            client = scope.get("client") or (None, None)
            client_host = client[0]
            headers = {
                key.decode("latin-1"): value.decode("latin-1")
                for key, value in scope.get("headers", [])
                if key.lower() in _HEADERS_OF_INTEREST
            }
            diagnostics_logger.info(
                "%s %s scheme=%s client=%s family=%s headers=%s",
                scope_type,
                scope.get("path", ""),
                scope.get("scheme", ""),
                client_host,
                _address_family(client_host),
                headers,
            )

        await self.app(scope, receive, send)
