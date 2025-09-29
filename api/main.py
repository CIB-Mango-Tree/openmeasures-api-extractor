from starlette.applications import Starlette
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
from src.endpoints import QueryEndpoint
from src.settings import HOST, PORT


def main() -> None:
    db = init_DB("sqlite://backend.db")
    emitter = AsyncIOEventEmitter()
    query_repo = QueryRepository(db)
    query_term_repo = QueryTermRepository(db)
    query_request_repo = QueryRequestRepository(db)
    query_limit_repo = QueryLimitRepository(db)
    query_service = QueryService(
        query_repo, query_term_repo, query_request_repo, query_limit_repo, emitter
    )
    query_limit_service = QueryLimitService(query_limit_repo)
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
    routes = [query_router.route("/api/queries", endpoint=QueryEndpoint)]
    app = Starlette(debug=True, routes=routes)

    run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
