from typing import List
from datetime import datetime

from pydantic import BaseModel
from beanie import PydanticObjectId

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.tools import BaseTool

from databases.models.kasdi import User
from controllers import user_controller

from .user_service import UserContextService
from .chat_service import ChatService

from chains.utils import read_prompt

from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)

from core.logger import create_scoped_logger


logger = create_scoped_logger("kasdi.agent")


class KasdiConfigs(BaseModel):
    OPENAI_API_KEY     : str
    TAVILY_API_KEY     : str
    FIRE_CRAWL_API_KEY : str

    # LLM Conf
    MODEL              : str = "gpt-4o-mini"
    TEMPERATURE        : float = 0.5

    @classmethod
    def from_env(cls) -> 'KasdiConfigs':
        from dependencies import get_config

        return cls(
            OPENAI_API_KEY=get_config().OPENAI_API_KEY,
            TAVILY_API_KEY=get_config().TAVILY_API_KEY,
            FIRE_CRAWL_API_KEY=get_config().FIRE_CRAWL_API_KEY,
            MODEL=get_config().LLM_MODEL,
            TEMPERATURE=get_config().LLM_TEMPERATURE,
        )


class KasdiAgent:
    """Main Kasdi React Agent orchestrator."""

    def __init__(self,
                 configs: KasdiConfigs = KasdiConfigs.from_env()
                ):
        self.user_service = UserContextService()
        self.chat_service = ChatService()
        self.configs = configs

    def _build_system_prompt(self, user_context: dict) -> str:
        """Build the system prompt with user context."""
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

        return system_prompt.format(
            user_name=user_context["user_name"],
            user_instructions=user_context["user_instructions"],
            users_books=user_context["users_books"],
            memory=user_context["memory"],
            date=datetime.now().strftime("%Y-%m-%d"),
        )

    def _get_tools(self, user: User) -> List[BaseTool]:
        """Get tools based on user configuration."""
        from ..tools import (
            MemoryTool,
            SearchBooksTool,
            SearchBooksByQueryTool,
            WebScrapeTool,
            WebSearchTool,
        )

        tools = [
            SearchBooksTool(),
            SearchBooksByQueryTool(
                openai_api_key=self.configs.OPENAI_API_KEY
            ),
            WebScrapeTool(
                api_key=self.configs.FIRE_CRAWL_API_KEY
            ),
            WebSearchTool(
                tavily_api_key=self.configs.TAVILY_API_KEY
            ),
        ]

        if user.memory_enabled:
            logger.info(f"Memory is enabled for user {user.id}, adding MemoryTool")
            tools.append(MemoryTool(user_id=str(user.id)))

        return tools

    def _build_react_agent(self, user: User, system_message: str):
        """Build and configure the React agent."""
        tools = self._get_tools(user)

        llm = ChatOpenAI(
            model=self.configs.MODEL,
            temperature=self.configs.TEMPERATURE,
            api_key=self.configs.OPENAI_API_KEY,
        )

        return create_react_agent(
            model=llm,
            prompt=system_message,
            tools=tools,
        )

    @retry(  # Retry on any exception
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(Exception)
    )
    async def execute(self, user_id: PydanticObjectId, chat_id: PydanticObjectId) -> str:
        """Execute the agent conversation."""
        logger.info(f"Executing Kasdi agent for user {user_id} in chat {chat_id}")

        user = await user_controller.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user_context = await self.user_service.prepare_user_context(user)
        chat_history = await self.chat_service.get_chat_history(chat_id)
        system_message = self._build_system_prompt(user_context)
        agent = self._build_react_agent(user, system_message)

        response = await agent.ainvoke(
            {"messages": chat_history},
            {"configurable": {"thread_id": str(chat_id)}},
        )

        logger.info(f"Agent response DONE for user {user_id} in chat {chat_id}")

        return response


async def run_kasdi(
    user_id: PydanticObjectId,
    chat_id: PydanticObjectId,
) -> str:
    """Backward compatibility wrapper for the original run_kasdi function."""
    agent = KasdiAgent()
    return await agent.execute(user_id, chat_id)
