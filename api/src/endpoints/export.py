from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import Response
from pydantic import ValidationError
from ..services import QueryExportService
from ..validator import ExportParamValidator
from ..utils.responses import error_response
from ..utils.constants import OK, NOT_FOUND, UNPROCESSABLE_CONTENT


class QueryExportEndpoint(HTTPEndpoint):
    async def get(self, request: Request) -> Response:
        export_service: QueryExportService = request.app.state.export_service

        try:
            params = ExportParamValidator.model_validate(request.path_params)
            file_export = export_service.export(params)

            if file_export is None:
                return error_response(
                    NOT_FOUND,
                    {"message": "The query you are looking for cannot be found"},
                )

            # The content type comes from the exporter rather than being re-derived here; this
            # endpoint used to repeat the same three-way branch as the service.
            return Response(
                content=file_export.data,
                status_code=OK,
                media_type=file_export.content_type,
                headers={
                    "Content-Disposition": f'attachment; filename="{file_export.filename}"'
                },
            )

        except ValidationError as err:
            return error_response(
                UNPROCESSABLE_CONTENT,
                {"errors": err.errors(include_url=False, include_input=False)},
            )
