import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web   # <-- маленький http-сервер

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN (переменная окружения).")

# PORT нужен именно для Render Web Service
PORT = int(os.getenv("PORT", "10000"))

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


# ---------- мини-веб-сервер для Render ----------

async def handle_root(request: web.Request) -> web.Response:
    return web.Response(text="Vysshaya Traektoria bot is running")


async def start_web_app():
    app = web.Application()
    app.router.add_get("/", handle_root)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()

    logging.info(f"HTTP server started on port {PORT}")


async def main():
    logging.info("Запуск бота и HTTP-сервера…")
    # 1) запускаем веб-сервер (порт для Render)
    await start_web_app()
    # 2) запускаем long polling бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
