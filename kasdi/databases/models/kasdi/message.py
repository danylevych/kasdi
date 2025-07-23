from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class Role(str, Enum):
    ASSISTANT = "assistant"
    USER = "user"


class Message(BaseModel):
    message_id: int
    role: Role
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
