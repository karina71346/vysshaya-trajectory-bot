import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiohttp import web  # мини HTTP-сервер для Render

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN (переменная окружения).")

# PORT нужен для Render Web Service
PORT = int(os.getenv("PORT", "10000"))

bot = Bot(TOKEN)   # без parse_mode
dp = Dispatcher()

# состояния: user_id -> str
# "await_consent" / "await_name" / "await_phone" / "await_email" / "await_channel" / "ready" / "no_consent"
user_states: dict[int, str] = {}
user_profiles: dict[int, dict] = {}   # имя, телефон, почта

CHANNEL_USERNAME = "@businesskodrosta"  # канал для проверки подписки


def notebook_inline_kb() -> InlineKeyboardMarkup:
    """Кнопка с переходом на интерактивную тетрадь лидера."""
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
    """Кнопки ПДн + согласие/отказ."""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Политика конфиденциальности",
                    url="https://github.com/karina71346/vysshaya-trajectory-bot/raw/main/politika_konfidencialnosti.pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📄 Согласие на обработку ПДн",
                    url="https://github.com/karina71346/vysshaya-trajectory-bot/raw/main/soglasie_na_obrabotku_pd.pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Далее",
                    callback_data="consent_yes",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Не согласен",
                    callback_data="consent_no",
                )
            ],
        ]
    )
    return kb


def contact_phone_kb() -> ReplyKeyboardMarkup:
    """Клавиатура для отправки контакта."""
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    kb.add(
        KeyboardButton(
            text="📲 Отправить мой номер",
            request_contact=True,
        )
    )
    return kb


