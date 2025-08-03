import os
from dotenv import load_dotenv
from functools import lru_cache


load_dotenv()


class Config:
    """
    Configuration class for the KSD parser.
    """
    # MySQL database configuration
    MYSQL_DATABASE_URL: str = os.getenv("MYSQL_DATABASE_URL")

    # MongoDB configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DATABASE_KSD: str = os.getenv("MONGODB_DATABASE_KSD", "ksd")
    MONGODB_DATABASE_KASDI: str = os.getenv("MONGODB_DATABASE_KASDI", "kasdi")

    # Pinecone vector store configuration
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME")

    # OpenAI API key for embeddings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    EMBEDDINGS_MODEL: str = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")

    # Tavily API key for web search
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY")

    # FireCrawl API key for web crawling
    FIRE_CRAWL_API_KEY: str = os.getenv("FIRE_CRAWL_API_KEY")

    # LLM configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.5"))

    # Telegram Bot configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")

    # Application settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


@lru_cache(maxsize=1)
def get_config() -> Config:
    """
    Get the configuration instance.

    :return: Config instance with loaded environment variables.
    """
    return Config()
