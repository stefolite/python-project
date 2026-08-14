from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from uuid import uuid4
from pydantic import BaseModel, Field, ValidationError
from typing import Literal
from json import JSONDecodeError
from contextlib import asynccontextmanager


class IncomingMessage(BaseModel):
    type: Literal["message"]
    text: str = Field(min_length=1, max_length=500)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App starting...")
    yield
    print("App closing...")


app = FastAPI(lifespan=lifespan)


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


manager = ConnectionManager()


@app.get('/health')
def health_check():
    return {"status": "ok"}


@app.websocket('/ws/{room_id}')
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    websocket.state.room_id = room_id
    connection_id = await manager.connect(websocket)
    try:
        await websocket.send_json(
            {
                "type": "connected",
                "connection_id": connection_id,
            }
        )
        event = {
            "type": "member_joined",
            "connection_id": connection_id,
        }
        await manager.broadcast(websocket.state.room_id, event)
        while True:
            try:
                data = await websocket.receive_json()
                message = IncomingMessage.model_validate(data)
                event = {
                    "type": "message",
                    "sender_id": websocket.state.connection_id,
                    "text": message.text,
                }
                await manager.broadcast(websocket.state.room_id, event)

            except (ValidationError, JSONDecodeError):
                await websocket.send_json(
                    {"type": "error", "detail": "Invalid message"}
                )

    except WebSocketDisconnect:
        print('Client disconnected')

    finally:
        manager.disconnect(websocket)
        event = {
            "type": "member_left",
            "connection_id": connection_id,
        }
        await manager.broadcast(room_id, event)
