from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from core.configs import get_config
from .models import Author, Book


async def init_db():
    client = AsyncIOMotorClient(get_config().MONGODB_URL)

    await init_beanie(
        database=client[get_config().MONGODB_DATABASE],
        document_models=[Author, Book],
    )
