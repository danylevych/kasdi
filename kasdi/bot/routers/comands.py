import os
from aiogram import Bot, Router, types
from aiogram.filters import CommandStart
from aiogram.types import Message

from controllers import user_controller


router = Router(
    name="comands",
)


@router.message(CommandStart())
async def start_handler(message: Message):
    user_data = message.from_user

    user = await user_controller.get_user_by_tg_id(user_data.id)

    if user: # Update existing user
        user.first_name = user_data.first_name
        user.last_name = user_data.last_name
        await user_controller.update_user(user)

        await message.answer(f"Привіт, {user.first_name}! Ти як?")

    else: # Create new user
        user = await user_controller.create_user(
            user_controller.User(
                tg_id=user_data.id,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
            )
        )
        await message.answer(f"Привіт, {user.first_name}! Ти новий користувач. Як справи?")
