import asyncio

from aiogram import Bot, Dispatcher

from bot.handlers import routers
from config import load_settings


async def main() -> None:
    settings = load_settings()
    bot = Bot(token=settings.tg_key)
    dispatcher = Dispatcher()
    for router in routers:
        dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
