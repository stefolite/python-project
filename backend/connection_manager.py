from fastapi import WebSocket, WebSocketDisconnect
from uuid import uuid4


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        connection_id = uuid4().hex[:12]
        websocket.state.connection_id = connection_id
        room_id = websocket.state.room_id
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][connection_id] = websocket
        return connection_id

    def disconnect(self, websocket: WebSocket):
        room_id = websocket.state.room_id
        connection_id = websocket.state.connection_id
        room = self.active_connections.get(room_id)
        if room is None:
            return
        room.pop(connection_id, None)
        if not room:
            self.active_connections.pop(room_id, None)

    async def broadcast(self, room_id: str, event: dict):
        room = self.active_connections.get(room_id)
        if room is None:
            return
        for connection in list(room.values()):
            try:
                await connection.send_json(event)
            except (WebSocketDisconnect, RuntimeError):
                self.disconnect(connection)
