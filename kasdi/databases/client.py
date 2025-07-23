from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from core.configs import get_config
from .models.ksd import Author, Book
from .models.kasdi import Chat, ReadedBook, User

from core.logger import create_scoped_logger

logger = create_scoped_logger("kasdi.databases.client")


async def init_db():
    logger.info("Initializing Beanie with MongoDB...")

    client = AsyncIOMotorClient(get_config().MONGODB_URL)

    logger.info("Initializing Beanie for KSD database...")
    await init_beanie(
        database=client[get_config().MONGODB_DATABASE_KSD],
        document_models=[Author, Book],
    )
    logger.info("Initializing Beanie for KASDI database...")

    logger.info("Connecting to KASDI database...")
    await init_beanie(
        database=client[get_config().MONGODB_DATABASE_KASDI],
        document_models=[Chat, ReadedBook, User],
    )
    logger.info("Beanie initialization complete.")
