from pydantic import BaseModel
from typing import Literal


class MessageEvent(BaseModel):
    type: Literal["message"] = "message"
    sender_id: str
    text: str


event = MessageEvent(
    sender_id="123",
    text="123",
)

print(event)
print(event.model_dump())
