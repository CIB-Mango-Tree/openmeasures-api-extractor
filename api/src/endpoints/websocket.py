from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket
from starlette.types import Message
from pydantic import ValidationError
from asyncio import get_running_loop
from json import JSONDecodeError, loads
from ..services import WebSocketService
from ..validator import SubscriptionActionValidator
from ..utils.constants import SUBSCRIBE, UNSUBSCRIBE
from ..log import logger
from typing import Any


class UpdateStreamEndpoint(WebSocketEndpoint):
    encoding = "json"

    async def on_connect(self, websocket: WebSocket) -> None:
        websocket_service: WebSocketService = websocket.app.state.websocket_service
        connection = websocket_service.create(websocket)

        if not websocket_service.is_event_loop_set():
            loop = get_running_loop()
            websocket_service.set_event_loop(loop)

        await connection.socket.accept()
        await connection.socket.send_json({"message": "Connected!!!"})

    async def decode(self, websocket: WebSocket, message: Message) -> Any:
        """Decodes a frame, returning None instead of closing when it cannot.

        Deliberately does not call super(): Starlette's JSON branch closes the socket with 1003
        *before* raising, so catching the exception is too late. Since the client reconnects and
        replays its subscriptions, one bad frame would become a permanent reconnect loop rather
        than a single dropped message.
        """
        text: str | None = message.get("text")

        if text is None and message.get("bytes") is not None:
            try:
                text = message["bytes"].decode("utf-8")

            except UnicodeDecodeError as err:
                logger.error("discarding non-utf8 websocket frame", exc_info=err)
                return None

        if text is None:
            return None

        try:
            return loads(text)

        except JSONDecodeError as err:
            logger.error("discarding undecodable websocket frame", exc_info=err)
            return None

    async def on_receive(self, websocket: WebSocket, data: Any) -> None:
        if data is None:
            return

        websocket_service: WebSocketService = websocket.app.state.websocket_service
        connection = websocket_service.get_by_id(websocket.state.id)

        if connection is None:
            return

        # encoding = "json" means Starlette has already decoded the frame, so `data` is a dict.
        # Calling json.loads on it raised TypeError, which escaped on_receive and killed the
        # connection -- the client then reconnected, replayed its subscription and died again,
        # roughly once a second, so no progress or limit events were ever delivered.
        try:
            payload = loads(data) if isinstance(data, (str, bytes, bytearray)) else data
            validator_data = SubscriptionActionValidator.model_validate(payload)
            topic_str = str(validator_data.topic)

            if validator_data.action.value == SUBSCRIBE:
                if connection.topics.has(topic_str):
                    await connection.socket.send_json(
                        {
                            "event": "SUBSCRIBE:ALREADY_EXISTS",
                            "data": {
                                "message": "this connection is already subscribed to this topic"
                            },
                        }
                    )
                    return

                connection = websocket_service.subscribe(
                    connection.id, validator_data.topic
                )

                if connection is None:
                    return

                await connection.socket.send_json(
                    {
                        "event": "SUBSCRIBE:SUCCESS",
                        "data": {
                            "message": f"this connection has been subscribed to topic: {topic_str}"
                        },
                    }
                )
                return

            if validator_data.action.value == UNSUBSCRIBE:
                connection = websocket_service.unsubscribe(connection.id, topic_str)

                if connection is None:
                    return

                await connection.socket.send_json(
                    {
                        "event": "UNSUBSCRIBE:SUCCESS",
                        "data": {
                            "message": f"this connection has been unsubscribed from topic: {topic_str}"
                        },
                    }
                )
                return

        except ValidationError as err:
            await connection.socket.send_json(
                {
                    "event": "ERRORS:VALIDATION_ERROR",
                    "data": {
                        "message": "an error occurred when validating subscription action",
                        "errors": err.json(),
                    },
                }
            )

        # A malformed frame must never bring the socket down: an exception escaping here
        # terminates the connection, and the client's reconnect makes that a permanent loop.
        except (JSONDecodeError, TypeError, ValueError) as err:
            logger.error("discarding malformed websocket message", exc_info=err)

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        websocket_service: WebSocketService = websocket.app.state.websocket_service
        connection = websocket_service.get_by_id(websocket.state.id)

        if connection is None:
            return

        websocket_service.delete(connection.id)
