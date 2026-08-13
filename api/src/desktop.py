from threading import Thread
from time import monotonic, sleep
from typing import Any
from uvicorn import Config, Server
from .log import logger
from .settings import DEBUG, HOST

STARTUP_TIMEOUT_SECONDS = 30.0
SHUTDOWN_TIMEOUT_SECONDS = 10.0
POLL_INTERVAL_SECONDS = 0.05

WINDOW_TITLE = "CIB Mango Tree API Extractor"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 860
MIN_WINDOW_WIDTH = 960
MIN_WINDOW_HEIGHT = 600


def _bound_port(server: Server) -> int:
    """Reads the port the OS actually assigned.

    Binding port 0 lets the OS pick a free one, which removes the possibility of colliding with
    whatever else the user happens to be running. Nothing else needs to know the number: the
    frontend is served from this same origin and uses relative URLs.
    """
    for bound in server.servers:
        for socket in bound.sockets:
            return int(socket.getsockname()[1])

    raise RuntimeError("server started but no socket was bound")


def serve_in_background(app: Any, port: int) -> tuple[Server, Thread, int]:
    """Starts uvicorn on a worker thread and waits until it is actually accepting connections.

    The GUI toolkit requires the main thread (Cocoa enforces this), so the server cannot have it.
    uvicorn's Server.capture_signals() already no-ops when it is not on the main thread, so no
    signal-handling workaround is needed.
    """
    config = Config(app, host=HOST, port=port, log_config=None, use_colors=DEBUG)
    server = Server(config)
    thread = Thread(target=server.run, name="uvicorn", daemon=True)

    thread.start()

    deadline = monotonic() + STARTUP_TIMEOUT_SECONDS

    while not server.started:
        if not thread.is_alive():
            raise RuntimeError("server thread exited before startup completed")

        if monotonic() > deadline:
            raise RuntimeError(
                f"server did not start within {STARTUP_TIMEOUT_SECONDS:.0f}s"
            )

        sleep(POLL_INTERVAL_SECONDS)

    return server, thread, _bound_port(server)


def stop_server(server: Server, thread: Thread) -> None:
    server.should_exit = True
    thread.join(timeout=SHUTDOWN_TIMEOUT_SECONDS)

    if thread.is_alive():
        logger.warning("server thread did not shut down cleanly within the timeout")


def run_desktop(app: Any) -> None:
    """Runs the app in a native webview window, serving on an ephemeral loopback port."""
    import webview

    server, thread, port = serve_in_background(app, 0)
    url = f"http://{HOST}:{port}"

    logger.info("serving desktop UI at %s", url)

    try:
        webview.create_window(
            WINDOW_TITLE,
            url,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            min_size=(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT),
        )
        # Blocks on the main thread until the window is closed.
        webview.start()

    finally:
        stop_server(server, thread)
