from .connection import WebSocketConnection
from typing import Dict, List


class ConnectionStore:
    _connections: Dict[str, WebSocketConnection]

    def __init__(self) -> None:
        self._connections = {}

    def get_by_id(self, id: str) -> WebSocketConnection:
        if id not in self._connections:
            return None

        return self._connections[id]

    def get(self) -> List[WebSocketConnection]:
        return self._connections.values()

    def set(self, connection: WebSocketConnection) -> None:
        self._connections[connection.id] = connection

    def remove(self, id: str) -> None:
        if id not in self._connections:
            return

        del self._connections[id]
