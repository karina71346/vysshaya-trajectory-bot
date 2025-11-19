import os
import asyncio
import logging

from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext


# -------------------- БАЗОВЫЕ НАСТРОЙКИ --------------------

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN (переменная окружения).")

bot = Bot(TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Канал и ссылки
CHANNEL_ID = "@businesskodrosta"  # если будет numeric id, подставим его сюда

NOTEBOOK_URL = "https://tetrad-lidera.netlify.app/"

# база для всех PDF в репозитории
GITHUB_BLOB_BASE = (
    "https://github.com/karina71346/vysshaya-trajectory-bot/blob/main"
)


# -------------------- СОСТОЯНИЯ --------------------

class LeadStates(StatesGroup):
    waiting_consent = State()
    waiting_name = State()
    waiting_phone = State()
    waiting_email = State()
    waiting_channel_check = State()


# -------------------- КЛАВИАТУРЫ --------------------

def consent_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопки под приветствием:
    - Политика конфиденциальности (PDF, открывается на GitHub)
    - Согласие на обработку ПД (PDF)
    - Далее (callback)
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Политика конфиденциальности",
                    url=f"{GITHUB_BLOB_BASE}/politika_konfidencialnosti.pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📄 Согласие на обработку ПД",
                    url=f"{GITHUB_BLOB_BASE}/soglasie_na_obrabotku_pd.pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Далее",
                    callback_data="consent_next",
                )
            ],
        ]
    )
    return kb


def contact_keyboard() -> ReplyKeyboardMarkup:
    """
    Кнопка для отправки контакта.
    ВАЖНО: в aiogram v3 нужно передавать параметр keyboard=
    """
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Отправить мой номер", request_contact=True
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return kb


def channel_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопки для шага с каналом:
    - перейти в канал
    - я вступил(а)
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Вступить в канал",
                    url="https://t.me/businesskodrosta",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Я вступил(а)",
                    callback_data="check_channel",
                )
            ],
        ]
    )
    return kb


def leader_pack_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура под «Папкой лидера»:
    - тетрадь (Netlify)
    - гайд
    - чек-лист
    - подборка книг
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔷 Открыть тетрадь лидера",
                    url=NOTEBOOK_URL,
                )
            ],
            [
                InlineKeyboardButton(
                    text="📘 Гайд «Карта управленческой зрелости»",
                    url=f"{GITHUB_BLOB_BASE}/karta_upravlencheskoy_zrelosti.pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Чек-лист зрелого лидера",
                    url=f"{GITHUB_BLOB_BASE}/checklist_zrelogo_lidera.pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Подборка книг для современных лидеров",
                    url=f"{GITHUB_BLOB_BASE}/podborca_knig_liderstvo.pdf",
                )
            ],
        ]
    )
    return kb


