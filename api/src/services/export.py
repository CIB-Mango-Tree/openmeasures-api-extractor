from math import floor
from ..db.repositories import QueryRepository
from ..storage import read_processed
from ..utils.export import FileExport
from ..validator import ExportParamValidator
from .exporters import exporter_for


class QueryExportService:
    _query_repo: QueryRepository

    def __init__(self, query_repo: QueryRepository) -> None:
        self._query_repo = query_repo

    def export(self, data: ExportParamValidator) -> FileExport | None:
        query = self._query_repo.find_by_id(data.id)

        if query is None:
            return None

        frame = read_processed(data.id)

        if frame is None:
            return None

        exporter = exporter_for(data.format)
        # The percentage is a raw ratio, so interpolating the float straight in produced names
        # like "..._0.4235294117647059.csv". Truncated rather than rounded: rounding turns a 99.9%
        # extraction into "1.00", which reads as complete and defeats the point of the suffix.
        completion = floor(query.percentage * 100) / 100
        filename = (
            f"{query.platform}_{query.created_at.strftime('%Y%m%d')}"
            f"_{completion:.2f}{exporter.extension}"
        )

        return FileExport(
            filename=filename,
            data=exporter.write(frame),
            content_type=exporter.content_type,
        )
