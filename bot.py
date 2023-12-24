import asyncio
import logging
from aiogram import Bot, Dispatcher, types
import handler


logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot("")
    dp = Dispatcher()
    dp.include_router(handler.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
