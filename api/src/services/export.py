from ..db.repositories import QueryRepository
from ..validator import ExportParamValidator
from ..utils.export import FileExport
from ..utils.constants import EXCEL, JSON, CSV
from io import BytesIO
from sys import getsizeof


class QueryExportService:
    _query_repo: QueryRepository

    def __init__(self, query_repo: QueryRepository) -> None:
        self._query_repo = query_repo

    def export(self, data: ExportParamValidator) -> FileExport | None:
        query = self._query_repo.find_by_id(data.id)

        if query is None:
            return None

        if getsizeof(query.processed_data) == 0:
            return None

        data_frame = query.from_processed_data_to_dataframe()

        if data_frame is None:
            return None

        buffer = BytesIO()
        filename = (
            f"{query.platform}_{query.created_at.strftime('%Y%m%d')}_{query.percentage}"
        )

        if data.format.value == EXCEL:
            filename += ".xlsx"
            data_frame.to_excel(buffer)

        if data.format.value == JSON:
            filename += ".json"
            data_frame.to_json(buffer, orient="records")

        if data.format.value == CSV:
            filename += ".csv"
            data_frame.to_csv(buffer)

        return FileExport(filename=filename, data=buffer.getvalue())
