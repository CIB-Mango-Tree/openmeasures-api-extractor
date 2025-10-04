from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket
from pydantic import ValidationError
from lagom import injectable
from ..services import WebSocketService
from ..validator import SubscriptionActionValidator
from ..utils.constants import SUBSCRIBE, UNSUBSCRIBE
from typing import Any


class UpdateStreamEndpoint(WebSocketEndpoint):
    async def on_connect(
        self, websocket: WebSocket, websocket_service: WebSocketService = injectable
    ) -> None:
        connection = websocket_service.create(websocket)

        await connection.socket.send_json({"message": "Connected!!!"})

    async def on_receive(
        self,
        websocket: WebSocket,
        data: Any,
        websocekt_service: WebSocketService = injectable,
    ) -> None:
        connection = websocekt_service.get_by_id(websocket.state.id)

        if connection is None:
            return

        try:
            validator_data = SubscriptionActionValidator.model_validate(data)
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

                connection = websocekt_service.subscribe(connection.id, topic_str)

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

            if validator_data.action.value == UNSUBSCRIBE:
                connection = websocekt_service.unsubscribe(connection.id, topic_str)

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

        except ValidationError as err:
            if connection is None:
                return

            await connection.socket.send_json(
                {
                    "event": "ERRORS:VALIDATION_ERROR",
                    "data": {
                        "message": "an error occurred when validating subscription action",
                        "errors": err.json(),
                    },
                }
            )

    async def on_disconnect(
        self,
        websocket: WebSocket,
        close_code: int,
        websocket_service: WebSocketService = injectable,
    ) -> None:
        connection = websocket_service.get_by_id(websocket.state.id)

        if connection is None:
            return

        await connection.socket.send_json({"message": "Closing connection..."})
        websocket_service.delete(connection.id)
