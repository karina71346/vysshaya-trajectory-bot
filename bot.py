import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiohttp import web

logging.basicConfig(level=logging.INFO)

# === Конфиг ===

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN (переменная окружения).")

bot = Bot(TOKEN)
dp = Dispatcher()

# Канал, куда нужно вступить
CHANNEL_USERNAME = "@businesskodrosta"

# База для PDF-файлов в репозитории GitHub
# ВАЖНО: проверь, что имена файлов совпадают с реальными!
GITHUB_RAW_BASE = "https://github.com/karina71346/vysshaya-trajectory-bot/raw/main"

# Простые "состояния" пользователя
user_states: dict[int, str] = {}
user_data: dict[int, dict] = {}


# === Клавиатуры ===

def pd_inline_kb() -> InlineKeyboardMarkup:
    """
    Кнопки под текстом о ПДн: две ссылки + «Далее».
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Политика конфиденциальности",
                    url=f"{GITHUB_RAW_BASE}/politika_konfidencialnosti.pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛡 Согласие на обработку персональных данных",
                    url=f"{GITHUB_RAW_BASE}/soglasie_na_obrabotku_pd.pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="▶️ Далее",
                    callback_data="pd_next",
                )
            ],
        ]
    )


def contact_phone_kb() -> ReplyKeyboardMarkup:
    """
    Клавиатура для отправки контакта.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📲 Отправить мой номер",
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def channel_kb() -> InlineKeyboardMarkup:
    """
    Кнопки для шага с каналом.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔔 Вступить в канал «Бизнес со смыслом»",
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


def notebook_inline_kb() -> InlineKeyboardMarkup:
    """
    Кнопка на интерактивную тетрадь лидера (Netlify).
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔷 Открыть тетрадь лидера",
                    url="https://tetrad-lidera.netlify.app/",
                )
            ]
        ]
    )


