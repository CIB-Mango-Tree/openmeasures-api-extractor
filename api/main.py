from collections.abc import AsyncGenerator
from asyncio import Task, sleep, create_task, to_thread
from contextlib import asynccontextmanager
from typing import Any
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from uvicorn import run
from pyventus.events import AsyncIOEventEmitter
from lagom import Container
from lagom.integrations.starlette import StarletteIntegration
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
    QueriesEndpoint,
    QueryEndpoint,
    QueryLimitEndpoint,
    QueryExportEndpoint,
    UpdateStreamEndpoint,
    PlatformsEndpoint,
)
from src.settings import HOST, PORT, DATABASE_URL, DEBUG
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
    query_container = Container()
    query_limit_container = Container()
    query_export_container = Container()
    websocket_container = Container()
    query_container[QueryService] = query_service
    query_limit_container[QueryLimitService] = query_limit_service
    query_export_container[QueryExportService] = query_export_service
    websocket_container[WebSocketService] = websocket_service
    query_router = StarletteIntegration(query_container)
    query_limit_router = StarletteIntegration(query_limit_container)
    query_export_router = StarletteIntegration(query_export_container)
    websocket_router = StarletteIntegration(websocket_container)
    routes = [
        query_router.route("/api/queries", endpoint=QueriesEndpoint),
        query_router.route("/api/queries/{id:uuid}", endpoint=QueryEndpoint),
        query_export_router.route(
            "/api/queries/{id:uuid}/download/{format:str}", endpoint=QueryExportEndpoint
        ),
        query_limit_router.route("/api/limit", endpoint=QueryLimitEndpoint),
        websocket_router.ws_route("/api/ws/updates", endpoint=UpdateStreamEndpoint),
        Route("/api/platforms", endpoint=PlatformsEndpoint),
    ]

    @asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncGenerator[Any, Any]:
        task: Task[None] = create_task(refresh_limit_task(query_limit_service))

        try:
            yield

        finally:
            task.cancel()

            try:
                await task
            except Exception:
                pass

    app = Starlette(
        debug=DEBUG,
        routes=routes,
        lifespan=lifespan,
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            )
        ],
    )
    run(app, host=HOST, port=PORT, use_colors=DEBUG, log_config=None)


if __name__ == "__main__":
    main()
