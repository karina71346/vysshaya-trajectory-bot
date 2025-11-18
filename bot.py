import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiohttp import web  # мини HTTP-сервер для Render

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN (переменная окружения).")

# PORT нужен именно для Render Web Service
PORT = int(os.getenv("PORT", "10000"))

bot = Bot(TOKEN)   # без parse_mode, шлём простой текст
dp = Dispatcher()

# простейшее «состояние» пользователей в памяти
user_states: dict[int, str] = {}   # user_id -> "await_consent" / "await_name" / "done"


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


def consent_kb() -> InlineKeyboardMarkup:
    """
    Кнопки согласия на обработку персональных данных.
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, согласен",
                    callback_data="consent_yes",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Нет, не сейчас",
                    callback_data="consent_no",
                )
            ],
        ]
    )
    return kb


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """
    Первый шаг: текст о персональных данных + запрос согласия.
    """
    user_id = message.from_user.id
    user_states[user_id] = "await_consent"

    text = (
        "Привет! Бот «Высшая траектория» на связи 🚀\n\n"
        "Перед тем как выдать тебе интерактивную «Тетрадь лидера по делегированию»,\n"
        "мне важно получить согласие на обработку персональных данных.\n\n"
        "🔐 Какие данные могут обрабатываться:\n"
        "— имя и ник в Telegram;\n"
        "— контакт для связи, если ты его укажешь;\n"
        "— ответы в тетрадях и чек-листах (в обобщённом виде для аналитики).\n\n"
        "Цель обработки данных: предоставить материалы проекта «Высшая траектория»,\n"
        "обратную связь по результатам и приглашения на обучающие мероприятия.\n\n"
        "Ты можешь в любой момент отказаться, написав здесь «стоп».\n\n"
        "Если тебе это ок — нажми «Да, согласен» 👇"
    )

    await message.answer(text, reply_markup=consent_kb())


@dp.callback_query(F.data == "consent_yes")
async def consent_yes(callback: CallbackQuery):
    """
    Пользователь дал согласие — просим имя и роль.
    """
    user_id = callback.from_user.id
    user_states[user_id] = "await_name"

    # убираем кнопки под прошлым сообщением
    try:
        await callback.message.edit_reply_markup()
    except Exception:
        pass

    await callback.answer()
    await callback.message.answer(
        "Отлично, спасибо за доверие 🌿\n\n"
        "Напиши, пожалуйста, в одном сообщении:\n"
        "— как к тебе обращаться;\n"
        "— и какую роль ты сейчас играешь в бизнесе.\n\n"
        "Например: «Карина, собственник образовательного проекта»."
    )


@dp.callback_query(F.data == "consent_no")
async def consent_no(callback: CallbackQuery):
    """
    Пользователь не дал согласие — ничего не сохраняем и не выдаём тетрадь.
    """
    user_id = callback.from_user.id
    user_states[user_id] = "no_consent"

    try:
        await callback.message.edit_reply_markup()
    except Exception:
        pass

    await callback.answer()
    await callback.message.answer(
        "Понимаю, спасибо за честность.\n\n"
        "Я не буду сохранять и обрабатывать твои данные и не выдам тетрадь.\n"
        "Если захочешь вернуться к материалам — просто напиши /start."
    )


@dp.message(Command("notebook"))
async def cmd_notebook(message: types.Message):
    """
    Команда /notebook: выдаём тетрадь только тем, кто прошёл согласие.
    """
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if state != "done":
        await message.answer(
            "Чтобы выдать тебе тетрадь лидера, мне нужно согласие на обработку данных.\n"
            "Напиши, пожалуйста, /start и пройди короткий шаг согласия."
        )
        return

    text = (
        "📘 Тетрадь лидера по делегированию.\n\n"
        "Откроется в браузере: можно заполнять онлайн и сохранять отчёт."
    )
    await message.answer(text, reply_markup=notebook_inline_kb())


@dp.message(Command("ping"))
async def cmd_ping(message: types.Message):
    await message.answer("pong")


@dp.message()
async def handle_any_message(message: types.Message):
    """
    Обработка всех остальных сообщений:
    — если ждём имя/роль — сохраняем и выдаём тетрадь;
    — если обычный режим — просто эхо.
    """
    user_id = message.from_user.id
    state = user_states.get(user_id)

    # пользователь в шаге ввода имени и роли
    if state == "await_name":
        user_states[user_id] = "done"

        # логируем в консоль (потом можно подключить БД)
        logging.info(f"Новый лидер: {user_id} -> {message.text!r}")

        text = (
            "Спасибо! Сохранила:\n"
            f"{message.text}\n\n"
            "Теперь держи твою интерактивную «Тетрадь лидера по делегированию».\n"
            "Заполняй онлайн и забирай отчёт в PDF или Word."
        )
        await message.answer(text, reply_markup=notebook_inline_kb())
        return

    # команда «стоп» — условный отзыв согласия
    if message.text and message.text.strip().lower() in ("стоп", "stop"):
        user_states[user_id] = "no_consent"
        await message.answer(
            "Хорошо, я остановлю взаимодействие и не буду дальше обрабатывать данные.\n"
            "Если передумаешь — всегда можно начать заново через /start."
        )
        return

    # обычный режим: простое эхо, чтобы видеть, что бот жив
    await message.answer(f"Ты написал(а): {message.text}")


# ---------- мини-веб-сервер для Render (порт для Web Service) ----------

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
