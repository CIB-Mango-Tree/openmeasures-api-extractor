from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse
from lagom import injectable
from pydantic import ValidationError
from ..services import QueryService
from ..serializers import QuerySerializer
from ..validator import (
    ParamValidator,
    CreateQueryValidator,
    UpdateQueryValidator,
    DeleteQueriesValidator,
)
from ..utils.responses import OK_response, OK_collection_response, error_response
from ..utils.constants import OK, CREATED, NOT_FOUND, UNPROCESSABLE_CONTENT


class QueriesEndpoint(HTTPEndpoint):
    async def get(
        self, _: Request, query_service: QueryService = injectable
    ) -> JSONResponse:
        queries = query_service.get()

        return OK_collection_response(
            OK, QuerySerializer.convert_models_to_dict(queries)
        )

    async def post(
        self, request: Request, query_service: QueryService = injectable
    ) -> JSONResponse:
        try:
            body = await request.json()
            validator_data = CreateQueryValidator.model_validate(body)
            query = query_service.create(validator_data)

            return OK_response(CREATED, QuerySerializer.convert_model_to_dict(query))

        except ValidationError as err:
            return error_response(
                UNPROCESSABLE_CONTENT,
                err.errors(include_url=False, include_input=False),
            )

    async def delete(
        self, request: Request, query_service: QueryService = injectable
    ) -> JSONResponse:
        try:
            body = await request.json()
            validator_data = DeleteQueriesValidator.model_validate(body)

            query_service.batch_delete(validator_data)

            return OK_response(OK, {"message": "queries were deleted successfully"})

        except ValidationError as err:
            return error_response(
                UNPROCESSABLE_CONTENT,
                err.errors(include_url=False, include_input=False),
            )


class QueryEndpoint(HTTPEndpoint):
    async def get(
        self, request: Request, query_service: QueryService = injectable
    ) -> JSONResponse:
        try:
            param_validator = ParamValidator.model_validate(request.path_params)
            query = query_service.get_by_id(param_validator.id)

            if query is None:
                return error_response(
                    NOT_FOUND, {"message": "query could not be found"}
                )

            return OK_response(OK, QuerySerializer.convert_model_to_dict(query))

        except ValidationError as err:
            return error_response(
                UNPROCESSABLE_CONTENT,
                err.errors(include_url=False, include_input=False),
            )

    async def patch(
        self, request: Request, query_service: QueryService = injectable
    ) -> JSONResponse:
        try:
            param_validator = ParamValidator.model_validate(request.path_params)
            query = query_service.get_by_id(param_validator.id)

            if query is None:
                return error_response(
                    NOT_FOUND, {"message": "query could not be found"}
                )

            body = await request.json()
            validator_data = UpdateQueryValidator.model_validate(body)
            updated_query = query_service.update(param_validator.id, validator_data)

            return OK_response(OK, QuerySerializer.convert_model_to_dict(updated_query))

        except ValidationError as err:
            return error_response(
                UNPROCESSABLE_CONTENT,
                err.errors(include_url=False, include_input=False),
            )

    async def delete(
        self, request: Request, query_service: QueryService = injectable
    ) -> JSONResponse:
        try:
            param_validator = ParamValidator.model_validate(request.path_params)
            query = query_service.get_by_id(param_validator.id)

            if query is None:
                return error_response(
                    NOT_FOUND, {"message": "query could not be found"}
                )

            query_service.delete(param_validator)

            return OK_response(OK, {"message": "query was deleted successfully"})

        except ValidationError as err:
            return error_response(
                UNPROCESSABLE_CONTENT,
                err.errors(include_url=False, include_input=False),
            )
