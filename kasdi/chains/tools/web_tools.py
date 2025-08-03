from langchain_tavily import TavilySearch as WebSearchTool
from langchain_community.document_loaders import FireCrawlLoader
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from typing import Type


class WebSearchToolArgs(BaseModel):
    url: str = Field(
        ...,
        description="The URL to search for.",
    )


class WebScrapeTool(BaseTool):
    name: str = "web_scrape"
    description: str = "Scrape the content of a web page."
    args_schema: Type[WebSearchToolArgs] = WebSearchToolArgs

    _api_key: str = PrivateAttr()

    def __init__(self, api_key: str, **data):
        super().__init__(**data)
        self._api_key = api_key

    async def _arun(self, url: str) -> str:
        """
        Asynchronously scrape the content of the given URL.
        """
        loader = FireCrawlLoader(url=[url], api_key=self._api_key, mode='scrape')
        documents = await loader.aload()
        if not documents:
            return f"No content found at {url}"

        return "\n".join(doc.page_content for doc in documents)

    def _run(self, url: str) -> str:
        """
        Scrape the content of the given URL.
        """
        loader = FireCrawlLoader(url=[url], api_key=self._api_key, mode='scrape')
        documents = loader.load()
        if not documents:
            return f"No content found at {url}"

        return "\n".join(doc.page_content for doc in documents)
