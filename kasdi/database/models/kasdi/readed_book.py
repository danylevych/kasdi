from beanie import Document, Link
from bson import ObjectId
from pydantic import Field
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class ReadedBook(Document):

    model_config = {
        "arbitrary_types_allowed": True
    }

    class Settings:
        name = "readed_books"

    user: Link["User"]
    ksd_book_id: Optional[ObjectId] = None

    title: str
    author: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
