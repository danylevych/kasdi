from dependencies import (
    initialize_dependencies
)

from core.configs import get_config

from bot.bot import start

from core.logger import create_scoped_logger

logger = create_scoped_logger("kasdi.start_bot")

async def main():
    logger.info("Starting bot application: initializing dependencies")
    await initialize_dependencies()
    config = get_config()
    logger.info("Dependencies initialized; launching bot")
    await start(token=config.TELEGRAM_BOT_TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
