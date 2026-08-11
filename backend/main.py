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
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        connection_id = uuid4().hex[:12]
        websocket.state.connection_id = connection_id
        self.active_connections[websocket.state.connection_id] = websocket
        return connection_id

    def disconnect(self, websocket: WebSocket):
        self.active_connections.pop(websocket.state.connection_id, None)

    async def broadcast(self, sender: WebSocket, message: str):
        event = {
            "type": "message",
            "sender_id": sender.state.connection_id,
            "text": message,
        }
        for connection in list(self.active_connections.values()):
            try:
                await connection.send_json(event)
            except (WebSocketDisconnect, RuntimeError):
                self.disconnect(connection)


manager = ConnectionManager()


@app.get('/health')
def health_check():
    return {"status": "ok"}


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    connection_id = await manager.connect(websocket)
    await websocket.send_json(
        {
            "type": "connected",
            "connection_id": connection_id,
        }
    )
    try:
        while True:
            try:
                data = await websocket.receive_json()
                message = IncomingMessage.model_validate(data)
                await manager.broadcast(websocket, message.text)

            except (ValidationError, JSONDecodeError):
                await websocket.send_json(
                    {"type": "error", "detail": "Invalid message"}
                )

    except WebSocketDisconnect:
        print('Client disconnected')

    finally:
        manager.disconnect(websocket)
