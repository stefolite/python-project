from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from json import JSONDecodeError
from contextlib import asynccontextmanager
from backend.schemas import (
    IncomingMessage,
    MessageEvent,
    ConnectedEvent,
    MemberJoinedEvent,
    MemberLeftEvent,
    ErrorEvent,
)
from backend.connection_manager import ConnectionManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App starting...")
    yield
    print("App closing...")


app = FastAPI(lifespan=lifespan)


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
            ConnectedEvent(connection_id=connection_id).model_dump()
        )
        event = MemberJoinedEvent(connection_id=connection_id).model_dump()
        await manager.broadcast(websocket.state.room_id, event)
        while True:
            try:
                data = await websocket.receive_json()
                message = IncomingMessage.model_validate(data)
                event = MessageEvent(
                    sender_id=connection_id,
                    text=message.text
                )
                await manager.broadcast(
                    websocket.state.room_id,
                    event.model_dump()
                )

            except (ValidationError, JSONDecodeError):
                await websocket.send_json(
                    ErrorEvent(detail="Invalid message").model_dump()
                )

    except WebSocketDisconnect:
        print('Client disconnected')

    finally:
        manager.disconnect(websocket)
        event = MemberLeftEvent(connection_id=connection_id).model_dump()
        await manager.broadcast(room_id, event)
