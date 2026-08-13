from ..db.repositories import QueryRepository
from ..validator import ExportParamValidator
from ..utils.export import FileExport
from ..db.models import Query
from ..utils.constants import EXCEL, JSON, CSV
from io import BytesIO


class QueryExportService:
    _query_repo: QueryRepository

    def __init__(self, query_repo: QueryRepository) -> None:
        self._query_repo = query_repo

    def export(self, data: ExportParamValidator) -> FileExport | None:
        query = self._query_repo.find_by_id(data.id)

        if query is None:
            return None

        # Fetched as a single scalar column rather than off the model: processed_data is
        # deferred and the query instance is detached by the time it gets here.
        processed_data = self._query_repo.find_processed_data(data.id)
        data_frame = Query.processed_data_to_dataframe(processed_data)

        if data_frame is None:
            return None

        buffer = BytesIO()
        filename = (
            f"{query.platform}_{query.created_at.strftime('%Y%m%d')}_{query.percentage}"
        )

        if data.format.value == EXCEL:
            filename += ".xlsx"
            data_frame.to_excel(buffer, engine="xlsxwriter")

        if data.format.value == JSON:
            filename += ".json"
            data_frame.to_json(buffer, orient="records")

        if data.format.value == CSV:
            filename += ".csv"
            data_frame.to_csv(buffer)

        return FileExport(filename=filename, data=buffer.getvalue())
