from typing import List
from datetime import datetime
from beanie import PydanticObjectId
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage

from databases.models.kasdi import Chat, Message, Role, User
from langchain.memory import ConversationBufferMemory


from .utils import read_prompt


from controllers import user_controller, readed_book_controller, chat_controller


async def prepare_readed_books(user: User) -> str:
    readed_books = await readed_book_controller.get_readed_books_by_user_id(user.id)

    if not readed_books:
        return "The user does not provide any read books."

    book_info = [
        f"Title: {book.title}\nAuthor: {book.author or 'Unknown'}\nUser Notes: {book.notes or 'No notes'}"
        for book in readed_books
    ]

    return "\n\n".join(book_info)


async def prepare_user_instructions(user: User) -> str:
    if not user.custom_instruction:
        return "The user has no specific instructions."

    return user.custom_instruction

async def prepare_memory(user: User) -> str:
    if user.memory_enabled is False:
        return "Memory is disabled for this user."

    if not user.memory:
        return "We do not have any memory for this user."

    memory_items = [
        "- " + item.content + f" (created at {item.created_at.strftime('%Y-%m-%d')})"
        for item in user.memory if item.content
    ]

    return "\n".join(memory_items)


async def get_chat_history(chat_id: PydanticObjectId) -> List[BaseMessage]:
    chat = await chat_controller.get_chat_by_id(chat_id)

    if not chat:
        return []

    return [
        HumanMessage(content=message.content) if message.role == Role.USER
        else AIMessage(content=message.content)
        for message in chat.messages
    ]


async def run_kasdi(
    api_key: str,
    user_id: PydanticObjectId,
    chat_id: PydanticObjectId,
) -> str:
    user = await user_controller.get_user_by_id(user_id)

    if not user:
        raise ValueError("User not found")

    user_name = f"{user.first_name} {user.last_name or ''}".strip()
    users_books = await prepare_readed_books(user)
    user_instructions = await prepare_user_instructions(user)
    memory = await prepare_memory(user)

    system_prompt = PromptTemplate(
        template=read_prompt("kasdi_prompt.md"),
        input_variables=[
            "user_name",
            "user_instructions",
            "users_books",
            "memory",
            "date",
        ],
    )

    system_message = system_prompt.format(
        user_name=user_name,
        user_instructions=user_instructions,
        users_books=users_books,
        memory=memory,
        date=datetime.now().strftime("%Y-%m-%d"),
    )

    from .tools import (
        MemoryTool,
        SearchBooksByQueryTool,
        WebScrapeTool,
        web_search,
    )

    tools = [
        SearchBooksByQueryTool(),
        WebScrapeTool(),
        web_search,
    ]

    if user.memory_enabled:
        tools.append(MemoryTool(user_id=str(user.id)))

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.5,
        api_key=api_key,
    )

    chat_history = await get_chat_history(chat_id)

    kasdi = create_react_agent(
        model=llm,
        prompt=system_message,
        tools=tools,
    )

    print(system_message)

    response = await kasdi.ainvoke(
            {"messages": chat_history},
            {"configurable": {"thread_id": str(chat_id)}},
        )

    return response
