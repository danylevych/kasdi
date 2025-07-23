from beanie import Document, Link
from pydantic import Field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .message import Message


class Chat(Document):
    class Settings:
        name = "chats"

    user: Link["User"] = Field(unique=True)
    title: str
    description: Optional[str] = None
    messages: List["Message"] = Field(default_factory=list)
