import polars as pl
from ..db.repositories import QueryRepository
from ..storage import read_processed
from ..validator import ExportParamValidator
from ..utils.export import FileExport
from ..utils.constants import EXCEL, JSON, CSV
from io import BytesIO
from json import dumps


def _to_json(value: object) -> str | None:
    if value is None:
        return None

    return dumps(value, default=str)


class QueryExportService:
    _query_repo: QueryRepository

    def __init__(self, query_repo: QueryRepository) -> None:
        self._query_repo = query_repo

    @staticmethod
    def _flatten_nested(frame: pl.DataFrame) -> pl.DataFrame:
        """Renders nested columns as JSON text.

        CSV and Excel cannot represent a List or Struct column and polars refuses to write one.
        truth_social's `mentions` is the case that hits this.
        """
        nested = [
            name
            for name, dtype in zip(frame.columns, frame.dtypes)
            if isinstance(dtype, (pl.List, pl.Struct))
        ]

        if not nested:
            return frame

        return frame.with_columns(
            [
                pl.col(name)
                .map_elements(_to_json, return_dtype=pl.String)
                .alias(name)
                for name in nested
            ]
        )

    def export(self, data: ExportParamValidator) -> FileExport | None:
        query = self._query_repo.find_by_id(data.id)

        if query is None:
            return None

        data_frame = read_processed(data.id)

        if data_frame is None:
            return None

        buffer = BytesIO()
        filename = (
            f"{query.platform}_{query.created_at.strftime('%Y%m%d')}_{query.percentage}"
        )

        if data.format.value == EXCEL:
            filename += ".xlsx"
            self._flatten_nested(data_frame).write_excel(buffer)

        if data.format.value == JSON:
            filename += ".json"
            # Nested values stay nested here; JSON can represent them.
            data_frame.write_json(buffer)

        if data.format.value == CSV:
            filename += ".csv"
            self._flatten_nested(data_frame).write_csv(buffer)

        return FileExport(filename=filename, data=buffer.getvalue())
