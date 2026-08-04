from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from uuid import uuid4
from pydantic import BaseModel, Field, ValidationError
from typing import Literal
from json import JSONDecodeError


class IncomingMessage(BaseModel):
    type: Literal["message"]
    text: str = Field(min_length=1, max_length=500)


app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        websocket.state.connection_id = uuid4().hex[:12]
        self.active_connections[websocket.state.connection_id] = websocket

    def disconnect(self, websocket: WebSocket):
        self.active_connections.pop(websocket.state.connection_id, None)

    async def broadcast(self, sender: WebSocket, message: str):
        event = {
            "type": "message",
            "sender_id": sender.state.connection_id,
            "text": message,
        }
        for connection in list(self.active_connections.values()):
            await connection.send_json(event)


manager = ConnectionManager()


@app.get('/health')
def health_check():
    return {"status": "ok"}


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
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
