import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart

# === Настройки ===
TOKEN = os.getenv("BOT_TOKEN")  # <--- проверь, как называется переменная на Render

if not TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN в переменных окружения")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    text = (
        "Привет! Я бот «Высшая Траектория».\n\n"
        "Сейчас я в режиме MVP: главное — показать, что система жива ✅\n"
        "Чуть позже добавим полную диагностику управленческой зрелости и все твои практики."
    )
    await message.answer(text)


@dp.message()
async def echo(message: types.Message):
    # Временный обработчик: просто повторяем текст, чтобы видеть, что бот отвечает
    await message.answer(f"Ты написал(а): {message.text}")


async def main():
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
