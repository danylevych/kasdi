import base64
from aiogram import Bot
from typing import BinaryIO, List, Optional
from langchain_core.messages import HumanMessage

from bot.types import BookCreateMessage
from databases.models.kasdi import ReadedBook
from chains.parse_data import ParseBookDataChain, BookDataList

from core.logger import create_scoped_logger


logger = create_scoped_logger("kasdi.bot.utils")


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
                    actual_readed_books: Optional[List[ReadedBook]]
                ) -> List[ReadedBook]:
        actual_readed_books_str = self._preatyfy_readed_books(actual_readed_books) if actual_readed_books else " No readed books found."
        human_message = self._make_human_message(messages)

        response = await self.parser_chain.arun(
            actual_books=actual_readed_books_str,
            human_message=human_message
        )

        return self._create_readed_books_entities(response)


    def _make_human_message(self, messages: List[BookCreateMessage]) -> HumanMessage:
        human_message = HumanMessage(content=[])

        def decode_photo(photo: BinaryIO) -> str:
            return base64.b64encode(photo.read()).decode('utf-8')

        for message in messages:
            if message.text:
                human_message.content.append({
                    "type": "text",
                    "content": message.text
                })

            if message.photos:
                for photo in message.photos:
                    photo_info = self.bot.get_file(photo)
                    photo_data = self.bot.download_file(photo_info.file_path)

                    image_url = f"data:image/{photo_info.file_path.split('.')[-1]};base64,{decode_photo(photo_data)}"

                    human_message.content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    })

        return human_message

    def _preatyfy_readed_books(self, readed_books: List[ReadedBook]) -> str:
        """
        Prettify the readed books data for the prompt.

        :param readed_books: List of ReadedBook objects.
        :return: Formatted string of readed books.
        """
        return "\n".join(
            f"Title: {book.title}, Author: {book.author or 'Unknown'}, Notes: {book.notes or 'No notes'}"
            for book in readed_books
        )

    def _create_readed_books_entities(self, response: BookDataList) -> List[ReadedBook]:
        """
        Create ReadedBook entities from the parsed response.

        :param response: Parsed BookData object.
        :return: List of ReadedBook entities.
        """
        return [
            ReadedBook(
                title=book.title,
                author=book.author,
                notes=book.notes
            )
            for book in response.root
        ]
