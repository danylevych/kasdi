import asyncio
from typing import Any, Type
from pydantic import PrivateAttr
from langchain_core.tools import BaseTool
from langchain_openai import OpenAIEmbeddings

from database.models.ksd import Book, Author

from .args_schemas import SearchBooksByQueryArgs
from .utils import book_formatter


class SearchBooksByQueryTool(BaseTool):
    name: str = "search_books_by_query"
    description: str = (
        "Use this tool to find books in the KSD bookstore database when the user provides a free-form "
        "description, partial information, or wants books similar in theme, story, or style. "
        "It searches across book titles, original titles, author names, and descriptions to match "
        "the meaning of the query, not just exact words.\n\n"
        "When to use:\n"
        "- The user describes the plot, theme, or feeling of the book (e.g., 'про магічну школу і друзів').\n"
        "- The user remembers only part of the title or author.\n"
        "- The user wants recommendations similar to a specific book.\n"
        "- The request is broad and doesn't fit strict filters.\n\n"
        "What NOT to do:\n"
        "- Do not call if the user gives exact structured filters (author + genre) — use 'search_books' instead.\n"
        "- Avoid using for unrelated requests or non-book searches.\n\n"
        "This tool is ideal for matching the idea or topic of a book, even if the exact name or author is unknown."
    )
    args_schema: Type[SearchBooksByQueryArgs] = SearchBooksByQueryArgs

    _embeddings: OpenAIEmbeddings = PrivateAttr()

    def __init__(self,
                 openai_api_key: str,
                 embedding_model: str = "text-embedding-3-small",
                 **kargs: Any
                ):
        super().__init__(**kargs)
        self._embeddings = OpenAIEmbeddings(
            model=embedding_model,
            api_key=openai_api_key,
        )

    def _run(
        self,
        query: str,
        limit: int = 10,
    ) -> str:
        """
        Run the search tool with the provided arguments.
        """
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
        books = [doc async for doc in cursor_vec]

        if not books:
            return "No books found matching the query."

        for book in books:
            author = await Author.find_one(Author.id == book["author_id"])
            if author:
                book["author"] = author.name

        response = "Books found:\n\n"
        for index, book in enumerate(books, start=1):
            response += f"#{index}\n{book_formatter(book)}\n\n---\n\n"

        return response.strip()
