from aiogram import Bot, Dispatcher

from .routers.comands import router


async def start(token: str):
    print("Bot is starting...")

    bot = Bot(token=token)

    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)
