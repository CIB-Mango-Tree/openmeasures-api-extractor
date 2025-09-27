from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse
from lagom import injectable
from ..services import QueryService
from ..utils.responses import OK_response, OK_collection_response, error_response
from ..utils.constants import OK, CREATED, BAD_REQUEST, NOT_FOUND, UNPROCESSABLE_CONTENT


class QueryEndpoint(HTTPEndpoint):
    async def get(
        self, request: Request, query_service: QueryService = injectable
    ) -> JSONResponse:
        return OK_collection_response(OK, query_service.get())
