from aiogram.types import Message
from typing import List, Optional
from pydantic import BaseModel, Field


class PhotoModel(BaseModel):
    file_id: str = Field(..., description="Unique identifier for the photo file")
    caption: Optional[str] = Field(None, description="Caption for the photo, if any")

class BookCreateMessage(BaseModel):
    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "extra": "ignore"
    }

    text   : Optional[str]              = Field(None, description="Text content of the message")
    photos : Optional[List[PhotoModel]] = Field(default_factory=list)
    voice  : Optional[str]              = Field(None, description="Voice message file ID, if any")

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
                    entity.photos.append(PhotoModel(file_id=photo.file_id, caption=message.caption or None))
                    seen.add(photo.file_id)

        if message.voice:
            entity.voice = message.voice.file_id


        return entity
