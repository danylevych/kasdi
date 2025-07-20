from dependencies import (
    pinecone_manager,
    mysql_database_manager,
    initialize_dependencies,
)

from databases.relation_db.models.book import KSDBook
from sqlalchemy import select

from core.logger import create_scoped_logger


logger = create_scoped_logger("IngestManager")


async def ingest_data():
    """
    Ingest data into the application.
    """
    logger.info("Ingesting data...")

    try:
        async with mysql_database_manager.session as session:
            stmt = select(KSDBook).limit(15) # TODO: ITS A TEMPORARY LIMIT
            result = await session.execute(stmt)
            books = result.scalars().all()

            if not books:
                logger.warning("No books found in the database")
                return

            logger.info(f"Retrieved {len(books)} books from MySQL")

            texts = []
            metadatas = []
            ids = []

            for book in books:
                book_text = create_book_text(book)
                texts.append(book_text)
                metadata = book.to_dict()
                metadata["source"] = "mysql_ksd_books"
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


def create_book_text(book: KSDBook) -> str:
    """
    Create a comprehensive text representation of a book for embedding.

    Args:
        book: KSDBook instance

    Returns:
        Formatted text representation
    """
    text_parts = []

    # Title and author (most important)
    text_parts.append(f"Title: {book.book_title}")
    text_parts.append(f"Author: {book.author_name}")

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

    if book.original_name and book.original_name != book.book_title:
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

