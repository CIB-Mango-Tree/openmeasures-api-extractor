from starlette.websockets import WebSocket
from pyventus.events import EventLinker
from asyncio import create_task
from ..db.repositories import QueryRepository
from ..websocket import WebSocketConnection, ConnectionStore
from ..event import Event
from ..utils.constants import (
    FETCH_INCOMPLETE,
    FETCH_IN_PROGRESS,
    FETCH_UPDATE_PROGRESS,
    CLEAN_IN_PROGRESS,
    PARSE_IN_PROGRESS,
    QUERY_COMPLETE,
    LIMIT_MAXED_OUT,
)
from typing import List, Any


class WebSocketService:
    _query_repo: QueryRepository
    _store: ConnectionStore

    def __init__(self, query_repo: QueryRepository) -> None:
        self._store = ConnectionStore()
        self._query_repo = query_repo

        @EventLinker.on(FETCH_UPDATE_PROGRESS, force_async=True)
        def handle_progress_update(payload: Event) -> None:
            self.send_by_topic(
                payload.data.id, {
                    "event": FETCH_UPDATE_PROGRESS, "data": payload.data}
            )

        @EventLinker.on(FETCH_INCOMPLETE, force_async=True)
        def handle_incomplete_fetch(payload: Event):
            self.send_by_topic(
                payload.data.id,
                {
                    "event": FETCH_INCOMPLETE,
                    "data": {"message": payload.message, "query": payload.data},
                },
            )

        @EventLinker.on(CLEAN_IN_PROGRESS, force_async=True)
        def handle_in_progress_clean(payload: Event):
            self.send_by_topic(
                payload.data.id,
                {
                    "event": CLEAN_IN_PROGRESS,
                    "data": {"message": payload.message, "query": payload.data},
                },
            )

        @EventLinker.on(PARSE_IN_PROGRESS, force_async=True)
        def handle_in_progress_parse(payload: Event):
            self.send_by_topic(
                payload.data.id,
                {
                    "event": PARSE_IN_PROGRESS,
                    "data": {"message": payload.message, "query": payload.data},
                },
            )

        @EventLinker.on(LIMIT_MAXED_OUT, force_async=True)
        def handle_maxed_limit(payload: Event) -> None:
            self.send_by_topic(
                payload.data.id,
                {
                    "event": LIMIT_MAXED_OUT,
                    "data": {"message": payload.message, "query": payload.data},
                },
            )

    def get(self) -> List[WebSocketConnection]:
        return self._store.get()

    def get_by_id(self, id: str) -> WebSocketConnection:
        return self._store.get_by_id(id)

    def create(self, socket: WebSocket) -> WebSocketConnection:
        connection = WebSocketConnection(socket)

        self._store.set(connection)

        return connection

    def delete(self, id: str) -> None:
        self._store.remove(id)

    def subscribe(self, id: str, topic: str) -> WebSocketConnection:
        if not self._query_repo.exists(topic):
            return None

        connection = self._store.get_by_id(id)

        if not connection:
            return None

        connection.topics.add(topic)
        self._store.set(connection)

        return connection

    def unsubscribe(self, id: str, topic: str) -> WebSocketConnection:
        connection = self._store.get_by_id(id)

        if not connection:
            return None

        connection.topics.remove(topic)
        self._store.set(connection)

        return connection

    def broadcast(self, data: Any) -> None:
        connections = self._store.get()

        async def func():
            for connection in connections:
                connection.socket.send_json(data)

        create_task(func())

    def send(self, id: str, data: Any) -> None:
        connection = self._store.get_by_id(id)

        if connection is None:
            return

        async def func() -> None:
            connection.socket.send_json(data)

        create_task(func())

    def send_by_topic(self, topic: str, data: Any) -> None:
        connections = self._store.get()

        async def func() -> None:
            for connection in connections:
                if connection.topics.has(topic):
                    connection.socket.send_json(data)

        create_task(func())
