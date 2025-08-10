from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from controllers import (
    user_controller,
)


router = Router(
    name="commands",
)

@router.message(CommandStart())
async def start_handler(message: Message):
    user_data = message.from_user

    user = await user_controller.get_user_by_tg_id(user_data.id)

    if user:
        user.first_name = user_data.first_name
        user.last_name = user_data.last_name
        await user_controller.update_user(user)
        greeting = f"Привіт, {user.first_name}! Ти як?"
    else:
        user = user_controller.User(
            tg_id=user_data.id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        await user_controller.create_user(user)
        greeting = f"Привіт, {user.first_name}! Ти новий користувач. Як справи?"

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Про мене")],
            [KeyboardButton(text="📚 Прочитані книги")]
        ],
        resize_keyboard=True
    )

    await message.answer(greeting, reply_markup=keyboard)

