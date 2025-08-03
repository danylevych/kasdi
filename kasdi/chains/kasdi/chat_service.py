from typing import List
from beanie import PydanticObjectId
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from databases.models.kasdi import Chat, Role
from controllers import chat_controller


class ChatService:
    """Service for handling chat history and message management."""

    @staticmethod
    async def get_chat_history(chat_id: PydanticObjectId) -> List[BaseMessage]:
        """Get chat history and convert to LangChain messages."""
        chat = await chat_controller.get_chat_by_id(chat_id)

        if not chat:
            return []

        return [
            HumanMessage(content=message.content) if message.role == Role.USER
            else AIMessage(content=message.content)
            for message in chat.messages
        ]
