from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base

from core.logger import create_scoped_logger


logger = create_scoped_logger("DatabaseManager")

Base = declarative_base()


class DatabaseManager:
    def __init__(self, conection_string: str):
        self.conection_string = conection_string
        self.engine = None
        self.Session = None

    async def connect(self):
        try:
            self.engine = create_async_engine(
                self.conection_string,
                echo=False,
            )

            import databases.relation_db.models  # Ensure models are imported to create tables

            self.Session = async_sessionmaker(bind=self.engine)
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Connected to Database successfully")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Database: {e}")
            return False

    async def close_connection(self):
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")

    @property
    def session(self):
        if not self.Session:
            logger.error("Database session is not initialized. Call connect() first.")
            raise Exception("Database session is not initialized. Call connect() first.")
        return self.Session()
