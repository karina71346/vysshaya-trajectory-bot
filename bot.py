import os
import asyncio
import logging

from aiohttp import web

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State


# -------------------------------------------------
# Базовая настройка
# -------------------------------------------------

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN (переменная окружения).")

bot = Bot(TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Канал, в который нужно вступить
CHANNEL_USERNAME = "@businesskodrosta"  # канал «Бизнес со смыслом»
CHANNEL_URL = "https://t.me/businesskodrosta"

# GitHub RAW – откуда отдаются PDF
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/karina71346/vysshaya-trajectory-bot/main"

# Документы по ПД
PDF_PD_POLICY = f"{GITHUB_RAW_BASE}/politika_konfidencialnosti.pdf"
PDF_PD_CONSENT = f"{GITHUB_RAW_BASE}/soglasie_na_obrabotku_pd.pdf"

# Папка лидера – материалы
PDF_KARTA_ZRELOSTI = f"{GITHUB_RAW_BASE}/karta_upravlencheskoy_zrelosti.pdf"
PDF_CHECKLIST = f"{GITHUB_RAW_BASE}/checklist_zrelogo_lidera.pdf"
PDF_BOOKS = f"{GITHUB_RAW_BASE}/podborca_knig_liderstvo.pdf"

# Интерактивная тетрадь лидера по делегированию (онлайн)
TETRAD_URL = "https://tetrad-lidera.netlify.app/"

# Ссылка для записи на консультацию
CONSULT_URL = "https://t.me/businesskodrosta"


# -------------------------------------------------
# Состояния анкеты
# -------------------------------------------------


class LeadForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_email = State()


# -------------------------------------------------
# Главное меню
# -------------------------------------------------

main_menu_kb = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton(text="📂 Папка лидера")],
        [
            KeyboardButton(text="ℹ️ Информация о Карине"),
            KeyboardButton(text="🧭 Записаться на консультацию"),
        ],
    ],
)


# -------------------------------------------------
# /start и согласие на ПД
# -------------------------------------------------


@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()

    text = (
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.\n\n"
        "Перед тем как получить интерактивную тетрадь лидера, нужно совсем чуть-чуть формальностей:\n"
        "🔹 Подтвердите, что вы согласны на обработку персональных данных (обязательное требование).\n"
        "🔹 После этого мы продолжим.\n\n"
        "▪️ Политика конфиденциальности\n"
        "▪️ Согласие на обработку персональных данных\n\n"
        "🛡 Нажимая кнопку «Далее», вы даёте согласие на обработку персональных данных "
        "и принимаете условия Политики конфиденциальности."
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Политика конфиденциальности (PDF)",
                    url=PDF_PD_POLICY,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛡 Согласие на обработку ПД (PDF)",
                    url=PDF_PD_CONSENT,
                )
            ],
            [InlineKeyboardButton(text="✅ Далее", callback_data="pd_accept")],
        ]
    )

    await message.answer(text, reply_markup=kb)


@dp.callback_query(F.data == "pd_accept")
async def cb_pd_accept(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    await callback.message.answer(
        "Отлично! Давайте начнём знакомство.\n\n"
        "Напишите, как к вам обращаться — ФИ:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(LeadForm.waiting_for_name)


# -------------------------------------------------
# Сбор имени / телефона / почты
# -------------------------------------------------


@dp.message(LeadForm.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)

    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Отправить мой номер",
                    request_contact=True,
                )
            ]
        ],
    )

    await message.answer(
        "Напишите, пожалуйста, ваш телефон.\n"
        "Можете нажать кнопку «📱 Отправить мой номер» или просто отправить номер текстом.",
        reply_markup=kb,
    )
    await state.set_state(LeadForm.waiting_for_phone)


@dp.message(LeadForm.waiting_for_phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await ask_email(message, state)


@dp.message(LeadForm.waiting_for_phone)
async def process_phone_text(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    await state.update_data(phone=phone)
    await ask_email(message, state)


async def ask_email(message: types.Message, state: FSMContext):
    await message.answer(
        "Напишите, пожалуйста, ваш e-mail.\n"
        "Он нужен, чтобы при необходимости отправить вам материалы.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(LeadForm.waiting_for_email)


@dp.message(LeadForm.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    email = message.text.strip()
    await state.update_data(email=email)

    data = await state.get_data()
    logging.info("Новый лид: %s", data)

    await state.clear()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Вступить в канал «Бизнес со смыслом»",
                    url=CHANNEL_URL,
                )
            ],
            [InlineKeyboardButton(text="✅ Я в канале", callback_data="check_sub")],
        ]
    )

    await message.answer(
        "Благодарю! Теперь мы с вами на связи 🙌\n\n"
        "Финальный шаг: вступите в канал «Бизнес со смыслом», "
        "а затем нажмите кнопку «✅ Я в канале».\n"
        "Там продолжается работа с управленческой зрелостью лидера.",
        reply_markup=kb,
    )


# -------------------------------------------------
# Проверка подписки на канал
# -------------------------------------------------


