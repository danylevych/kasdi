from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter


class ShowProfileFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.text == "👤 Про мене"


class AddInstructionCallback(BaseFilter):
    async def __call__(self, callback_query: CallbackQuery) -> bool:
        return callback_query.data == "add_instruction"


class EditInstructionCallback(BaseFilter):
    async def __call__(self, callback_query: CallbackQuery) -> bool:
        return callback_query.data == "edit_instruction"


class DeleteInstructionCallback(BaseFilter):
    async def __call__(self, callback_query: CallbackQuery) -> bool:
        return callback_query.data == "delete_instruction"


class CancelInstructionCallback(BaseFilter):
    async def __call__(self, callback_query: CallbackQuery) -> bool:
        return callback_query.data == "cancel_instruction"
