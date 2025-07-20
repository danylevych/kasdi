from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func

from ..database_manager import Base


class KSDBook(Base):
    __tablename__ = 'ksd_books'

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(500), nullable=False, unique=True)

    book_title = Column(String(500), nullable=False)
    author_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    language = Column(String(50), nullable=True)
    original_language = Column(String(50), nullable=True)
    original_name = Column(String(500), nullable=True)

    cover_type = Column(String(100), nullable=True)
    number_of_pages = Column(Integer, nullable=True)

    publisher = Column(String(255), nullable=True)
    publish_year = Column(Integer, nullable=True)

    genre = Column("ganre", String(255), nullable=True)
    series = Column(String(255), nullable=True)

    format = Column(String(100), nullable=True)
    weight_in_grams = Column("weigth_in_grams", Float, nullable=True)

    isbn = Column(String(500), nullable=True) # ISBN can be multiple, so we use a string to store them
    count_in_complect = Column(Integer, nullable=True)
    age_restriction = Column(String(50), nullable=True)
    price = Column(Float, nullable=True)
    translators = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=func.now())

    def to_dict(self) -> dict:
        fields = [
            "id", "url", "book_title", "author_name", "description",
            "language", "original_language", "original_name", "cover_type",
            "number_of_pages", "publisher", "publish_year", "genre", "series",
            "format", "weight_in_grams", "isbn", "count_in_complect",
            "age_restriction", "price"
        ]

        dict_obj = {}

        for field in fields:
            value = getattr(self, field, None)
            if value is not None:
                dict_obj[field] = value

        return dict_obj
