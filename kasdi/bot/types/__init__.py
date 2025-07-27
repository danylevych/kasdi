from aiogram.types import Message
from typing import List, Optional
from pydantic import BaseModel, Field


class BookCreateMessage(BaseModel):
    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "extra": "ignore"
    }

    text   : Optional[str]       = Field(None, description="Text content of the message")
    photos : Optional[List[str]] = Field(default_factory=list)


    @classmethod
    def from_message(cls, message: Message) -> "BookCreateMessage":
        """
        Create a BookCreateMessage instance from a message object.
        """
        entity = cls()

        if message.text:
            entity.text = message.text

        if message.photo:
            seen = set()
            for photo in message.photo:
                if photo.file_id not in seen:
                    entity.photos.append(photo.file_id)
                    seen.add(photo.file_id)

        return entity
