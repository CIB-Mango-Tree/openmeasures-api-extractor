"""Tests for the per-format export strategies.

The Format enum values (`excel`/`json`/`csv`) are in the download URL and are hardcoded in
site/src/components/export.tsx -- they are API contract, not internal names.
"""

import csv
import json
from io import BytesIO, StringIO
from zipfile import ZipFile

import polars as pl
import pytest

from src.services.exporters import (
    EXPORTERS,
    CsvExporter,
    ExcelExporter,
    JsonExporter,
    UnsupportedExportFormat,
    exporter_for,
)
from src.utils.constants import CSV_CONTENT_TYPE, EXCEL_CONTENT_TYPE, JSON_CONTENT_TYPE
from src.validator import Format

FLAT = pl.DataFrame({"_id": ["a", "b"], "text": ["first", "second"], "count": [1, 2]})

# truth_social's `mentions` column: polars refuses to write a List column to a tabular format.
NESTED = pl.DataFrame(
    {
        "_id": ["a", "b"],
        "mentions": [[{"id": "m1", "username": "someone"}], []],
    }
)


def test_every_format_has_an_exporter() -> None:
    assert set(EXPORTERS) == set(Format)


@pytest.mark.parametrize(
    "format,extension,content_type",
    [
        (Format.CSV, ".csv", CSV_CONTENT_TYPE),
        (Format.JSON, ".json", JSON_CONTENT_TYPE),
        (Format.EXCEL, ".xlsx", EXCEL_CONTENT_TYPE),
    ],
)
def test_exporter_declares_extension_and_content_type(
    format: Format, extension: str, content_type: str
) -> None:
    exporter = exporter_for(format)

    assert exporter.extension == extension
    assert exporter.content_type == content_type


def test_unknown_format_raises_instead_of_returning_an_empty_file() -> None:
    """Previously an unrecognized format fell through every branch and produced a 0-byte file."""
    with pytest.raises(UnsupportedExportFormat):
        exporter_for("not-a-format")  # type: ignore[arg-type]


def test_csv_round_trips() -> None:
    payload = CsvExporter().write(FLAT).decode()
    rows = list(csv.DictReader(StringIO(payload)))

    assert [row["_id"] for row in rows] == ["a", "b"]
    assert rows[0]["text"] == "first"


def test_json_round_trips() -> None:
    records = json.loads(JsonExporter().write(FLAT).decode())

    assert [record["_id"] for record in records] == ["a", "b"]
    assert records[1]["count"] == 2


def test_excel_produces_a_readable_workbook() -> None:
    payload = ExcelExporter().write(FLAT)

    # Inspected as the zip container xlsx actually is, rather than parsed: reading it back would
    # add a dependency (fastexcel) that only the tests would use. Byte comparison is out either
    # way, since xlsx embeds a creation timestamp.
    with ZipFile(BytesIO(payload)) as workbook:
        names = workbook.namelist()

    assert "xl/workbook.xml" in names
    assert any(name.startswith("xl/worksheets/") for name in names)


def test_csv_renders_nested_columns_as_json_text() -> None:
    payload = CsvExporter().write(NESTED).decode()
    rows = list(csv.DictReader(StringIO(payload)))

    assert json.loads(rows[0]["mentions"]) == [{"id": "m1", "username": "someone"}]
    assert json.loads(rows[1]["mentions"]) == []


def test_excel_accepts_nested_columns() -> None:
    """Without flattening, polars raises rather than writing the sheet."""
    assert len(ExcelExporter().write(NESTED)) > 0


def test_json_keeps_nested_columns_nested() -> None:
    records = json.loads(JsonExporter().write(NESTED).decode())

    # Not a JSON string: the format can represent the structure, so flattening would lose it.
    assert records[0]["mentions"] == [{"id": "m1", "username": "someone"}]
