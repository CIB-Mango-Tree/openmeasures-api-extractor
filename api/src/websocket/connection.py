from starlette.websockets import WebSocket
from uuid import uuid4
from .topic import TopicStore


class WebSocketConnection:
    id: str
    topics: TopicStore
    socket: WebSocket

    def __init__(self, socket: WebSocket) -> None:
        self.id = str(uuid4())
        self.topics = TopicStore()
        socket.state["id"] = self.id
        self.socket = socket
