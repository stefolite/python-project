from fastapi import WebSocket, WebSocketDisconnect
from uuid import uuid4


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        connection_id = uuid4().hex[:12]
        websocket.state.connection_id = connection_id
        conversation_id = websocket.state.conversation_id
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = {}
        self.active_connections[conversation_id][connection_id] = websocket
        return connection_id

    def disconnect(self, websocket: WebSocket):
        conversation_id = websocket.state.conversation_id
        connection_id = websocket.state.connection_id
        conversation = self.active_connections.get(conversation_id)
        if conversation is None:
            return
        conversation.pop(connection_id, None)
        if not conversation:
            self.active_connections.pop(conversation_id, None)

    async def broadcast(self, conversation_id: int, event: dict):
        conversation = self.active_connections.get(conversation_id)
        if conversation is None:
            return
        for connection in list(conversation.values()):
            try:
                await connection.send_json(event)
            except (WebSocketDisconnect, RuntimeError):
                self.disconnect(connection)
