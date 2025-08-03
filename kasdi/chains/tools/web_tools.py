from langchain_tavily import TavilySearch as WebSearchTool
from langchain_community.document_loaders import FireCrawlLoader
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

from dependencies import get_config

class WebSearchToolArgs(BaseModel):
    url: str = Field(
        ...,
        description="The URL to search for.",
    )


class WebScrapeTool(BaseTool):
    name: str = "web_scrape"
    description: str = "Scrape the content of a web page."
    args_schema: Type[WebSearchToolArgs] = WebSearchToolArgs

    async def _arun(self, url: str) -> str:
        """
        Asynchronously scrape the content of the given URL.
        """
        loader = FireCrawlLoader(url=[url], api_key=get_config().FIRE_CRAWL_API_KEY, mode='scrape')
        documents = await loader.aload()
        if not documents:
            return f"No content found at {url}"

        return "\n".join(doc.page_content for doc in documents)

    def _run(self, url: str) -> str:
        """
        Scrape the content of the given URL.
        """
        loader = FireCrawlLoader(url=[url], api_key=get_config().FIRE_CRAWL_API_KEY, mode='scrape')
        documents = loader.load()
        if not documents:
            return f"No content found at {url}"

        return "\n".join(doc.page_content for doc in documents)
