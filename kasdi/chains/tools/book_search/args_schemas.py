from typing import Optional
from pydantic import BaseModel, Field

from .enums import GenreEnum, AgeRestrictionEnum


class SearchBooksByQueryArgs(BaseModel):
    query: str = Field(
        ...,
        description="The query to search for books in database."
    )
    limit: Optional[int] = Field(
        10,
        ge=1,
        description="Number of results to return (default is 10, try to set it not higher than 25).",
    )


class SearchBooksArgs(BaseModel):
    author_name : Optional[str] = Field(
        default=None,
        description="Author name filter (optional)."
    )

    title : Optional[str] = Field(
        default=None,
        description="Book title filter (optional)."
    )

    book_series : Optional[str] = Field(
        default=None,
        description="Book series filter (optional)."
    )

    publisher : Optional[str] = Field(
        default=None,
        description="Publisher filter (optional)."
    )

    genre : Optional[GenreEnum] = Field(
        default=GenreEnum.ALL,
        description="Genre filter (optional)."
    )

    age_restriction : Optional[AgeRestrictionEnum] = Field(
        default=AgeRestrictionEnum.ALL,
        description="Age rating, e.g., '14+' (optional)."
    )

    limit : Optional[int] = Field(
        default=10,
        ge=1,
        description="Number of results to return (default is 10, try to set it not higher than 25)."
    )

