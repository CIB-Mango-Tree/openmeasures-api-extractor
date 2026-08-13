"""Tests for the desktop save bridge.

The webview has no download manager: a link to the download endpoint renders the file in the
window instead of saving it. These cover everything the bridge does except the native dialog
itself, which is stubbed.
"""

from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

import polars as pl
import pytest

from src.db.connection import init_DB
from src.db.models import Query
from src.db.repositories import QueryRepository
from src.desktop_api import DesktopApi
from src.services.export import QueryExportService
from src.storage import write_processed


class StubWindow:
    """Stands in for the pywebview window; records what the dialog was asked for."""

    def __init__(self, choice: Any) -> None:
        self.choice = choice
        self.requested_filename: str | None = None

    def create_file_dialog(self, _: Any, save_filename: str = "") -> Any:
        self.requested_filename = save_filename
        return self.choice


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    monkeypatch.setattr("src.storage.dataset.get_app_data_dir", lambda *_: str(tmp_path))
    yield tmp_path


@pytest.fixture
def exportable(tmp_path: Path, workspace: Path) -> Iterator[tuple[QueryExportService, Query]]:
    from datetime import datetime

    factory = init_DB(f"sqlite:///{tmp_path / 'test.db'}")
    repo = QueryRepository(factory)
    query = repo.create(
        Query(
            status="COMPLETE",
            timezone="UTC",
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 1, 2),
            platform="bluesky",
        )
    )

    write_processed(query.id, pl.DataFrame({"_id": ["a"], "text": ["hello"]}))

    yield QueryExportService(repo), query


def test_saves_the_export_to_the_chosen_path(
    tmp_path: Path, exportable: tuple[QueryExportService, Query]
) -> None:
    service, query = exportable
    destination = tmp_path / "chosen.csv"
    api = DesktopApi(service)

    window = StubWindow(str(destination))
    api.bind(window)  # type: ignore[arg-type]

    result = api.save_export(str(query.id), "csv")

    assert result["status"] == "saved"
    assert destination.exists()
    assert "hello" in destination.read_text()
    # The dialog is pre-filled with the generated filename, extension included.
    assert window.requested_filename is not None
    assert window.requested_filename.endswith(".csv")


def test_accepts_a_list_from_the_dialog(
    tmp_path: Path, exportable: tuple[QueryExportService, Query]
) -> None:
    """Some pywebview backends return a tuple of paths rather than a single string."""
    service, query = exportable
    destination = tmp_path / "from-list.json"
    api = DesktopApi(service)

    api.bind(StubWindow([str(destination)]))  # type: ignore[arg-type]

    assert api.save_export(str(query.id), "json")["status"] == "saved"
    assert destination.exists()


def test_cancelling_the_dialog_writes_nothing(
    exportable: tuple[QueryExportService, Query]
) -> None:
    service, query = exportable
    api = DesktopApi(service)

    api.bind(StubWindow(None))  # type: ignore[arg-type]

    assert api.save_export(str(query.id), "csv")["status"] == "cancelled"


def test_unknown_query_reports_an_error(
    tmp_path: Path, exportable: tuple[QueryExportService, Query]
) -> None:
    service, _ = exportable
    api = DesktopApi(service)

    api.bind(StubWindow(str(tmp_path / "nope.csv")))  # type: ignore[arg-type]

    result = api.save_export(str(uuid4()), "csv")

    assert result["status"] == "error"
    assert "message" in result


def test_invalid_format_reports_an_error_rather_than_raising(
    tmp_path: Path, exportable: tuple[QueryExportService, Query]
) -> None:
    service, query = exportable
    api = DesktopApi(service)

    api.bind(StubWindow(str(tmp_path / "nope.parquet")))  # type: ignore[arg-type]

    assert api.save_export(str(query.id), "parquet")["status"] == "error"
