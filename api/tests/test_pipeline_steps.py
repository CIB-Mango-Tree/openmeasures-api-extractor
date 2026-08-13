"""Integration tests for the extraction pipeline.

The emitted event names are the WebSocket wire protocol: site/src/home.tsx switches on them, and
they double as the persisted Query.status. These drive the real orchestrator so the sequence is
pinned end to end -- steps report an outcome and QueryService decides the transition, so testing
a step in isolation would no longer prove what the frontend actually receives.
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

import polars as pl
import pytest
from sqlalchemy.orm import selectinload

from src.db.connection import init_DB
from src.db.models import Query, QueryLimit, QueryTerm
from src.db.repositories import (
    QueryLimitRepository,
    QueryRepository,
    QueryRequestRepository,
    QueryTermRepository,
)
from src.services.openmeasures import RateLimited
from src.services.query import QueryService
from src.services.steps import FetchStep, Outcome, ParseStep, QuotaTracker
from src.utils.constants import (
    CLEAN_CONTINUE,
    CLEAN_IN_PROGRESS,
    FETCH_IN_PROGRESS,
    FETCH_INCOMPLETE,
    LIMIT_MAXED_OUT,
    LIMIT_UPDATE,
    PARSE_CONTINUE,
    PARSE_IN_PROGRESS,
    QUERY_COMPLETE,
)


class RecordingEmitter:
    """Captures emissions in order. Payloads are pyventus Event objects."""

    def __init__(self) -> None:
        self.events: list[str] = []

    def emit(self, event: str, payload: Any = None) -> None:
        self.events.append(event)


class StubClient:
    """Replays scripted pages, or raises when the script holds an exception."""

    def __init__(self, pages: list[Any]) -> None:
        self.pages = pages
        self.calls = 0

    def fetch(self, params: dict[str, Any]) -> dict[str, Any]:
        page = self.pages[min(self.calls, len(self.pages) - 1)]
        self.calls += 1

        if isinstance(page, Exception):
            raise page

        return page


def _hits(count: int, start: datetime, offset: int = 0) -> dict[str, Any]:
    return {
        "hits": {
            "hits": [
                {
                    "_index": "bluesky",
                    "_id": f"post-{offset + index}",
                    "_source": {
                        "author": f"author-{offset + index}",
                        "createdAt": (start + timedelta(minutes=offset + index)).isoformat(),
                        "text": f"post &amp; body {offset + index}",
                    },
                }
                for index in range(count)
            ]
        }
    }


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    monkeypatch.setattr("src.storage.dataset.get_app_data_dir", lambda *_: str(tmp_path))
    yield tmp_path


@pytest.fixture
def repos(tmp_path: Path) -> Iterator[dict[str, Any]]:
    factory = init_DB(f"sqlite:///{tmp_path / 'test.db'}")

    yield {
        "query": QueryRepository(factory),
        "term": QueryTermRepository(factory),
        "request": QueryRequestRepository(factory),
        "limit": QueryLimitRepository(factory),
    }


def _seed_query(repos: dict[str, Any], status: str = FETCH_IN_PROGRESS) -> Query:
    start = datetime(2026, 1, 1, 0, 0, 0)
    query = repos["query"].create(
        Query(
            status=status,
            timezone="UTC",
            start_date=start,
            end_date=start + timedelta(days=1),
            platform="bluesky",
        )
    )

    repos["term"].batch_create(
        [QueryTerm(query_id=query.id, term="mango", modifier="EQ", position=1)]
    )
    repos["limit"].create(QueryLimit(id=1, count=39, percentage=1.0))

    return repos["query"].find_by_id(
        query.id, [selectinload(Query.terms), selectinload(Query.requests)]
    )


def _service(
    repos: dict[str, Any], emitter: RecordingEmitter, client: Any
) -> QueryService:
    steps = [
        FetchStep(
            repos["query"],
            emitter,  # type: ignore[arg-type]
            repos["request"],
            QuotaTracker(repos["limit"], emitter),  # type: ignore[arg-type]
            client,
        ),
        ParseStep(repos["query"], emitter),  # type: ignore[arg-type]
    ]

    return QueryService(repos["query"], repos["term"], emitter, steps)  # type: ignore[arg-type]


def _run(service: QueryService, query_id: Any) -> None:
    async def go() -> None:
        await service.process_query(query_id)

    asyncio.run(go())


def test_full_pipeline_emits_fetch_then_parse_then_complete(
    workspace: Path, repos: dict[str, Any]
) -> None:
    emitter = RecordingEmitter()
    query = _seed_query(repos)
    service = _service(repos, emitter, StubClient([_hits(5, query.start_date)]))

    _run(service, query.id)

    # LIMIT:UPDATE from spending a request, then the two transitions the orchestrator derives
    # from the pipeline order: fetch advances to parse, parse advances to complete.
    assert emitter.events == [LIMIT_UPDATE, PARSE_IN_PROGRESS, QUERY_COMPLETE]

    final = repos["query"].find_by_id(query.id)
    assert final.status == QUERY_COMPLETE
    assert final.rows_fetched == 5


def test_pipeline_writes_raw_pages_and_a_processed_dataset(
    workspace: Path, repos: dict[str, Any]
) -> None:
    emitter = RecordingEmitter()
    query = _seed_query(repos)
    service = _service(repos, emitter, StubClient([_hits(3, query.start_date)]))

    _run(service, query.id)

    dataset = workspace / "datasets" / str(query.id)
    pages = list((dataset / "raw").glob("*.parquet"))

    assert len(pages) == 1
    assert pl.read_parquet(pages[0]).height == 3

    processed = pl.read_parquet(dataset / "processed.parquet")

    assert processed.height == 3
    # Sanitization is a read-time transform inside parse, not a stored artifact.
    assert processed["text"][0] == "post & body 0"


def test_empty_first_page_completes_without_running_parse(
    workspace: Path, repos: dict[str, Any]
) -> None:
    emitter = RecordingEmitter()
    query = _seed_query(repos)
    service = _service(repos, emitter, StubClient([{"hits": {"hits": []}}]))

    _run(service, query.id)

    # COMPLETE short-circuits the remaining steps: there is no dataset to parse.
    assert emitter.events == [QUERY_COMPLETE]
    assert not (workspace / "datasets" / str(query.id) / "processed.parquet").exists()


def test_rate_limited_pauses_the_query_and_zeroes_the_quota(
    workspace: Path, repos: dict[str, Any]
) -> None:
    emitter = RecordingEmitter()
    query = _seed_query(repos)
    service = _service(repos, emitter, StubClient([RateLimited("429")]))

    _run(service, query.id)

    assert emitter.events == [LIMIT_MAXED_OUT, FETCH_INCOMPLETE]
    assert repos["query"].find_by_id(query.id).status == FETCH_INCOMPLETE
    assert repos["limit"].find().count == 0


def test_exhausted_quota_pauses_before_making_a_request(
    workspace: Path, repos: dict[str, Any]
) -> None:
    emitter = RecordingEmitter()
    query = _seed_query(repos)

    limit = repos["limit"].find()
    limit.count = 0
    repos["limit"].update(limit)

    client = StubClient([_hits(5, query.start_date)])
    service = _service(repos, emitter, client)

    _run(service, query.id)

    assert emitter.events == [LIMIT_MAXED_OUT, FETCH_INCOMPLETE]
    # The quota is checked before the call, so no request is wasted.
    assert client.calls == 0


def test_pause_stops_the_pipeline_before_parse(
    workspace: Path, repos: dict[str, Any]
) -> None:
    emitter = RecordingEmitter()
    query = _seed_query(repos)
    service = _service(repos, emitter, StubClient([RateLimited("429")]))

    _run(service, query.id)

    assert PARSE_IN_PROGRESS not in emitter.events
    assert QUERY_COMPLETE not in emitter.events


def test_parse_resumes_from_a_legacy_clean_status(
    workspace: Path, repos: dict[str, Any]
) -> None:
    """Clean is no longer a stage, but a query persisted mid-flight can still be sitting in one."""
    emitter = RecordingEmitter()
    query = _seed_query(repos)

    _service(repos, emitter, StubClient([_hits(2, query.start_date)]))
    _run(_service(repos, emitter, StubClient([_hits(2, query.start_date)])), query.id)

    stale = repos["query"].find_by_id(query.id)
    stale.status = CLEAN_IN_PROGRESS
    repos["query"].update(stale, True)
    emitter.events.clear()

    _run(_service(repos, emitter, StubClient([])), query.id)

    assert emitter.events == [QUERY_COMPLETE]
    assert repos["query"].find_by_id(query.id).status == QUERY_COMPLETE


def test_orchestrator_derives_transitions_from_pipeline_order(
    repos: dict[str, Any]
) -> None:
    """The next status comes from the pipeline, not from anything a step names."""
    emitter = RecordingEmitter()
    service = _service(repos, emitter, StubClient([]))
    fetch, parse = service._steps

    assert service._next_status(fetch, Outcome.ADVANCE, [parse]) == PARSE_IN_PROGRESS
    # Nothing after it: advancing means the query is done.
    assert service._next_status(parse, Outcome.ADVANCE, []) == QUERY_COMPLETE
    assert service._next_status(fetch, Outcome.PAUSE, [parse]) == FETCH_INCOMPLETE
    assert service._next_status(fetch, Outcome.COMPLETE, [parse]) == QUERY_COMPLETE


def test_parse_step_accepts_clean_statuses_for_resume(repos: dict[str, Any]) -> None:
    parse = ParseStep(repos["query"], RecordingEmitter())  # type: ignore[arg-type]

    assert parse.handles(PARSE_IN_PROGRESS)
    assert parse.handles(PARSE_CONTINUE)
    assert parse.handles(CLEAN_IN_PROGRESS)
    assert parse.handles(CLEAN_CONTINUE)
