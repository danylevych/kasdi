from beanie import Document, Indexed, BackLink
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .readed_book import ReadedBook


class MemoryItem(BaseModel):
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class User(Document):

    model_config = {
        "arbitrary_types_allowed": True
    }

    class Settings:
        name = "users"

    tg_id: int = Indexed(unique=True)
    first_name: str
    last_name: Optional[str] = None

    custom_instruction: Optional[str] = None
    memory_enabled: bool = True
    memory: Optional[List[MemoryItem]] = None

    readed_books: List[BackLink["ReadedBook"]] = Field(
        default_factory=list,
        original_field="user"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
