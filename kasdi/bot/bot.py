from aiogram import Bot, Dispatcher

from .routers.commands import router as commands_router
from .routers.profile import router as profile_router
from .routers.book    import router as book_router
from .routers.kasdi   import router as kasdi_router

from core.logger import create_scoped_logger

logger = create_scoped_logger("kasdi.bot")


async def start(token: str):
    logger.info("Starting Telegram bot")

    dp = Dispatcher()

    logger.debug("Including routers: commands, profile, book, kasdi")
    dp.include_router(commands_router)
    dp.include_router(profile_router)
    dp.include_router(book_router)
    dp.include_router(kasdi_router)

    try:
        logger.info("Starting polling loop")
        await dp.start_polling(Bot(token=token))
    except Exception as e:
        logger.error(f"Bot polling failed: {e}")
        raise
    finally:
        logger.info("Bot polling stopped")
