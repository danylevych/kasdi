import base64
from aiogram import Bot
from typing import BinaryIO, List, Optional
from langchain_core.messages import HumanMessage

from bot.types import BookCreateMessage
from database.models.kasdi import ReadedBook, User
from chains.parse_data import ParseBookDataChain, BookDataList

from .voice_parser import VoiceParser

from core.logger import create_scoped_logger


logger = create_scoped_logger("BookMessagesParser")


class BookMessagesParser:
    def __init__(self, bot: Bot, openai_api_key: str):
        self.bot = bot
        self.parser_chain = ParseBookDataChain(
            api_key=openai_api_key,
            model_name="gpt-4o-mini",
            temperature=0.0
        )

    async def parse(self,
                    messages: List[BookCreateMessage],
                    user: User,
                ) -> List[ReadedBook]:
        human_message = await self._make_human_message(messages)

        response = await self.parser_chain.arun(
            human_message=human_message,
        )

        return self._create_readed_books_entities(response, user)


    async def _make_human_message(self, messages: List[BookCreateMessage]) -> HumanMessage:
        human_message = HumanMessage(content=[])

        def decode_photo(photo: BinaryIO) -> str:
            return base64.b64encode(photo.read()).decode('utf-8')

        for message in messages:
            if message.text:
                human_message.content.append({
                    "type": "text",
                    "text": message.text
                })

            if message.photos:
                for photo in message.photos:
                    photo_info = await self.bot.get_file(photo.file_id)
                    photo_data = await self.bot.download_file(photo_info.file_path)

                    image_url = f"data:image/{photo_info.file_path.split('.')[-1]};base64,{decode_photo(photo_data)}"

                    human_message.content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    })

                    if photo.caption:
                        human_message.content.append({
                            "type": "text",
                            "text": photo.caption
                        })

            if message.voice:
                from core.configs import get_config

                voice_info = await self.bot.get_file(message.voice)
                voice_data = await self.bot.download_file(voice_info.file_path)

                voice_parser = VoiceParser(
                    api_key=get_config().OPENAI_API_KEY,
                    language="uk"
                )

                transcription = await voice_parser.run(voice_data.read())

                human_message.content.append({
                    "type": "text",
                    "text": transcription
                })

        return human_message

    def _create_readed_books_entities(self, response: BookDataList, user: User) -> List[ReadedBook]:
        """
        Create ReadedBook entities from the parsed response.

        :param response: Parsed BookData object.
        :return: List of ReadedBook entities.
        """
        print(f"Parsed response: {response}")
        return [
            ReadedBook(
                title=book.get("title", ""),
                author=book.get("author", ""),
                notes=book.get("notes", ""),
                user=user
            )
            for book in response
        ]
