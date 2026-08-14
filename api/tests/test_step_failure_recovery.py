"""What a query looks like after a step raises.

A failing step used to be logged and swallowed, leaving the query on the IN_PROGRESS status that
_resume had just written. No step handles that status and no event ever clears it, so the query
was stuck: the progress bar span forever and the details dialog offered no way to retry, because
resuming is only offered for an INCOMPLETE status. These pin the recovery down.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

import pytest
from pyventus.events import AsyncIOEventEmitter, EventLinker

from src.db.connection import init_DB
from src.db.models import Query, QueryTerm
from src.db.repositories import QueryRepository, QueryTermRepository
from src.services.steps import ParseStep
from src.utils.constants import PARSE_CONTINUE, PARSE_IN_PROGRESS, PARSE_INCOMPLETE


@pytest.fixture(autouse=True)
def isolated_linker() -> Iterator[None]:
    EventLinker.remove_all()
    yield
    EventLinker.remove_all()


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    monkeypatch.setattr("src.storage.dataset.get_app_data_dir", lambda *_: str(tmp_path))
    yield tmp_path


def _build(tmp_path: Path) -> dict[str, Any]:
    factory = init_DB(f"sqlite:///{tmp_path / 'test.db'}")
    query_repo = QueryRepository(factory)
    term_repo = QueryTermRepository(factory)
    start = datetime(2026, 1, 1)
    query = query_repo.create(
        Query(
            status=PARSE_CONTINUE,
            timezone="UTC",
            start_date=start,
            end_date=start + timedelta(days=1),
            platform="bluesky",
        )
    )

    term_repo.batch_create(
        [QueryTerm(query_id=query.id, term="mango", modifier="EQUAL", position=1)]
    )

    return {
        "repo": query_repo,
        "query": query,
        # No raw pages were ever written, so ParseStep raises "no raw dataset found".
        "step": ParseStep(query_repo, AsyncIOEventEmitter()),
    }


def test_a_failed_step_leaves_the_query_resumable(workspace: Path, tmp_path: Path) -> None:
    built = _build(tmp_path)

    assert built["step"].run(built["query"]) is None, "a raising step must not return a result"

    stored = built["repo"].find_by_id(built["query"].id)

    assert stored is not None
    assert stored.status == PARSE_INCOMPLETE, (
        f"expected the query to be resumable, got {stored.status}"
    )
    assert stored.status != PARSE_IN_PROGRESS, "the query would be stuck with no way to retry"


def test_the_failure_is_announced_to_connected_clients(
    workspace: Path, tmp_path: Path
) -> None:
    """Without an event the UI keeps waiting on a query the backend has already given up on."""
    built = _build(tmp_path)
    received: list[tuple[str, Any]] = []

    @EventLinker.on(PARSE_INCOMPLETE)
    def handler(payload: Any) -> None:
        received.append((PARSE_INCOMPLETE, payload))

    built["step"].run(built["query"])

    assert len(received) == 1, f"expected one PARSE:INCOMPLETE event, got {received}"


def test_a_query_already_marked_incomplete_is_not_reprocessed(
    workspace: Path, tmp_path: Path
) -> None:
    """Guards the retry loop: run() returns early rather than raising a second time."""
    built = _build(tmp_path)
    query: Query = built["query"]

    query.status = PARSE_INCOMPLETE

    assert built["step"].run(query) is None
