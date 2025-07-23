from dependencies import (
    initialize_dependencies
)

from core.configs import get_config

from bot.bot import start

async def main():
    await initialize_dependencies()
    config = get_config()
    await start(token=config.BOT_TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
