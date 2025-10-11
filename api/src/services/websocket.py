from starlette.websockets import WebSocket
from pyventus.events import EventLinker
from asyncio import (
    create_task,
    gather,
    get_event_loop,
    run_coroutine_threadsafe,
    AbstractEventLoop,
)
from uuid import UUID
from ..db.repositories import QueryRepository
from ..websocket import WebSocketConnection, ConnectionStore
from ..event import Event
from ..log import logger
from ..utils.constants import (
    FETCH_INCOMPLETE,
    FETCH_UPDATE_PROGRESS,
    CLEAN_IN_PROGRESS,
    PARSE_IN_PROGRESS,
    QUERY_COMPLETE,
    LIMIT_MAXED_OUT,
)
from typing import Any


class WebSocketService:
    _query_repo: QueryRepository
    _store: ConnectionStore
    _loop: AbstractEventLoop | None

    def __init__(self, query_repo: QueryRepository) -> None:
        self._store = ConnectionStore()
        self._query_repo = query_repo
        self._loop = None

        @EventLinker.on(FETCH_UPDATE_PROGRESS)
        def handle_progress_update(payload: Event) -> None:
            self.send_by_topic(
                str(payload.data["id"]),
                {"event": FETCH_UPDATE_PROGRESS, "data": payload.data},
            )

        @EventLinker.on(FETCH_INCOMPLETE)
        def handle_incomplete_fetch(payload: Event):
            logger.debug(f"!!! ABOUT TO EMIT EVENT !!! {FETCH_INCOMPLETE}")
            self.send_by_topic(
                str(payload.data["id"]),
                {
                    "event": FETCH_INCOMPLETE,
                    "data": {"message": payload.message, "query": payload.data},
                },
            )
            logger.error(f"!!! EVENT EMITTED !!!")

        @EventLinker.on(CLEAN_IN_PROGRESS)
        def handle_in_progress_clean(payload: Event):
            self.send_by_topic(
                str(payload.data["id"]),
                {
                    "event": CLEAN_IN_PROGRESS,
                    "data": {"message": payload.message, "query": payload.data},
                },
            )

        @EventLinker.on(PARSE_IN_PROGRESS)
        def handle_in_progress_parse(payload: Event):
            self.send_by_topic(
                str(payload.data["id"]),
                {
                    "event": PARSE_IN_PROGRESS,
                    "data": {"message": payload.message, "query": payload.data},
                },
            )

        @EventLinker.on(LIMIT_MAXED_OUT)
        def handle_maxed_limit(payload: Event) -> None:
            self.send_by_topic(
                str(payload.data["id"]),
                {
                    "event": LIMIT_MAXED_OUT,
                    "data": {"message": payload.message, "query": payload.data},
                },
            )

        @EventLinker.on(QUERY_COMPLETE)
        def handle_query_complete(payload: Event) -> None:
            self.send_by_topic(
                str(payload.data["id"]),
                {
                    "event": QUERY_COMPLETE,
                    "data": {"message": payload.message, "query": payload.data},
                },
            )

    def set_event_loop(self, loop: AbstractEventLoop) -> None:
        self._loop = loop

    def get(self) -> list[WebSocketConnection]:
        return self._store.get()

    def get_by_id(self, id: str) -> WebSocketConnection | None:
        return self._store.get_by_id(id)

    def create(self, socket: WebSocket) -> WebSocketConnection:
        connection = WebSocketConnection(socket)

        self._store.set(connection)

        return connection

    def delete(self, id: str) -> None:
        self._store.remove(id)

    def subscribe(self, id: str, topic: UUID) -> WebSocketConnection | None:
        if not self._query_repo.exists(topic):
            return None

        connection = self._store.get_by_id(id)

        if connection is None:
            return None

        connection.topics.set(str(topic))
        self._store.set(connection)

        return connection

    def unsubscribe(self, id: str, topic: str) -> WebSocketConnection | None:
        connection = self._store.get_by_id(id)

        if not connection:
            return None

        connection.topics.remove(topic)
        self._store.set(connection)

        return connection

    def broadcast(self, data: Any) -> None:
        connections = self._store.get()

        async def func():
            if not connections:
                return

            await gather(
                *[connection.socket.send_json(data) for connection in connections],
                return_exceptions=True,
            )

        create_task(func())

    def send(self, id: str, data: Any) -> None:
        connection = self._store.get_by_id(id)

        if connection is None:
            return

        async def func() -> None:
            await connection.socket.send_json(data)

        create_task(func())

    def send_by_topic(self, topic: str, data: Any) -> None:
        if self._loop is None:
            return

        connections = self._store.get()
        subscribed = [connection for connection in connections]

        logger.debug(f"!!! send_by_topic called !!!")
        logger.debug(f"Topic: {topic}")
        logger.debug(f"Total connections: {len(connections)}")
        logger.debug(f"Subscribed connections: {len(subscribed)}")

        async def func() -> None:
            if not connections:
                return

            logger.debug(f"About to send to {len(subscribed)} connections")
            results = await gather(
                *[connection.socket.send_json(data) for connection in subscribed],
                return_exceptions=True,
            )
            logger.debug(f"Send results: {results}")

        logger.debug("About to create task")
        try:
            routine = run_coroutine_threadsafe(func(), self._loop)

            routine.result(timeout=5)
            logger.debug("Message sent successfully")

        except Exception as err:
            logger.error(err, exc_info=True)
