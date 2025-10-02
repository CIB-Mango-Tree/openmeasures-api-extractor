from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import Response
from pydantic import ValidationError
from lagom import injectable
from ..services import QueryExportService
from ..validator import ExportParamValidator
from ..utils.responses import error_response
from ..utils.constants import (
    OK,
    EXCEL,
    JSON,
    CSV,
    EXCEL_CONTENT_TYPE,
    JSON_CONTENT_TYPE,
    CSV_CONTENT_TYPE,
    NOT_FOUND,
    UNPROCESSABLE_CONTENT,
)


class QueryExportEndpoint(HTTPEndpoint):
    async def get(
        self, request: Request, export_service: QueryExportService = injectable
    ) -> Response:
        try:
            params = ExportParamValidator.model_validate(request.path_params)
            file_export = export_service.export(params)

            if file_export is None:
                return error_response(
                    NOT_FOUND,
                    {"message": "The query you are looking for cannot be found"},
                )

            content_type = ""

            if params.format.value == EXCEL:
                content_type = EXCEL_CONTENT_TYPE

            if params.format.value == JSON:
                content_type = JSON_CONTENT_TYPE

            if params.format.value == CSV:
                content_type = CSV_CONTENT_TYPE

            return Response(
                content=file_export.data,
                status_code=OK,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'attachment; filename="{file_export.filename}"'
                },
            )

        except ValidationError as err:
            return error_response(
                UNPROCESSABLE_CONTENT,
                {"errors": err.errors(include_url=False, include_input=False)},
            )
