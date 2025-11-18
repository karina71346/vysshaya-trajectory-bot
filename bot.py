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

# PORT нужен именно для Render Web Service
PORT = int(os.getenv("PORT", "10000"))

bot = Bot(TOKEN)   # без parse_mode, шлём простой текст
dp = Dispatcher()

# простейшее «состояние» пользователей в памяти
# user_id -> "await_consent" / "await_name" / "await_contacts" / "done" / "no_consent"
user_states: dict[int, str] = {}
user_profiles: dict[int, dict] = {}   # здесь складываем имя/роль и контакты


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


def contact_kb() -> ReplyKeyboardMarkup:
    """
    Клавиатура для отправки контакта.
    """
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


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """
    Первый шаг: текст о персональных данных + запрос согласия.
    """
    user_id = message.from_user.id
    user_states[user_id] = "await_consent"

    text = (
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.\n\n"
        "Перед тем как получить интерактивную тетрадь лидера, нужно совсем чуть-чуть формальностей:\n"
        "🔹 Подтвердите, что вы согласны на обработку персональных данных (обязательное требование).\n"
        "🔹 После этого мы продолжим.\n\n"
        "▪️ Политика конфиденциальности\n"
        "▪️ Согласие на обработку персональных данных\n\n"
        "Полный текст документов можно получить по запросу на email: carmen_84@inbox.ru\n\n"
        "🛡️ Нажимая кнопку «Далее», вы даёте согласие на обработку персональных данных\n"
        "и принимаете условия Политики конфиденциальности.\n\n"
        "👋 На связи Карина Конорева.\n"
        "Здесь предприниматели выходят из режима «герой-одиночка» и собирают систему, "
        "которая опирается не только на личную силу, но и на зрелость управления.\n\n"
        "Нажмите «Далее», чтобы начать."
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
        "Отлично! Давайте начнём знакомство.\n\n"
        "Напишите, пожалуйста, в одном сообщении:\n"
        "— как к вам обращаться (имя или ФИО);\n"
        "— и какую роль вы сейчас играете в бизнесе.\n\n"
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
    Команда /notebook: выдаём тетрадь только тем, кто прошёл согласие и указал данные.
    """
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if state != "done":
        await message.answer(
            "Чтобы выдать тебе тетрадь лидера, мне нужно пройти короткий шаг согласия и знакомства.\n"
            "Напиши, пожалуйста, /start и пройди его заново."
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
    — если ждём имя/роль — сохраняем и просим контакты;
    — если ждём контакты — фиксируем и выдаём тетрадь;
    — если обычный режим — простое эхо.
    """
    user_id = message.from_user.id
    state = user_states.get(user_id)

    # шаг ввода имени и роли
    if state == "await_name":
        profile = user_profiles.get(user_id, {})
        profile["name_role"] = message.text
        user_profiles[user_id] = profile

        logging.info(f"Профиль лидера (имя/роль): {user_id} -> {message.text!r}")

        user_states[user_id] = "await_contacts"

        await message.answer(
            "Благодарю! Теперь давайте оставим контакты, чтобы мы с вами не потерялись.\n\n"
            "Отправьте, пожалуйста, ваш номер телефона и почту:\n"
            "— можно нажать кнопку «📲 Отправить мой номер»,\n"
            "— или просто написать номер и email в одном сообщении.",
            reply_markup=contact_kb()
        )
        return

    # шаг ввода контактов (телефон + почта)
    if state == "await_contacts":
