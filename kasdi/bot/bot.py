from aiogram import Bot, Dispatcher

from .routers.comands import router as commands_router
from .routers.profile import router as profile_router
from .routers.book    import router as book_router
from .routers.kasdi   import router as kasdi_router

async def start(token: str):
    print("Bot is starting...")

    dp = Dispatcher()

    dp.include_router(commands_router)
    dp.include_router(profile_router)
    dp.include_router(book_router)
    dp.include_router(kasdi_router)

    await dp.start_polling(Bot(token=token))
