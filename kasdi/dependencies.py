from database.client import init_db
from core.configs import get_config

configs_obj = get_config()

async def initialize_dependencies():
    """
    Initialize all dependencies.
    """
    await init_db()
