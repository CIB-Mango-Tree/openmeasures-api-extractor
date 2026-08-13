from collections.abc import AsyncGenerator
from asyncio import CancelledError, Task, sleep, create_task, to_thread
from contextlib import asynccontextmanager
from typing import Any
from starlette.applications import Starlette
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from uvicorn import run
from pyventus.events import AsyncIOEventEmitter
from src.db.connection import init_DB
from src.db.repositories import (
    QueryRepository,
    QueryTermRepository,
    QueryRequestRepository,
    QueryLimitRepository,
)
from src.services import (
    QueryService,
    QueryLimitService,
    QueryExportService,
    WebSocketService,
)
from src.endpoints import (
    Home,
    QueriesEndpoint,
    QueryEndpoint,
    QueryLimitEndpoint,
    QueryExportEndpoint,
    UpdateStreamEndpoint,
    PlatformsEndpoint,
)
from src.middleware import DiagnosticsMiddleware
from src.desktop import run_desktop
from src.spa import SPAStaticFiles, mount_path
from src.settings import HOST, PORT, DATABASE_URL, DEBUG, HEADLESS, SPA_DIR
from src.log import logger
import src.utils.user_dir


async def refresh_limit_task(limit_service: QueryLimitService) -> None:
    while True:
        try:
            await to_thread(limit_service.maintain_and_check)
            await sleep(60)

        except Exception as e:
            logger.error("Error in refresh_limit_task: %s", e, exc_info=True)
            await sleep(60)


def main() -> None:
    db = init_DB(DATABASE_URL)
    emitter = AsyncIOEventEmitter()
    query_repo = QueryRepository(db)
    query_term_repo = QueryTermRepository(db)
    query_request_repo = QueryRequestRepository(db)
    query_limit_repo = QueryLimitRepository(db)
    query_service = QueryService(
        query_repo, query_term_repo, query_request_repo, query_limit_repo, emitter
    )
    query_limit_service = QueryLimitService(query_limit_repo, emitter)
    query_export_service = QueryExportService(query_repo)
    websocket_service = WebSocketService(query_repo)
    routes = [
        Route("/api/queries", endpoint=QueriesEndpoint),
        Route("/api/queries/{id:uuid}", endpoint=QueryEndpoint),
        Route(
            "/api/queries/{id:uuid}/download/{format:str}", endpoint=QueryExportEndpoint
        ),
        Route("/api/limit", endpoint=QueryLimitEndpoint),
        WebSocketRoute("/api/ws/updates", endpoint=UpdateStreamEndpoint),
        Route("/api/platforms", endpoint=PlatformsEndpoint),
        Route("/api/health", endpoint=Home),
    ]

    # Registered last and deliberately so: a Mount at "/" matches everything, so it would
    # swallow the API routes if it came first.
    spa_dir = mount_path(SPA_DIR)

    if spa_dir is not None:
        routes.append(Mount("/", app=SPAStaticFiles(directory=spa_dir, html=True)))

    @asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncGenerator[Any, Any]:
        task: Task[None] = create_task(refresh_limit_task(query_limit_service))

        try:
            yield

        finally:
            task.cancel()

            try:
                await task

            # CancelledError derives from BaseException, not Exception, so catching Exception
            # here let it escape and every shutdown ended in "Application shutdown failed".
            except CancelledError:
                pass

            except Exception:
                logger.error("error while shutting down refresh task", exc_info=True)

    # Each service is a single instance built above, so the endpoints read them straight off
    # app.state rather than through a DI container.
    app = Starlette(
        debug=DEBUG,
        routes=routes,
        lifespan=lifespan,
        middleware=[
            Middleware(DiagnosticsMiddleware),
            Middleware(
                CORSMiddleware,
                allow_origin_regex=r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$",
                allow_methods=["*"],
                allow_headers=["*"],
            )
        ],
    )

    app.state.query_service = query_service
    app.state.limit_service = query_limit_service
    app.state.export_service = query_export_service
    app.state.websocket_service = websocket_service

    if HEADLESS:
        run(app, host=HOST, port=PORT, use_colors=DEBUG, log_config=None)
        return

    run_desktop(app)


if __name__ == "__main__":
    main()
