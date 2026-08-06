import uuid

from fastapi import WebSocket


class ConnectionManager:
    """Per-process registry of open conversation sockets, keyed by match_id.

    In-memory and single-process, matching the current modular-monolith
    deployment; multi-process scaling would need a Redis pub/sub fan-out.
    """

    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[WebSocket]] = {}

    async def connect(self, match_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(match_id, set()).add(websocket)

    def disconnect(self, match_id: uuid.UUID, websocket: WebSocket) -> None:
        connections = self._connections.get(match_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            del self._connections[match_id]

    async def broadcast(self, match_id: uuid.UUID, payload: dict) -> None:
        for websocket in list(self._connections.get(match_id, ())):
            await websocket.send_json(payload)


manager = ConnectionManager()
