import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.handlers.commands import router as commands_router
from bot.handlers.expense import router as expense_router


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(commands_router)
    dp.include_router(expense_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
