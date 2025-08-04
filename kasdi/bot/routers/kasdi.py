import asyncio
from aiogram import Router
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

from chains.kasdi import run_kasdi

from controllers import (
    user_controller,
    chat_controller,
)

from bot.utils import make_telegram_safe_message
from bot.parsers.voice_parser import process_voice_message

# TODO: AFTER 40 MESSAGES MAKE THE FANTUNE OF HOW DOES THE USER COMMUNICATE AND USE IT TO MAKE BETTER RESPONSES


router = Router(
    name="kasdi",
)

_message_locks: dict[int, asyncio.Lock] = {}


async def _handle_user_message(message: Message):
    user = await user_controller.get_user_by_tg_id(message.from_user.id)

    if not user:
        await message.answer("Будь ласка, спочатку почніть розмову з ботом командою /start.")
        return

    chat = await chat_controller.get_or_create_tg_chat(user.id, message.chat.id)

    text = message.text or ""

    if message.voice:
        text = await process_voice_message(message)

    await chat_controller.add_message_to_chat(
        chat=chat,
        message=chat_controller.Message(
            role=chat_controller.Role.USER,
            content=text
        )
    )

    async with ChatActionSender(bot=message.bot, chat_id=message.chat.id):
        response = await run_kasdi(
            user_id=user.id,
            chat_id=chat.id
        )

        print(f"Response from Kasdi: {response}")
        final_message = response["messages"][-1].content

        await message.answer(make_telegram_safe_message(final_message), parse_mode="markdown")
        await chat_controller.add_message_to_chat(
            chat=chat,
            message=chat_controller.Message(
                role=chat_controller.Role.ASSISTANT,
                content=final_message
            )
        )


@router.message()
async def handle_user_message(message: Message):
    """Handle user messages in a chat."""
    if message.chat.id not in _message_locks:
        _message_locks[message.chat.id] = asyncio.Lock()
    # else:
    #     # TODO: MAKE DUNAMIC GENERATION
    #     await message.answer("Будь ласка, зачекай, я обробляю відповідаю..")

    async with _message_locks[message.chat.id]:
        await _handle_user_message(message)
