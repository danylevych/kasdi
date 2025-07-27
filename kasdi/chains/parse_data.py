from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field, RootModel

from .utils import read_prompt


class BookData(BaseModel):
    title  : str           = Field(..., description="The title of the book")
    author : Optional[str] = Field(None, description="The author of the book")
    notes  : Optional[str] = Field(None, description="User's notes about the book")


class BookDataList(RootModel[List[BookData]]):
    pass


class ParseBookDataChain:
    def __init__(self,
                 api_key: str,
                 model_name: str = "gpt-4o-mini",
                 temperature: float = 0.0
                ):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
        )

        self.output_parser = JsonOutputParser(
            pydantic_object=BookDataList
        )

        self.system_prompt = PromptTemplate(
            input_variables=["actual_books"],
            template=read_prompt("parse_prompt.md")
        )

    async def arun(self, actual_books: str, human_message: HumanMessage) -> BookDataList:
        messages = [
            SystemMessage(content=self.system_prompt.format(actual_books=actual_books)),
            human_message
        ]

        response = await self.llm.ainvoke(messages, tools=[{"type": "web_search_preview"}])
        return self.output_parser.parse(response.content)


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    chain = ParseBookDataChain(api_key=api_key)
    print(chain.system_prompt.format(actual_books="Some example books data"))

    import asyncio
    async def main():
        response = await chain.arun(
            actual_books="Some example books data",
            human_message=HumanMessage(content="I read 'The Great Gatsby' by F. Scott Fitzgerald and I loved it!")
        )
        print(response)

    asyncio.run(main())
