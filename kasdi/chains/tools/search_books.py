from typing import Any, Dict, List, Optional, Type
import asyncio

from pydantic import BaseModel, Field, PrivateAttr
from langchain_core.tools import BaseTool
from langchain_openai import OpenAIEmbeddings

from databases.models.ksd import Book, Author
from core.configs import get_config


def _format_book(data: Dict[str, Any]) -> str:
    """
    Format a book document for output.
    """
    def remove_to_many_newlines(text: str) -> Any:
        if not isinstance(text, str):
            return text
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())

    book_formated = ""

    for key, value in data.items():
        if value:
            book_formated += f"{key.capitalize().replace('_', ' ')}: {remove_to_many_newlines(value)}\n"

    return book_formated.strip()



class SearchBooksByQueryArgs(BaseModel):
    query: Optional[str] = Field(
        None,
        description="Search string .",
    )
    limit: Optional[int] = Field(
        10,
        ge=1,
        description="Number of results to return (default is 10, try to set it not higher than 25).",
    )


class SearchBooksByQueryTool(BaseTool):
    name: str = "search_books_by_query"
    description: str = "Provide the similiraty search over books in database."
    args_schema: Type[SearchBooksByQueryArgs] = SearchBooksByQueryArgs

    _embeddings: OpenAIEmbeddings = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        cfg = get_config()
        self._embeddings = OpenAIEmbeddings(
            model=cfg.EMBEDDINGS_MODEL,
            api_key=cfg.OPENAI_API_KEY,
        )

    def _run(
        self,
        query: str,
        limit: int = 10,
    ) -> str:
        """
        Run the search tool with the provided arguments.
        """
        import asyncio
        return asyncio.run(self._arun(
            query=query,
            limit=limit,
        ))

    async def _arun(
        self,
        query: str,
        limit: int = 10,
    ) -> str:
        """
        Search over books using both vector and full-text search.
        """
        query_vec = await asyncio.to_thread(self._embeddings.embed_query, query)

        collection = Book.get_pymongo_collection()

        vector_pipeline = [
            {
                "$vectorSearch": {
                    "index": "book_vec",
                    "path": "embedding",
                    "queryVector": query_vec,
                    "numCandidates": 100,
                    "limit": limit,
                }
            },
            {
                "$set": {
                    "similarity_score": {
                        "$meta": "vectorSearchScore"
                    },
                },
            },
            {
                "$project": {
                    "embedding": 0,
                    "search_text": 0,
                    "tags": 0,
                    "format": 0,
                    "cover_type": 0,
                    "created_at": 0,
                    "weight_in_grams": 0,
                }
            },
        ]

        cursor_vec = collection.aggregate(vector_pipeline)
        docs = [doc async for doc in cursor_vec]

        if not docs:
            return "No books found matching the query."

        for doc in docs:
            author = await Author.find_one(Author.id == doc["author_id"])
            if author:
                doc["author"] = author.name

        response = "Books found:\n\n"
        for index, doc in enumerate(docs, start=1):
            response += f"#{index}\n{_format_book(doc)}\n\n---\n\n"

        return response.strip()


# TODO: Make the SearchBooksTool

class SearchBooksArgs(BaseModel):
    publisher: Optional[str] = Field(None, description="Publisher filter (optional).")
    genre: Optional[str] = Field(None, description="Genre filter (optional).")
    age_restriction: Optional[str] = Field(None, description="Age rating, e.g., '12+' (optional).")
    min_price: Optional[float] = Field(None, ge=0, description="Min price (optional).")
    max_price: Optional[float] = Field(None, ge=0, description="Max price (optional).")
    min_number_of_pages: Optional[int] = Field(None, ge=1, description="Min pages (optional).")
    max_number_of_pages: Optional[int] = Field(None, ge=1, description="Max pages (optional).")


class SearchBooksTool(BaseTool):
    name: str = "search_books"
    description: str = "Search books in the database with various filters."
    args_schema: Type[SearchBooksArgs] = SearchBooksArgs

    async def _arun(
        self,
        publisher: Optional[str] = None,
        genre: Optional[str] = None,
        age_restriction: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_number_of_pages: Optional[int] = None,
        max_number_of_pages: Optional[int] = None,
    ) -> str:
        """
        Search books in the database with the provided filters.
        """
        mongo_query = {}
        # Build MongoDB query based on provided filters
        if publisher:
            mongo_query["publisher"] = publisher

        if genre:
            mongo_query["genre"] = genre

        if age_restriction:
            mongo_query["age_restriction"] = age_restriction

        if min_price is not None or max_price is not None:
            price_filter = {}
            if min_price is not None:
                price_filter["$gte"] = min_price

            if max_price is not None:
                price_filter["$lte"] = max_price

            mongo_query["price"] = price_filter

        if min_number_of_pages is not None or max_number_of_pages is not None:
            pages_filter = {}

            if min_number_of_pages is not None:
                pages_filter["$gte"] = min_number_of_pages

            if max_number_of_pages is not None:
                pages_filter["$lte"] = max_number_of_pages

            mongo_query["number_of_pages"] = pages_filter

        collection = Book.get_pymongo_collection()
        cursor = collection.find(mongo_query)
        docs = [doc async for doc in cursor]

        if not docs:
            return "No books found matching the filters."

        for doc in docs:
            author = await Author.find_one(Author.id == doc["author_id"])
            if author:
                doc["author"] = author.name

        response = "Books found:\n\n"
        for index, doc in enumerate(docs, start=1):
            response += f"#{index}\n{_format_book(doc)}\n\n---\n\n"

        return response.strip()







if __name__ == "__main__":
    tool = SearchBooksByQueryTool()
    args = SearchBooksByQueryArgs(query="Вайолет і її дракон терн")

    import asyncio
    from dependencies import initialize_dependencies

    async def main():
        await initialize_dependencies()
        out = await tool._arun(**args.model_dump())
        import pprint
        pprint.pprint(out)

    asyncio.run(main())
