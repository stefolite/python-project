from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    HTTPException
)
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
    ConversationCreate,
    ConversationResponse
)
from backend.connection_manager import ConnectionManager
from backend.database import get_session
from backend.models import Conversation
from sqlalchemy import text, select, asc
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App starting...")
    yield
    print("App closing...")


app = FastAPI(lifespan=lifespan)


manager = ConnectionManager()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health_db")
async def health_check_db(session: AsyncSession = Depends(get_session)):
    result = await session.execute(text("SELECT 1"))
    value = result.scalar_one()
    if value == 1:
        return {"status": "ok"}


@app.websocket("/ws/{room_id}")
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
        print("Client disconnected")

    finally:
        manager.disconnect(websocket)
        event = MemberLeftEvent(connection_id=connection_id).model_dump()
        await manager.broadcast(room_id, event)


@app.post("/conversations", response_model=ConversationResponse)
async def conversation_post(
    payload: ConversationCreate,
    session: AsyncSession = Depends(get_session),
):
    conversation = Conversation(name=payload.name)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


@app.get("/conversations", response_model=list[ConversationResponse])
async def conversations_list(session: AsyncSession = Depends(get_session)):
    stmt = select(Conversation).order_by(asc(Conversation.id))
    result = await session.execute(stmt)
    return result.scalars().all()


@app.get(
        "/conversations/{conversation_id}",
        response_model=ConversationResponse
)
async def conversation_get(
    conversation_id: int,
    session: AsyncSession = Depends(get_session)
):
    conversation = await session.get(Conversation, conversation_id)
    if conversation:
        return conversation
    raise HTTPException(status_code=404, detail="No conversation with such id")
