import asyncio
from typing import List, Optional, Type
from langchain_core.tools import BaseTool

from database.models.ksd import Book, Author

from .args_schemas import SearchBooksArgs
from .enums import GenreEnum, AgeRestrictionEnum
from .utils import book_formatter


class SearchBooksTool(BaseTool):
    name: str = "search_books"
    description: str = (
        "Use this tool to search for books in the KSD bookstore database by applying one or more filters. "
        "Call this tool when the user wants book recommendations, is searching for a specific title, "
        "series, author, or wants books within certain genres, publishers, or age restrictions.\n\n"
        "When to use:\n"
        "- The user names a book title, series, or author they are looking for.\n"
        "- The user asks for books in a specific genre or with a specific age rating.\n"
        "- The user wants books from a certain publisher.\n"
        "- The user gives partial info (e.g., 'fantasy books for teens').\n\n"
        "What NOT to do:\n"
        "- Do not call if the request is unrelated to books.\n"
        "- Do not guess parameters — if unsure, pass only what the user mentioned.\n"
        "- Avoid over-filtering unless the user explicitly sets multiple criteria.\n\n"
        "If multiple filters are provided, the search will match all of them. "
        "Always prefer concise and relevant filters to get the most accurate results."
    )

    args_schema: Type[SearchBooksArgs] = SearchBooksArgs


    async def find(
        self,
        author_name: Optional[str] = None,
        title: Optional[str] = None,
        book_series: Optional[str] = None,
        publisher: Optional[str] = None,
        genre: Optional[GenreEnum] = GenreEnum.ALL,
        age_restriction: Optional[AgeRestrictionEnum] = AgeRestrictionEnum.ALL,
        limit: int = 10,
    ) -> List[Book]:
        author_ids = []

        if author_name:
            authors = await self._search_authors(author_name)
            if not authors:
                return "No authors found matching the query."

            author_ids = [author.id for author in authors]

        # Search books by title and other filters
        books = await self._search_books_by_title(
            author_ids=author_ids,
            title=title,
            publisher=publisher,
            genre=genre,
            age_restriction=age_restriction,
            book_series=book_series,
            limit=limit,
        )

        return books

    async def _arun(
        self,
        author_name: Optional[str] = None,
        title: Optional[str] = None,
        book_series: Optional[str] = None,
        publisher: Optional[str] = None,
        genre: Optional[GenreEnum] = GenreEnum.ALL,
        age_restriction: Optional[AgeRestrictionEnum] = AgeRestrictionEnum.ALL,
        limit: int = 10,
    ) -> str:
        """
        Search books in the database with the provided filters.
        """
        # Run the search for authors
        books = await self.find(
            author_name=author_name,
            title=title,
            book_series=book_series,
            publisher=publisher,
            genre=genre,
            age_restriction=age_restriction,
            limit=limit,
        )

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

    def _run(
        self,
        author_name: Optional[str] = None,
        title: Optional[str] = None,
        book_series: Optional[str] = None,
        publisher: Optional[str] = None,
        genre: Optional[GenreEnum] = GenreEnum.ALL,
        age_restriction: Optional[AgeRestrictionEnum] = AgeRestrictionEnum.ALL,
        limit: int = 10,
    ) -> str:
        """
        Run the search tool with the provided arguments.
        """
        return asyncio.run(self._arun(
            author_name=author_name,
            title=title,
            book_series=book_series,
            publisher=publisher,
            genre=genre,
            age_restriction=age_restriction,
            limit=limit,
        ))


    async def _search_authors(self, author_name: str) -> List[Author]:
        pipeline = [
            {
                "$search": {
                    "index": "default",
                    "autocomplete": {
                        "query": author_name,
                        "path": "name",
                        "fuzzy": {
                            "maxEdits": 2,
                            "prefixLength": 1
                        }
                    }
                }
            },
            {"$limit": 5}
        ]

        collection = Author.get_pymongo_collection()
        cursor = collection.aggregate(pipeline)
        return [Author(**doc) async for doc in cursor]

    async def _search_books_by_title(
            self,
            author_ids: List[str],
            title: Optional[str] = None,
            book_series: Optional[str] = None,
            publisher: Optional[str] = None,
            genre: Optional[GenreEnum] = GenreEnum.ALL,
            age_restriction: Optional[AgeRestrictionEnum] = AgeRestrictionEnum.ALL,
            limit: int = 10
        ) -> List[Book]:
        """
        Search books by title with optional genre and age restriction filters.
        """
        pipeline = []

        if title or book_series:
            autocomplete = []

            if title:
                autocomplete.append({
                    "autocomplete": {
                        "query": title,
                        "path": "title",
                        "fuzzy": {
                            "maxEdits": 2,
                            "prefixLength": 1
                        }
                    }
                })

            if book_series:
                autocomplete.append({
                    "autocomplete": {
                        "query": book_series,
                        "path": "series",
                        "fuzzy": {
                            "maxEdits": 2,
                            "prefixLength": 1
                        }
                    }
                })

            if len(autocomplete) > 1:
                pipeline.append(
                    {
                        "$search": {
                            "index": "book_def",
                            "compound": {
                                "should": autocomplete
                            }
                        }
                    }
                )

            elif autocomplete:
                pipeline.append(
                    {
                        "$search": {
                            "index": "book_def",
                            **autocomplete[0]
                        }
                    }
                )

        match_conditions = {}

        if author_ids:
            match_conditions = {"author_id": {"$in": author_ids}}

        if publisher:
            match_conditions["publisher"] = publisher

        if genre != GenreEnum.ALL:
            match_conditions["genre"] = genre

        if age_restriction != AgeRestrictionEnum.ALL:
            match_conditions["age_restriction"] = age_restriction

        pipeline.extend([
            {
                "$match": match_conditions
            },
            {
                "$limit": limit
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
            }
        ])

        collection = Book.get_pymongo_collection()
        cursor = collection.aggregate(pipeline)
        return [doc async for doc in cursor]
