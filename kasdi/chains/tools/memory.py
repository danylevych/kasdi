from typing import Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from database.models.kasdi import User
from controllers import user_controller


class MemoryArgs(BaseModel):
    content: str = Field(
        ...,
        description=(
            "A short, clear fact about the user that should be remembered for future conversations. "
            "Include only long-term or recurring information that can help personalize answers."
        ),
    )

class MemoryTool(BaseTool):
    name: str = "memory_tool"
    description: str = (
        "Use this tool to save important information about the user that should persist across conversations. "
        "Call this tool ONLY when the user shares a new fact about themselves, their preferences, dislikes, "
        "or their reading habits that would be useful for future personalization.\n\n"
        "What to store:\n"
        "- Preferred genres, authors, book formats.\n"
        "- Books the user has read, is reading, or wants to read.\n"
        "- Recurring personal preferences that affect conversation style.\n\n"
        "What NOT to store:\n"
        "- Temporary states or moods (e.g., 'today I feel tired').\n"
        "- Information unrelated to books or preferences or dislikes.\n"
        "- Sensitive/private data (passwords, addresses, personal contacts) unless user confirms.\n\n"
        "Store facts in a short, clear form so they can be directly injected into the system prompt."
    )
    args_schema: Type[MemoryArgs] = MemoryArgs

    _user_id: str = PrivateAttr()

    def __init__(self, user_id: str, **data):
        super().__init__(**data)
        self._user_id = user_id

    async def _arun(self, content: str) -> str:
        """
        Asynchronously store information in the user's memory.
        """
        try:
            await user_controller.add_user_memory(
                user=self._user_id,
                content=content
            )
            return "Stored in memory."
        except ValueError as e:
            return str(e)

    def _run(self, content: str, user: User) -> str:
        """
        Store information in the user's memory.
        """
        import asyncio
        return asyncio.run(self._arun(content, user))
