from pydantic import BaseModel, Field
from typing import Literal


class IncomingMessage(BaseModel):
    type: Literal["message"]
    text: str = Field(min_length=1, max_length=500)


class MessageEvent(BaseModel):
    type: Literal["message"] = "message"
    sender_id: str
    text: str


class ConnectedEvent(BaseModel):
    type: Literal["connected"] = "connected"
    connection_id: str


class MemberJoinedEvent(BaseModel):
    type: Literal["member_joined"] = "member_joined"
    connection_id: str


class MemberLeftEvent(BaseModel):
    type: Literal["member_left"] = "member_left"
    connection_id: str


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    code: Literal["invalid_message"] = "invalid_message"
    detail: str