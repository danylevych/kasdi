

from typing import Optional
from beanie import PydanticObjectId

from database.models.kasdi import Chat, Message, Role

from controllers import user_controller

async def get_chat_by_id(chat_id: PydanticObjectId) -> Optional[Chat]:
    """
    Get a chat by its ID.

    :param chat_id: The ID of the chat to be fetched.
    :return: The Chat object if found, otherwise None.
    """
    return await Chat.find_one(Chat.id == chat_id)


async def get_or_create_tg_chat(user_id: str, tg_chat_id: int) -> Chat:
    """
    Get or create a Telegram chat for a user.

    :param user_id: The ID of the user.
    :param tg_chat_id: The Telegram chat ID.
    :return: The Chat object.
    """
    chat = await Chat.find_one(Chat.tg_id == tg_chat_id)
    user = await user_controller.get_user_by_id(user_id)
    if not chat:
        chat = Chat(tg_id=tg_chat_id, user=user)
        await chat.save()

    return chat


async def add_message_to_chat(chat: Chat, message: Message) -> None:
    """
    Add a message to a chat.

    :param message: The Message object to be added.
    """
    chat = await get_chat_by_id(chat.id)

    if not chat:
        raise ValueError("Chat not found")

    chat.messages.append(message)
    await chat.save()
