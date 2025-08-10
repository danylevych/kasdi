from enum import Enum
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field


class Role(str, Enum):
    ASSISTANT = "assistant"
    USER = "user"


class Message(BaseModel):
    message_id: str = Field(default=str(uuid4()))
    role: Role
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
