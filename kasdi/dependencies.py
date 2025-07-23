from databases.client import init_db
from services.vector_store import AsyncPineconeManagerFactory

from core.configs import get_config

configs_obj = get_config()


from langchain_openai import OpenAIEmbeddings

pinecone_manager = AsyncPineconeManagerFactory.create_manager(
    embeddings=OpenAIEmbeddings(),
    api_key=configs_obj.PINECONE_API_KEY,
    index_name=configs_obj.PINECONE_INDEX_NAME
)


async def initialize_dependencies():
    """
    Initialize all dependencies.
    """
    await init_db()
    await pinecone_manager.connect()