def leader_pack_kb() -> InlineKeyboardMarkup:
    """
    Папка лидера: 4 подарка.
    ОБЯЗАТЕЛЬНО проверь имена файлов в репозитории.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📘 Тетрадь лидера (онлайн)",
                    url="https://tetrad-lidera.netlify.app/",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧭 Гайд «Карта управленческой зрелости»",
                    url=f"{GITHUB_RAW_BASE}/karta_upravlencheskoy_zrelosti.pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Чек-лист зрелого лидера",
                    url=f"{GITHUB_RAW_BASE}/checklist_zrelogo_lidera.pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Подборка книг для современных лидеров",
                    url=f"{GITHUB_RAW_BASE}/podborca_knig_liderstvo.pdf",
                )
            ],
        ]
    )


# === Служебные функции ===

async def send_notebook(chat_id: int):
    """
    Сообщение с кнопкой на интерактивную тетрадь.
    """
    text = (
        "🧩 Интерактивная «Тетрадь лидера по делегированию»\n\n"
        "Откройте её в браузере и выполните упражнения — "
        "вы увидите, где именно вы перегружены и что можно делегировать уже на этой неделе."
    )
    await bot.send_message(chat_id, text, reply_markup=notebook_inline_kb())


async def send_leader_pack(chat_id: int):
    """
    Сообщение с описанием и кнопками Папки лидера (4 подарка).
    """
    text = (
        "🎁 Папка лидера\n\n"
        "Здесь собраны материалы, о которых ты рассказываешь на выступлении:\n\n"
        "✅ Интерактивная тетрадь лидера по делегированию\n"
        "→ вы поймёте, где ваша главная точка перегруза и как её передать уже на этой неделе.\n\n"
        "✅ Гайд «Карта управленческой зрелости»\n"
        "→ вы найдёте, на каком уровне управления застряли и как выйти выше.\n\n"
        "✅ Чек-лист зрелого лидера\n"
        "→ вы проверите, насколько вы не спасатель, а действительно стратег.\n\n"
        "✅ Подборка книг для современных лидеров\n"
        "→ чтобы не искать, а сразу читать то, что помогает масштабироваться.\n\n"
        "Все материалы — в кнопках ниже 👇"
    )
    await bot.send_message(chat_id, text, reply_markup=leader_pack_kb())


# === Хэндлеры бота ===

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = "pd"

    text = (
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.\n\n"
        "Перед тем как получить интерактивную тетрадь лидера, нужно совсем чуть-чуть формальностей:\n"
        "🔹 Подтвердите, что вы согласны на обработку персональных данных (обязательное требование).\n"
        "🔹 После этого мы продолжим.\n\n"
        "🛡 Нажимая кнопку «Далее», вы даёте согласие на обработку персональных данных "
        "и принимаете условия Политики конфиденциальности."
    )

    await message.answer(text, reply_markup=pd_inline_kb())


@dp.message(Command("ping"))
async def cmd_ping(message: types.Message):
    await message.answer("pong")


@dp.callback_query(F.data == "pd_next")
async def cb_pd_next(callback: types.CallbackQuery):
    """
    После согласия на ПДн — знакомство.
    """
    user_id = callback.from_user.id
    user_states[user_id] = "await_name"

    await callback.answer()
    await callback.message.answer(
        "Отлично! Давайте начнём знакомство.\n\n"
        "Напишите, пожалуйста, как к вам обращаться — ФИ.",
    )


@dp.callback_query(F.data == "check_channel")
async def cb_check_channel(callback: types.CallbackQuery):
    """
    Проверяем, вступил ли пользователь в канал.
    """
    user_id = callback.from_user.id

    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        status = getattr(member, "status", None)
    except Exception as e:
        logging.exception("Ошибка проверки канала: %s", e)
        await callback.answer(
            "Не удалось проверить подписку. Попробуйте ещё раз чуть позже.",
            show_alert=True,
        )
        return

    if status in ("member", "administrator", "creator"):
        user_states[user_id] = "ready"

        await callback.answer()
        await callback.message.answer(
            "Отлично! Я вижу, что вы в канале «Бизнес со смыслом» 🌟\n\n"
            "Сначала — интерактивная тетрадь, затем — вся Папка лидера."
        )

        await send_notebook(callback.message.chat.id)
        await send_leader_pack(callback.message.chat.id)

    else:
        await callback.answer()
        await callback.message.answer(
            "Увы, пока я не вижу вас в канале «Бизнес со смыслом» 😔\n\n"
            "1) Нажмите «Вступить в канал».\n"
            "2) Подпишитесь.\n"
            "3) Вернитесь в бот и снова нажмите «Я вступил(а) в канал».",
            reply_markup=channel_kb(),
        )


@dp.message(Command("gifts"))
async def cmd_gifts(message: types.Message):
    """
    Повторная выдача Папки лидера тем, кто уже прошёл путь.
    """
    user_id = message.from_user.id
    if user_states.get(user_id) != "ready":
        await message.answer(
            "Папку лидера я выдаю после короткого маршрута знакомства.\n"
            "Напишите /start, чтобы пройти его сначала."
        )
        return

    await send_leader_pack(message.chat.id)


@dp.message()
async def handle_message(message: types.Message):
    """
    Универсальный обработчик сообщений по простым состояниям.
    """
    user_id = message.from_user.id
    state = user_states.get(user_id)

    # --- Имя ---
    if state == "await_name":
        name = (message.text or "").strip()
        if not name:
            await message.answer("Пожалуйста, напишите, как к вам обращаться — ФИ.")
            return

        user_data[user_id] = {"name": name}
        user_states[user_id] = "await_phone"

        await message.answer(
            "Спасибо! 🙌\n\n"
            "Теперь напишите, пожалуйста, ваш телефон.\n"
            "Можно просто отправить номер текстом или нажать кнопку ниже.",
            reply_markup=contact_phone_kb(),
        )
        return

    # --- Телефон ---
    if state == "await_phone":
        phone = None
        if message.contact and message.contact.phone_number:
            phone = message.contact.phone_number
        else:
            phone = (message.text or "").strip()

        if not phone:
            await message.answer(
                "Пожалуйста, отправьте номер телефона или напишите его текстом."
            )
            return

        user_data.setdefault(user_id, {})["phone"] = phone
        user_states[user_id] = "await_email"

        await message.answer(
            "Принято ✅\n\n"
            "Теперь напишите вашу почту.\n"
            "На случай, если захотите получать материалы и напоминания на email.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    # --- Почта ---
    if state == "await_email":
        email = (message.text or "").strip()
        user_data.setdefault(user_id, {})["email"] = email
        user_states[user_id] = "await_channel"

        await message.answer(
            "Благодарю! Теперь мы с вами на связи 🙌\n\n"
            "Совсем скоро вы увидите уровень своего лидерства через делегирование.\n"
            "Последний шаг — вступить в канал «Бизнес со смыслом».\n\n"
            "После вступления нажмите «Я вступил(а) в канал».",
            reply_markup=channel_kb(),
        )
        return

    # --- Все остальные случаи ---
    await message.answer(
        "Чтобы получить тетрадь и Папку лидера, напишите /start и пройдите короткий маршрут."
    )


# === HTTP-сервер для Render (PORT binding) ===

async def handle_root(request: web.Request):
    return web.Response(text="Vysshaya Traektoriya bot is running.")


async def start_web_app():
    app = web.Application()
    app.router.add_get("/", handle_root)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logging.info("HTTP server started on port %s", port)


# === Точка входа ===

async def main():
    logging.info("Бот запускается…")
    web_task = asyncio.create_task(start_web_app())
    await dp.start_polling(bot)
    await web_task


if __name__ == "__main__":
    asyncio.run(main())
