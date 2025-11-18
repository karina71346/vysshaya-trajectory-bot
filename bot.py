import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN (переменная окружения).")

bot = Bot(TOKEN)   # без parse_mode, шлём простой текст
dp = Dispatcher()


def notebook_inline_kb() -> InlineKeyboardMarkup:
    """
    Кнопка с переходом на интерактивную тетрадь лидера.
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔷 Открыть тетрадь лидера",
                    url="https://tetrad-lidera.netlify.app/"
                )
            ]
        ]
    )
    return kb


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    text = (
        "Привет! Бот «Высшая траектория» на связи 🚀\n\n"
        "Я помогу тебе перейти в интерактивную «Тетрадь лидера по делегированию».\n"
        "Нажми кнопку ниже, чтобы открыть тетрадь в браузере."
    )
    await message.answer(text, reply_markup=notebook_inline_kb())


@dp.message(Command("notebook"))
async def cmd_notebook(message: types.Message):
    """
    Дополнительная команда /notebook — тоже открывает тетрадь.
    """
    text = (
        "📘 Тетрадь лидера по делегированию.\n\n"
        "Откроется в браузере, там можно заполнять онлайн и сохранять отчёт."
    )
    await message.answer(text, reply_markup=notebook_inline_kb())


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
