from abc import ABC, abstractmethod
from io import BytesIO
from json import dumps
from typing import ClassVar
import polars as pl
from ..utils.constants import (
    CSV_CONTENT_TYPE,
    EXCEL_CONTENT_TYPE,
    JSON_CONTENT_TYPE,
)
from ..validator import Format


class UnsupportedExportFormat(Exception):
    """No exporter is registered for the requested format."""


def _to_json(value: object) -> str | None:
    if value is None:
        return None

    return dumps(value, default=str)


class Exporter(ABC):
    """Renders a processed dataset in one file format.

    Each format previously had its extension, MIME type and writer spread across four files, with
    the format branched on in both the service and the endpoint. All three now live together and
    are looked up once.
    """

    extension: ClassVar[str]
    content_type: ClassVar[str]

    @abstractmethod
    def write(self, frame: pl.DataFrame) -> bytes:
        """Serializes the frame."""

    @staticmethod
    def flatten_nested(frame: pl.DataFrame) -> pl.DataFrame:
        """Renders List and Struct columns as JSON text.

        Tabular formats cannot represent a nested column and polars refuses to write one.
        truth_social's `mentions` is the column that hits this.
        """
        nested = [
            name
            for name, dtype in zip(frame.columns, frame.dtypes)
            if isinstance(dtype, (pl.List, pl.Struct))
        ]

        if not nested:
            return frame

        # Built from to_list() rather than map_elements: map_elements hands a polars Series to
        # the callback for a List column, so json.dumps would serialize the Series *repr*
        # ("shape: (1,)\nSeries: ...") into the file instead of the value.
        return frame.with_columns(
            [
                pl.Series(
                    name, [_to_json(value) for value in frame[name].to_list()], dtype=pl.String
                )
                for name in nested
            ]
        )


class CsvExporter(Exporter):
    extension = ".csv"
    content_type = CSV_CONTENT_TYPE

    def write(self, frame: pl.DataFrame) -> bytes:
        buffer = BytesIO()

        self.flatten_nested(frame).write_csv(buffer)

        return buffer.getvalue()


class ExcelExporter(Exporter):
    extension = ".xlsx"
    content_type = EXCEL_CONTENT_TYPE

    def write(self, frame: pl.DataFrame) -> bytes:
        buffer = BytesIO()

        self.flatten_nested(frame).write_excel(buffer)

        return buffer.getvalue()


class JsonExporter(Exporter):
    extension = ".json"
    content_type = JSON_CONTENT_TYPE

    def write(self, frame: pl.DataFrame) -> bytes:
        buffer = BytesIO()

        # Nested values stay nested: JSON can represent them, so flattening would lose structure.
        frame.write_json(buffer)

        return buffer.getvalue()


EXPORTERS: dict[Format, Exporter] = {
    Format.CSV: CsvExporter(),
    Format.EXCEL: ExcelExporter(),
    Format.JSON: JsonExporter(),
}


def exporter_for(format: Format) -> Exporter:
    exporter = EXPORTERS.get(format)

    # Previously an unrecognized format fell through every `if` and returned a FileExport wrapping
    # an empty buffer, so the user downloaded a 0-byte file with no error anywhere.
    if exporter is None:
        raise UnsupportedExportFormat(f"no exporter registered for {format}")

    return exporter