# -------------------- ХЭНДЛЕРЫ --------------------

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    /start – приветствие + юридический блок.
    """
    await state.set_state(LeadStates.waiting_consent)

    text = (
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.\n\n"
        "Перед тем как получить интерактивную тетрадь лидера, нужно совсем чуть-чуть формальностей:\n"
        "🔹 подтвердить согласие на обработку персональных данных (обязательное требование);\n"
        "🔹 после этого продолжим маршрут лидера.\n\n"
        "🛡️ Нажимая кнопку «Далее», вы даёте согласие на обработку персональных данных\n"
        "и принимаете условия Политики конфиденциальности.\n\n"
        "Если хотите — можете открыть документы выше, посмотреть и сохранить себе."
    )

    await message.answer(text, reply_markup=consent_keyboard())


@dp.callback_query(F.data == "consent_next")
async def on_consent_next(callback: CallbackQuery, state: FSMContext):
    """
    Пользователь нажал «Далее» под юр. блоком.
    Переходим к знакомству – просим имя.
    """
    await state.set_state(LeadStates.waiting_name)

    await callback.message.answer(
        "Отлично! Давайте начнём знакомство.\n\n"
        "Напишите, пожалуйста, как к вам обращаться (ФИ).",
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.answer()


@dp.message(LeadStates.waiting_name)
async def on_name(message: Message, state: FSMContext):
    """
    Пользователь прислал имя.
    """
    name = message.text.strip()
    await state.update_data(name=name)

    await state.set_state(LeadStates.waiting_phone)
    await message.answer(
        "Напишите, пожалуйста, ваш телефон.\n\n"
        "Можете просто отправить номер текстом или нажать кнопку ниже 👇",
        reply_markup=contact_keyboard(),
    )


@dp.message(LeadStates.waiting_phone, F.contact)
async def on_phone_contact(message: Message, state: FSMContext):
    """
    Пользователь отправил контакт через кнопку.
    """
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await ask_email(message, state)


@dp.message(LeadStates.waiting_phone, F.text)
async def on_phone_text(message: Message, state: FSMContext):
    """
    Пользователь написал номер текстом.
    """
    phone = message.text.strip()
    await state.update_data(phone=phone)
    await ask_email(message, state)


async def ask_email(message: Message, state: FSMContext):
    await state.set_state(LeadStates.waiting_email)
    await message.answer(
        "Напишите, пожалуйста, вашу электронную почту.\n\n"
        "На всякий случай, чтобы мы могли прислать вам материалы и напоминание.",
        reply_markup=ReplyKeyboardRemove(),
    )


@dp.message(LeadStates.waiting_email)
async def on_email(message: Message, state: FSMContext):
    email = message.text.strip()
    await state.update_data(email=email)

    data = await state.get_data()
    name = data.get("name", "лидер")

    await state.set_state(LeadStates.waiting_channel_check)

    await message.answer(
        f"Благодарю, {name}! Теперь мы с вами на связи 🙌\n\n"
        "Чтобы получать максимум пользы, я приглашаю вас в канал "
        "«Бизнес со смыслом»: там будут дополнительные разборы, кейсы и акценты после выступления.\n\n"
        "1️⃣ Вступите в канал по кнопке ниже.\n"
        "2️⃣ Нажмите «Я вступил(а)», когда будете внутри.",
        reply_markup=channel_keyboard(),
    )


@dp.callback_query(F.data == "check_channel")
async def on_check_channel(callback: CallbackQuery, state: FSMContext):
    """
    Проверяем подписку на канал (по возможности).
    Если у бота нет прав – просто выдаём материалы.
    """
    user_id = callback.from_user.id

    ok = False
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status not in ("left", "kicked"):
            ok = True
    except Exception as e:
        # Если бот не админ/нет доступа – не валим сценарий.
        logging.warning(f"Не удалось проверить подписку на канал: {e}")
        ok = True  # считаем, что всё хорошо

    if ok:
        await send_leader_pack(callback.message)
        await state.clear()
        await callback.answer("Доступ к материалам открыт 🎁", show_alert=False)
    else:
        await callback.answer(
            "Похоже, вас ещё нет в канале. "
            "Мы очень ждём вас там – вернитесь после вступления 🙌",
            show_alert=True,
        )


async def send_leader_pack(message: Message):
    """
    Отправка «Папки лидера» с 4 подарками.
    """
    text = (
        "🎁 Папка лидера\n\n"
        "Здесь собраны ключевые материалы для роста управленческой зрелости:\n\n"
        "✅ Интерактивная тетрадь лидера по делегированию\n"
        "→ вы поймёте, где ваша главная точка перегруза и как её передать уже на этой неделе.\n\n"
        "✅ Гайд «Карта управленческой зрелости»\n"
        "→ вы найдёте, на каком уровне управления застряли и как выйти выше.\n\n"
        "✅ Чек-лист зрелого лидера\n"
        "→ вы проверите: насколько вы не спасатель, а действительно стратег.\n\n"
        "✅ Подборка книг для современных лидеров\n"
        "→ чтобы не искать, а сразу читать, что действительно помогает масштабироваться.\n"
    )

    await message.answer(text, reply_markup=leader_pack_keyboard())


# -------------------- МИНИ-WEB-СЕРВЕР ДЛЯ RENDER --------------------

async def handle_root(request):
    return web.Response(text="OK – Vysshaya Traektoriya bot is running.")


async def main():
    # поднимаем aiohttp-сервер, чтобы Render видел открытый порт
    app = web.Application()
    app.router.add_get("/", handle_root)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logging.info(f"HTTP-сервер запущен на порту {port}")
    logging.info("Стартуем polling бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
