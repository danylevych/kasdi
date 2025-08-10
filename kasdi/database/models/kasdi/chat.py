from beanie import Document, Link
from pydantic import Field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .message import Message, Role


class Chat(Document):
    class Settings:
        name = "chats"

    tg_id: int = Field(unique=True)

    user: Link["User"] = Field(unique=True)
    title: Optional[str] = None
    description: Optional[str] = None
    messages: List["Message"] = Field(default_factory=list)
