from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse
from ..services import QueryLimitService
from ..serializers import QueryLimitSerializer
from ..utils.responses import OK_response
from ..utils.constants import OK


class QueryLimitEndpoint(HTTPEndpoint):
    async def get(self, request: Request) -> JSONResponse:
        limit_service: QueryLimitService = request.app.state.limit_service
        limit = limit_service.get()

        if limit is None:
            return OK_response(
                OK,
                {
                    "count": 39,
                    "percentage": 0.0,
                    "previous_request_date": None,
                    "limit_refresh_date": None,
                },
            )

        return OK_response(OK, QueryLimitSerializer.convert_model_to_dict(limit))
