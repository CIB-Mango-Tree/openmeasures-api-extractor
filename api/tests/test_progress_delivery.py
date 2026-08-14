"""End-to-end delivery of progress events to a connected websocket.

The other pipeline tests use a recording emitter, so they prove the steps *emit* but never
exercise pyventus -> EventLinker -> WebSocketService -> socket. This covers that gap: it is the
path that actually drives the progress bar and the limit counter in the UI.
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

import pytest
from pyventus.events import AsyncIOEventEmitter, EventLinker
from sqlalchemy.orm import selectinload

from src.db.connection import init_DB
from src.db.models import Query, QueryLimit, QueryTerm
from src.db.repositories import (
    QueryLimitRepository,
    QueryRepository,
    QueryRequestRepository,
    QueryTermRepository,
)
from src.services.query import QueryService
from src.services.steps import FetchStep, ParseStep, QuotaTracker
from src.services.websocket import WebSocketService
from src.utils.constants import LIMIT_UPDATE, PARSE_IN_PROGRESS, QUERY_COMPLETE


class FakeSocket:
    """Captures what would go over the wire."""

    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []
        self.state = type("State", (), {})()

    async def send_json(self, data: dict[str, Any]) -> None:
        self.sent.append(data)


class StubClient:
    def __init__(self, pages: list[Any]) -> None:
        self.pages = pages
        self.calls = 0

    def fetch(self, params: dict[str, Any]) -> dict[str, Any]:
        page = self.pages[min(self.calls, len(self.pages) - 1)]
        self.calls += 1

        return page


def _hits(count: int, start: datetime) -> dict[str, Any]:
    return {
        "hits": {
            "hits": [
                {
                    "_index": "bluesky",
                    "_id": f"post-{index}",
                    "_source": {
                        "author": f"author-{index}",
                        "createdAt": (start + timedelta(minutes=index)).isoformat(),
                        "text": f"body {index}",
                    },
                }
                for index in range(count)
            ]
        }
    }


@pytest.fixture(autouse=True)
def isolated_linker() -> Iterator[None]:
    """EventLinker is a process-global registry; keep handlers from leaking between tests."""
    EventLinker.remove_all()
    yield
    EventLinker.remove_all()


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    monkeypatch.setattr("src.storage.dataset.get_app_data_dir", lambda *_: str(tmp_path))
    yield tmp_path


def _build(tmp_path: Path) -> dict[str, Any]:
    factory = init_DB(f"sqlite:///{tmp_path / 'test.db'}")
    repos = {
        "query": QueryRepository(factory),
        "term": QueryTermRepository(factory),
        "request": QueryRequestRepository(factory),
        "limit": QueryLimitRepository(factory),
    }
    start = datetime(2026, 1, 1)
    query = repos["query"].create(
        Query(
            status="FETCH:IN_PROGRESS",
            timezone="UTC",
            start_date=start,
            end_date=start + timedelta(days=1),
            platform="bluesky",
        )
    )

    repos["term"].batch_create(
        [QueryTerm(query_id=query.id, term="mango", modifier="EQUAL", position=1)]
    )
    repos["limit"].create(QueryLimit(id=1, count=39, percentage=1.0))

    emitter = AsyncIOEventEmitter()
    # Constructing the service is what registers the EventLinker handlers.
    websocket_service = WebSocketService(repos["query"])
    steps = [
        FetchStep(
            repos["query"],
            emitter,
            repos["request"],
            QuotaTracker(repos["limit"], emitter),
            StubClient([_hits(3, start)]),
        ),
        ParseStep(repos["query"], emitter),
    ]

    return {
        "repos": repos,
        "query": repos["query"].find_by_id(
            query.id, [selectinload(Query.terms), selectinload(Query.requests)]
        ),
        "service": QueryService(repos["query"], repos["term"], emitter, steps),
        "websocket": websocket_service,
    }


def test_a_subscribed_client_receives_progress_and_limit_events(
    workspace: Path, tmp_path: Path
) -> None:
    built = _build(tmp_path)
    websocket_service: WebSocketService = built["websocket"]
    query: Query = built["query"]
    socket = FakeSocket()

    async def run() -> None:
        # The endpoint captures the loop on first connect; without it every send is dropped.
        websocket_service.set_event_loop(asyncio.get_running_loop())

        connection = websocket_service.create(socket)  # type: ignore[arg-type]
        websocket_service.subscribe(connection.id, query.id)

        await built["service"].process_query(query.id)
        # Sends are fire-and-forget, so let the loop drain them.
        await asyncio.sleep(0.3)

    asyncio.run(run())

    events = [message["event"] for message in socket.sent]

    assert LIMIT_UPDATE in events, f"limit counter never updated; got {events}"
    assert PARSE_IN_PROGRESS in events, f"no progress transition; got {events}"
    assert QUERY_COMPLETE in events, f"no completion; got {events}"


def test_limit_updates_reach_clients_that_subscribed_to_nothing(
    workspace: Path, tmp_path: Path
) -> None:
    """LIMIT:* is broadcast, so the counter must update even without a topic subscription."""
    built = _build(tmp_path)
    websocket_service: WebSocketService = built["websocket"]
    socket = FakeSocket()

    async def run() -> None:
        websocket_service.set_event_loop(asyncio.get_running_loop())
        websocket_service.create(socket)  # type: ignore[arg-type]

        await built["service"].process_query(built["query"].id)
        await asyncio.sleep(0.3)

    asyncio.run(run())

    assert LIMIT_UPDATE in [message["event"] for message in socket.sent]


def test_nothing_is_sent_when_the_loop_was_never_captured(
    workspace: Path, tmp_path: Path
) -> None:
    """Documents the failure mode: no connection means no loop, so sends are dropped."""
    built = _build(tmp_path)
    socket = FakeSocket()

    built["websocket"].create(socket)  # type: ignore[arg-type]

    async def run() -> None:
        await built["service"].process_query(built["query"].id)
        await asyncio.sleep(0.2)

    asyncio.run(run())

    assert socket.sent == []


def _ws_app(built: dict[str, Any]) -> Any:
    """Minimal app exposing just the websocket route, so the endpoint can be driven directly."""
    from starlette.applications import Starlette
    from starlette.routing import WebSocketRoute

    from src.endpoints import UpdateStreamEndpoint

    app = Starlette(routes=[WebSocketRoute("/api/ws/updates", endpoint=UpdateStreamEndpoint)])
    app.state.websocket_service = built["websocket"]

    return app


def test_subscribe_frame_does_not_kill_the_connection(
    workspace: Path, tmp_path: Path
) -> None:
    """The regression that broke every extraction's progress reporting.

    encoding = "json" means Starlette hands on_receive a decoded dict, but it was passed to
    json.loads again. The TypeError escaped the handler and closed the socket; the client
    reconnected, replayed the subscription and died again about once a second.
    """
    from starlette.testclient import TestClient

    built = _build(tmp_path)
    topic = str(built["query"].id)

    with TestClient(_ws_app(built)) as client:
        with client.websocket_connect("/api/ws/updates") as socket:
            assert socket.receive_json() == {"message": "Connected!!!"}

            socket.send_json({"action": "SUBSCRIBE", "topic": topic})

            assert socket.receive_json()["event"] == "SUBSCRIBE:SUCCESS"

            # Still alive and still serving requests.
            socket.send_json({"action": "UNSUBSCRIBE", "topic": topic})

            assert socket.receive_json()["event"] == "UNSUBSCRIBE:SUCCESS"


def test_undecodable_frame_is_dropped_rather_than_closing_the_socket(
    workspace: Path, tmp_path: Path
) -> None:
    """Starlette closes with 1003 on bad JSON; with a reconnecting client that loops forever."""
    from starlette.testclient import TestClient

    built = _build(tmp_path)
    topic = str(built["query"].id)

    with TestClient(_ws_app(built)) as client:
        with client.websocket_connect("/api/ws/updates") as socket:
            socket.receive_json()

            socket.send_text("not json at all")
            socket.send_json({"action": "SUBSCRIBE", "topic": topic})

            assert socket.receive_json()["event"] == "SUBSCRIBE:SUCCESS"
