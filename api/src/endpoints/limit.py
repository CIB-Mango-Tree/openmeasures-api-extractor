from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse
from lagom import injectable
from ..services import QueryLimitService
from ..serializers import QueryLimitSerializer
from ..utils.responses import OK_response
from ..utils.constants import OK


class QueryLimitEndpoint(HTTPEndpoint):
    async def get(
        self, request: Request, limit_service: QueryLimitService = injectable
    ) -> JSONResponse:
        limit = limit_service.get()

        if limit is None:
            return OK_response(
                OK,
                {
                    "count": 39,
                    "percentage": 0.0,
                    "previous_request_date": "",
                    "limit_refresh_date": "",
                },
            )

        limit_model = QueryLimitSerializer.model_validate(limit)

        return OK_response(OK, limit_model.model_dump())