@dp.callback_query(F.data == "check_sub")
async def cb_check_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        status = member.status
    except Exception as e:
        logging.exception("Ошибка проверки подписки: %s", e)
        await callback.answer(
            "Не удалось проверить подписку, попробуйте ещё раз чуть позже.",
            show_alert=True,
        )
        return

    if status in ("member", "administrator", "creator"):
        await callback.answer("Вижу вас в канале, поехали! ✨")
        await callback.message.answer("Отлично! Тогда забирайте свою Папку лидера.")
        await send_leader_pack(callback.message.chat.id)
    else:
        await callback.answer()
        await callback.message.answer(
            "Увы, я пока не вижу вас в канале.\n"
            "Мы вас очень ждём 🤝\n"
            "Пожалуйста, зайдите в канал по кнопке выше и нажмите «✅ Я в канале» ещё раз.",
            reply_markup=callback.message.reply_markup,
        )


# -------------------------------------------------
# Папка лидера
# -------------------------------------------------


async def send_leader_pack(chat_id: int):
    text = (
        "🎁 <b>Папка лидера</b>\n\n"
        "Здесь собраны ключевые материалы для роста управленческой зрелости:\n\n"
        "✅ <b>Интерактивная тетрадь лидера по делегированию</b>\n"
        "→ вы поймёте, где ваша главная точка перегруза и как её передать уже на этой неделе.\n\n"
        "✅ <b>Гайд «Карта управленческой зрелости»</b>\n"
        "→ вы найдёте, на каком уровне управления застряли и как выйти выше.\n\n"
        "✅ <b>Чек-лист зрелого лидера</b>\n"
        "→ вы проверите, насколько вы не спасатель, а действительно стратег.\n\n"
        "✅ <b>Подборка книг для современных лидеров</b>\n"
        "→ чтобы не искать, а сразу читать, что действительно помогает масштабироваться.\n\n"
        "Нажмите на нужную кнопку — документ откроется в Telegram, а при желании его можно сохранить себе."
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📘 Тетрадь по делегированию (онлайн)",
                    url=TETRAD_URL,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗺 Карта управленческой зрелости (PDF)",
                    url=PDF_KARTA_ZRELOSTI,
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Чек-лист зрелого лидера (PDF)",
                    url=PDF_CHECKLIST,
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Подборка книг для лидеров (PDF)",
                    url=PDF_BOOKS,
                )
            ],
        ]
    )

    await bot.send_message(chat_id, text, reply_markup=kb)

    # Показать главное меню снизу
    await bot.send_message(
        chat_id,
        "👣 Дальше можно пользоваться главным меню ниже 👇",
        reply_markup=main_menu_kb,
    )


# -------------------------------------------------
# Главное меню / о Карине / консультация
# -------------------------------------------------


@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    await message.answer(
        "Главное меню. Выберите, что интересно сейчас:",
        reply_markup=main_menu_kb,
    )


@dp.message(F.text == "📂 Папка лидера")
async def menu_leader_pack(message: types.Message):
    await send_leader_pack(message.chat.id)


@dp.message(F.text == "ℹ️ Информация о Карине")
async def menu_about(message: types.Message):
    text = (
        "ℹ️ <b>Информация о Карине Коноревой</b>\n\n"
        "• Бизнес-психолог, интегральный коуч и HR-эксперт с 18+ годами практики.\n"
        "• Основатель проекта «Высшая траектория» — про живые команды и системный рост бизнеса.\n"
        "• Работает с предпринимателями и лидерами, которые хотят выйти из режима «герой-одиночка» "
        "и выстроить предсказуемый управляемый бизнес.\n\n"
        "Больше материалов и кейсов — в канале «Бизнес со смыслом»:\n"
        f"{CHANNEL_URL}"
    )
    await message.answer(text, reply_markup=main_menu_kb)


@dp.message(F.text == "🧭 Записаться на консультацию")
async def menu_consult(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧭 Оставить заявку в Telegram",
                    url=CONSULT_URL,
                )
            ]
        ]
    )

    text = (
        "🧭 <b>Запись на консультацию / коуч-сессию</b>\n\n"
        "Напишите пару слов о себе, бизнесе и запросе — Карина ответит и предложит "
        "ближайшие слоты для индивидуальной работы."
    )
    await message.answer(text, reply_markup=kb)


# -------------------------------------------------
# Фолбэк на непонятные сообщения
# -------------------------------------------------


@dp.message()
async def fallback(message: types.Message):
    await message.answer(
        "Я пока понимаю только команды бота и кнопки меню.\n"
        "Нажмите /start, если хотите пройти путь заново, или /menu — чтобы открыть главное меню.",
        reply_markup=main_menu_kb,
    )


# -------------------------------------------------
# HTTP-сервер для Render + запуск polling
# -------------------------------------------------


async def handle_root(request: web.Request) -> web.Response:
    return web.Response(text="Bot is running")


async def main():
    # Мини HTTP-сервер для Render (healthcheck)
    app = web.Application()
    app.add_routes([web.get("/", handle_root)])

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logging.info(f"HTTP-сервер запущен на порту {port}")

    # Запуск бота (long polling)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
