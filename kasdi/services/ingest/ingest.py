from aiohttp_retry import List
from dependencies import (
    pinecone_manager,
    initialize_dependencies,
)

from databases.models.ksd import Book, Author


from core.logger import create_scoped_logger


logger = create_scoped_logger("IngestManager")


async def ingest_data():
    """
    Ingest data into the application.
    """
    logger.info("Ingesting data...")

    try:

        books: List[Book] = await Book.find_all().to_list()

        if not books:
            logger.warning("No books found in the database")
            return

        logger.info(f"Retrieved {len(books)} books from MongoDB")

        texts = []
        metadatas = []
        ids = []

        for book in books:
            author = await Author.find_one(Author.id == book.author_id)
            book_text = create_book_text(book, author)
            texts.append(book_text)
            metadata = book.model_dump()
            metadata["source"] = "mongodb_ksd_books"
            metadatas.append(metadata)
            ids.append(f"book_{book.id}")

        logger.info("Adding documents to Pinecone...")
        document_ids = await pinecone_manager.add_documents(
            texts=texts,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"Successfully added {len(document_ids)} documents to Pinecone")
        logger.info(f"Document IDs: {document_ids}")

    except Exception as e:
        logger.error(f"Error during data ingestion: {e}")
        raise


def create_book_text(book: Book, author: Author) -> str:
    """
    Create a comprehensive text representation of a book for embedding.

    Args:
        book: KSDBook instance
        author: KSDAuthor instance

    Returns:
        Formatted text representation
    """
    text_parts = []

    # Title and author (most important)
    text_parts.append(f"Title: {book.title}")
    text_parts.append(f"Author: {author.name}")

    # Description if available
    if book.description:
        text_parts.append(f"Description: {book.description}")

    # Publication details
    if book.publisher:
        text_parts.append(f"Publisher: {book.publisher}")

    if book.publish_year:
        text_parts.append(f"Published: {book.publish_year}")

    # Genre and series
    if book.genre:  # Note: your model has 'ganre' instead of 'genre'
        text_parts.append(f"Genre: {book.genre}")

    if book.series:
        text_parts.append(f"Series: {book.series}")

    # Language information
    if book.language:
        text_parts.append(f"Language: {book.language}")

    if book.original_language and book.original_language != book.language:
        text_parts.append(f"Original Language: {book.original_language}")

    if book.original_name and book.original_name != book.title:
        text_parts.append(f"Original Title: {book.original_name}")

    # Physical details
    if book.number_of_pages:
        text_parts.append(f"Pages: {book.number_of_pages}")

    if book.cover_type:
        text_parts.append(f"Cover: {book.cover_type}")

    if book.format:
        text_parts.append(f"Format: {book.format}")

    # Additional metadata
    if book.translators:
        text_parts.append(f"Translators: {book.translators}")

    if book.isbn:
        text_parts.append(f"ISBN: {book.isbn}")

    if book.price:
        text_parts.append(f"Price: {book.price}")

    # Join all parts with newlines
    return "\n".join(text_parts)

