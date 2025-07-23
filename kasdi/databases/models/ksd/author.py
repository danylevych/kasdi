from beanie import BackLink, Document, Indexed
from pydantic import Field
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .book import Book


class Author(Document):
    class Settings:
        name = "authors"

    name: str = Indexed(str, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    bio: Optional[str] = None
    birth_year: Optional[int] = None
    nationality: Optional[str] = None
    website: Optional[str] = None
