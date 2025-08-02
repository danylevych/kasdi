from langchain_core.tools import BaseTool
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, Field, PrivateAttr



from databases.models.kasdi import User, MemoryItem
from controllers import user_controller


class MemoryArgs(BaseModel):
    content = Field(
        ...,
        description="Information to store in memory.",
    )


class MemoryTool(BaseTool):
    name: str = "memory_tool"
    description: str = "Store information in the user's memory."
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
