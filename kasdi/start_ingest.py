from services.ingest import ingest_data
from dependencies import (
    initialize_dependencies,
    pinecone_manager,
    mysql_database_manager,
)

async def main():
    """
    Main function to run the ingestion process.
    """
    try:
        await initialize_dependencies()
        await ingest_data()

    except Exception as e:
        raise

    finally:
        await pinecone_manager.close()
        await mysql_database_manager.close_connection()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
