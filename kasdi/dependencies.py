from database.client import init_db
from core.configs import get_config
from core.logger import create_scoped_logger

configs_obj = get_config()
logger = create_scoped_logger("kasdi.dependencies")


async def initialize_dependencies():
    """
    Initialize all dependencies.
    """
    logger.info("Initializing application dependencies")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize dependencies: {e}")
        raise
    finally:
        logger.debug("initialize_dependencies() finished")
