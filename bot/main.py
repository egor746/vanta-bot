import asyncio
import logging
from aiogram import Bot, Dispatcher

from bot.config import load_settings
from bot.db import Database
from bot.handlers import common, orders, profile


async def main():
    settings = load_settings()
    db = Database()
    await db.init()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    dp.include_router(common.router)
    dp.include_router(orders.router)
    dp.include_router(profile.router)

    await dp.start_polling(bot, db=db, group_chat_id=settings.group_chat_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
