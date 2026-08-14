"""The completion suffix on an exported filename.

percentage is a raw ratio, so interpolating it directly produced names like
"bluesky_20260813_0.4235294117647059.csv" -- which is what a partial export actually looked like,
since only a partial extraction has a percentage that is not exactly 1.
"""

from datetime import datetime
from pathlib import Path
from typing import Iterator

import polars as pl
import pytest

from src.db.connection import init_DB
from src.db.models import Query
from src.db.repositories import QueryRepository
from src.services.export import QueryExportService
from src.storage import write_processed
from src.validator import ExportParamValidator


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    monkeypatch.setattr("src.storage.dataset.get_app_data_dir", lambda *_: str(tmp_path))
    yield tmp_path


def _export_named(tmp_path: Path, percentage: float) -> str:
    factory = init_DB(f"sqlite:///{tmp_path / 'test.db'}")
    repo = QueryRepository(factory)
    query = repo.create(
        Query(
            status="COMPLETE",
            timezone="UTC",
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 1, 2),
            platform="bluesky",
            percentage=percentage,
        )
    )

    write_processed(query.id, pl.DataFrame({"_id": ["a"], "text": ["hello"]}))

    export = QueryExportService(repo).export(
        ExportParamValidator(id=query.id, format="csv")
    )

    assert export is not None

    return export.filename


def test_a_partial_export_is_named_with_two_decimal_places(
    workspace: Path, tmp_path: Path
) -> None:
    assert _export_named(tmp_path, 0.4235294117647059).endswith("_0.42.csv")


def test_a_complete_export_still_reads_as_complete(
    workspace: Path, tmp_path: Path
) -> None:
    assert _export_named(tmp_path, 1.0).endswith("_1.00.csv")


def test_an_almost_complete_export_is_not_rounded_up_to_look_complete(
    workspace: Path, tmp_path: Path
) -> None:
    """Rounding would name a 99.9% extraction "1.00", which is the one thing the suffix exists
    to distinguish."""
    assert _export_named(tmp_path, 0.999).endswith("_0.99.csv")


def test_a_small_fraction_keeps_two_decimal_places(
    workspace: Path, tmp_path: Path
) -> None:
    assert _export_named(tmp_path, 0.06666666666666667).endswith("_0.06.csv")
