from .connection import WebSocketConnection


class ConnectionStore:
    _connections: dict[str, WebSocketConnection]

    def __init__(self) -> None:
        self._connections = {}

    def get_by_id(self, id: str) -> WebSocketConnection | None:
        if id not in self._connections:
            return None

        return self._connections[id]

    def get(self) -> list[WebSocketConnection]:
        return list(self._connections.values())

    def set(self, connection: WebSocketConnection) -> None:
        self._connections[connection.id] = connection

    def remove(self, id: str) -> None:
        if id not in self._connections:
            return

        del self._connections[id]
