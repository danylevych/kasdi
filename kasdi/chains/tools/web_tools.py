from langchain_tavily import TavilySearch as WebSearchTool
from firecrawl import FirecrawlApp, AsyncFirecrawlApp
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from typing import Type


class WebSearchToolArgs(BaseModel):
    url: str = Field(
        ...,
        description=(
            "The full URL of the web page to scrape. Must be a direct link to the specific page "
            "the user wants information from. Only use URLs in allowed languages (no russian sources). "
            "Example: 'https://ksd.ua/book/harry-potter-i-kamen-filosofskiy/'."
        ),
    )


class WebScrapeTool(BaseTool):
    name: str = "web_scrape"
    description: str = (
        "Use this tool to retrieve the visible content of a specific web page. "
        "It converts the page into clean markdown or HTML so you can extract relevant information."
    )
    args_schema: Type[WebSearchToolArgs] = WebSearchToolArgs

    _api_key: str = PrivateAttr()

    def __init__(self, api_key: str, **data):
        super().__init__(**data)
        self._api_key = api_key

    async def _arun(self, url: str) -> str:
        """
        Asynchronously scrape the content of the given URL.
        """
        try:
            app = AsyncFirecrawlApp(api_key=self._api_key)
            res = await app.scrape_url(url, formats=["markdown"])
            return res.markdown or res.html or "No content"

        except Exception as e:
            return f"Error scraping URL: {e}"


    def _run(self, url: str) -> str:
        """
        Scrape the content of the given URL.
        """
        try:
            app = FirecrawlApp(api_key=self._api_key)
            res = app.scrape_url(url, formats=["markdown"])
            return res.markdown or res.html or "No content"

        except Exception as e:
            return f"Error scraping URL: {e}"


if __name__ == "__main__":
    # Example usage
    from dependencies import get_config
    tool = WebScrapeTool(api_key=get_config().FIRE_CRAWL_API_KEY)

    result = tool._run(url="https://itc.ua/en/articles/babel-or-the-necessity-of-violence-rebecca-kwan-an-alternative-history-fantasy-about-the-power-of-words-and-the-importance-of-language/")
    print(result)
