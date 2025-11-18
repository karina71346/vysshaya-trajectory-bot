import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN (переменная окружения).")

bot = Bot(TOKEN)          # БЕЗ parse_mode
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Привет! Бот «Высшая траектория» на связи 🚀")


@dp.message(Command("ping"))
async def cmd_ping(message: types.Message):
    await message.answer("pong")


@dp.message()
async def echo_any(message: types.Message):
    # Чтобы точно видеть, что бот жив — будет повторять любое сообщение
    await message.answer(f"Ты написал(а): {message.text}")


async def main():
    logging.info("Бот запущен и начинает polling…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