def channel_kb() -> InlineKeyboardMarkup:
    """Кнопки для перехода в канал и проверки подписки."""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 Открыть канал",
                    url="https://t.me/businesskodrosta",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Я вступил(а) в канал",
                    callback_data="check_channel",
                )
            ],
        ]
    )
    return kb


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Шаг 1: приветствие + ПДн + кнопка «Далее»."""
    user_id = message.from_user.id
    user_states[user_id] = "await_consent"

    text = (
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.\n\n"
        "Перед тем как получить интерактивную тетрадь лидера, нужно совсем чуть-чуть формальностей:\n"
        "🔹 Подтвердите, что вы согласны на обработку персональных данных (обязательное требование).\n"
        "🔹 После этого мы продолжим.\n\n"
        "Если нужно, вы можете открыть и сохранить документы:\n"
        "— Политика конфиденциальности\n"
        "— Согласие на обработку персональных данных\n\n"
        "🛡️ Нажимая кнопку «Далее», вы даёте согласие на обработку персональных данных\n"
        "и принимаете условия Политики конфиденциальности."
    )

    await message.answer(text, reply_markup=consent_kb())


@dp.callback_query(F.data == "consent_yes")
async def consent_yes(callback: CallbackQuery):
    """Пользователь дал согласие — Шаг 2: имя."""
    user_id = callback.from_user.id
    user_states[user_id] = "await_name"

    try:
        await callback.message.edit_reply_markup()
    except Exception:
        pass

    await callback.answer()
    await callback.message.answer(
        "Отлично!\n"
        "Давайте начнём знакомство.\n\n"
        "Напишите, как к вам обращаться — имя или ФИ."
    )


@dp.callback_query(F.data == "consent_no")
async def consent_no(callback: CallbackQuery):
    """Нет согласия — стоп."""
    user_id = callback.from_user.id
    user_states[user_id] = "no_consent"

    try:
        await callback.message.edit_reply_markup()
    except Exception:
        pass

    await callback.answer()
    await callback.message.answer(
        "Понимаю, спасибо за честность.\n\n"
        "Я не буду сохранять и обрабатывать ваши данные и не выдам тетрадь.\n"
        "Если захотите вернуться к материалам — напишите /start."
    )


@dp.message(Command("notebook"))
async def cmd_notebook(message: types.Message):
    """/notebook — выдаём только тем, кто прошёл все шаги."""
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if state != "ready":
        await message.answer(
            "Чтобы получить тетрадь лидера, нужно пройти короткий путь согласия, "
            "знакомства и подписки на канал.\n"
            "Напишите /start, чтобы начать сначала."
        )
        return

    await send_notebook(message.chat.id)


async def send_notebook(chat_id: int):
    """Сообщение с кнопкой тетради."""
    text = (
        "📘 Тетрадь лидера по делегированию.\n\n"
        "Откроется в браузере: можно заполнять онлайн и сохранять отчёт."
    )
    await bot.send_message(chat_id, text, reply_markup=notebook_inline_kb())


@dp.message()
async def handle_any_message(message: types.Message):
    """Диалог: имя -> телефон -> почта -> канал."""
    user_id = message.from_user.id
    state = user_states.get(user_id)

    # Шаг 2: имя
    if state == "await_name":
        profile = user_profiles.get(user_id, {})
        profile["name"] = (message.text or "").strip()
        user_profiles[user_id] = profile

        logging.info(f"Имя/ФИО лидера: {user_id} -> {message.text!r}")

        user_states[user_id] = "await_phone"

        await message.answer(
            "Спасибо!\n\n"
            "Теперь напишите, пожалуйста, ваш телефон.\n"
            "Можно нажать кнопку «📲 Отправить мой номер»\n"
            "или просто отправить номер в ответ на это сообщение.",
            reply_markup=contact_phone_kb()
        )
        return

    # Шаг 3: телефон
    if state == "await_phone":
        profile = user_profiles.get(user_id, {})

        phone = None
        if message.contact and message.contact.phone_number:
            phone = message.contact.phone_number
        elif message.text:
            phone = message.text.strip()

        if not phone:
            await message.answer(
                "Похоже, я не увидел номер телефона.\n"
                "Пожалуйста, отправьте его ещё раз или используйте кнопку «📲 Отправить мой номер»."
            )
            return

        profile["phone"] = phone
        user_profiles[user_id] = profile

        logging.info(f"Телефон лидера: {user_id} -> {phone!r}")

        user_states[user_id] = "await_email"

        await message.answer(
            "Отлично!\n\n"
            "Теперь напишите свою почту в ответ на это сообщение.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Шаг 4: почта
    if state == "await_email":
        profile = user_profiles.get(user_id, {})
        email = (message.text or "").strip()
        profile["email"] = email
        user_profiles[user_id] = profile

        logging.info(f"Email лидера: {user_id} -> {email!r}")

        user_states[user_id] = "await_channel"

        await message.answer(
            "Благодарю! Теперь мы с вами на связи 🤝\n\n"
            "Совсем скоро вы сможете узнать уровень своего лидерства через делегирование.\n\n"
            "Что дальше:\n"
            "— вступите в канал проекта «Бизнес со смыслом»:\n"
            "https://t.me/businesskodrosta\n\n"
            "После вступления вернитесь сюда и нажмите «Я вступил(а) в канал».",
            reply_markup=channel_kb()
        )
        return

    # Стоп-слово
    if message.text and message.text.strip().lower() in ("стоп", "stop"):
        user_states[user_id] = "no_consent"
        await message.answer(
            "Хорошо, я остановлю взаимодействие и не буду дальше обрабатывать данные.\n"
            "Если передумаете — всегда можно начать заново через /start."
        )
        return

    # Остальное — простое эхо (чтобы бот не молчал вовсе)
    if message.text:
        await message.answer(f"Ты написал(а): {message.text}")


@dp.callback_query(F.data == "check_channel")
async def check_channel(callback: CallbackQuery):
    """Проверяем, вступил ли пользователь в канал."""
    user_id = callback.from_user.id
    state = user_states.get(user_id)

    if state != "await_channel":
        await callback.answer("Сначала пройдите шаги знакомства.", show_alert=True)
        return

    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        status = member.status
    except Exception as e:
        logging.warning(f"Не удалось проверить подписку на канал: {e}")
        await callback.answer(
            "Я пока не могу проверить подписку. Попробуйте ещё раз чуть позже.",
            show_alert=True
        )
        return

    if status in ("member", "administrator", "creator"):
        user_states[user_id] = "ready"

        await callback.answer()
        await callback.message.answer(
            "Отлично! Я вижу, что вы в канале «Бизнес со смыслом» 🌟\n\n"
            "Рада видеть вас в пространстве «Высшая Траектория».\n"
            "Теперь можно переходить к тетради лидера."
        )

        await send_notebook(callback.message.chat.id)
    else:
        await callback.answer()
        await callback.message.answer(
            "Увы, я пока не вижу вас среди участников канала.\n\n"
            "Мы вас очень ждём — подпишитесь на канал и нажмите «Я вступил(а) в канал» ещё раз.",
            reply_markup=channel_kb()
        )


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
    await start_web_app()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
