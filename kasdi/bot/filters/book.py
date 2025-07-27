from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter


class ShowReadedBooksFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.text == "📚 Прочитані книги"


class DeleteReadedBookCallback(BaseFilter):
    async def __call__(self, callback_query: CallbackQuery) -> bool:
        return callback_query.data.startswith("delete_book:")


class AddReadedBookCallback(BaseFilter):
    async def __call__(self, callback_query: CallbackQuery) -> bool:
        return callback_query.data == "add_book"


class SaveAllReadedBooksCallback(BaseFilter):
    async def __call__(self, callback_query: CallbackQuery) -> bool:
        return callback_query.data == "save_all_books"


class CancelAllReadedBooksCallback(BaseFilter):
    async def __call__(self, callback_query: CallbackQuery) -> bool:
        return callback_query.data == "cancel_all_books"

class CancelAddingBooksCallback(BaseFilter):
    async def __call__(self, callback_query: CallbackQuery) -> bool:
        return callback_query.data == "cancel_adding_books"
