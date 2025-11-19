import os
import asyncio
import logging

from aiohttp import web

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.enums import ChatMemberStatus

logging.basicConfig(level=logging.INFO)

# =====================================================================
# НАСТРОЙКИ (меняешь только эти значения, остальное не трогаешь)
# =====================================================================

TOKEN = os.getenv("BOT_TOKEN")  # на Render уже задан, тут ничего не правим

# Юзернейм твоего канала (где проверяем подписку)
CHANNEL_USERNAME = "@businesskodrosta"

# Ссылка на интерактивную тетрадь по делегированию
# 👉 ПОДСТАВЬ сюда реальный адрес своей тетради
TETRAD_URL = "https://tetrad-lidera.netlify.app/"

# Ссылка для записи на консультацию
# 👉 ПОДСТАВЬ сюда свой рабочий линк (личный TG, лендинг, форма и т.п.)
CONSULT_LINK = "https://forms.yandex.ru/u/69178642068ff0624a625f20/"

# База для прямых ссылок на PDF в GitHub (raw, а не HTML-страница)
GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/karina71346/vysshaya-trajectory-bot/main"
)

# =====================================================================

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в переменных окружения.")

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()


# ------------------------- FSM Состояния -------------------------------

class Form(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_email = State()


# --------------------------- Клавиатуры --------------------------------

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📁 Папка лидера")],
            [
                KeyboardButton(text="ℹ️ О Карине"),
                KeyboardButton(text="🧭 Записаться на консультацию/сессию"),
            ],
        ],
        resize_keyboard=True,
    )


def consent_kb() -> InlineKeyboardMarkup:
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
                    text="📄 Согласие на обработку персональных данных",
                    url=f"{GITHUB_RAW_BASE}/soglasie_na_obrabotku_pd.pdf",
                )
            ],
            [InlineKeyboardButton(text="Далее", callback_data="consent_continue")],
        ]
    )


def leader_pack_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📘 Открыть тетрадь лидера",
                    url=TETRAD_URL,
                )
            ],
            [
                InlineKeyboardButton(
                    text="📗 Гайд «Карта управленческой зрелости»",
                    url=f"{GITHUB_RAW_BASE}/karta_upravlencheskoy_zrelosti.pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📙 Чек-лист зрелого лидера",
                    url=f"{GITHUB_RAW_BASE}/checklist_zrelogo_lidera.pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Подборка книг для лидеров",
                    url=f"{GITHUB_RAW_BASE}/podborca_knig_liderstvo.pdf",
                )
            ],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_menu")],
        ]
    )


def consult_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оставить заявку", url=CONSULT_LINK)],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_menu")],
        ]
    )


# --------------------------- Хендлеры ----------------------------------


@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    text = (
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.\n\n"
        "Перед тем как получить Папку лидера и интерактивную тетрадь, нужно чуть-чуть формальностей:\n"
        "🔹 подтвердить согласие на обработку персональных данных.\n\n"
        "Сначала посмотрите документы, затем нажмите «Далее»."
    )
    await message.answer(text, reply_markup=consent_kb())


# --- после согласия — собираем данные ---

@dp.callback_query(F.data == "consent_continue")
async def consent_continue(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Отлично! Давайте начнём знакомство.\n\n"
        "Напишите, пожалуйста, как к вам обращаться — ФИ.",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(Form.waiting_name)


@dp.message(Form.waiting_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить мой номер", request_contact=True)]],
        resize_keyboard=True,
    )

    await message.answer(
        "Спасибо! Теперь отправьте, пожалуйста, ваш телефон.\n"
        "Можно нажать кнопку «Отправить мой номер» или написать его текстом.",
        reply_markup=kb,
    )
    await state.set_state(Form.waiting_phone)


@dp.message(Form.waiting_phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await ask_email(message, state)


@dp.message(Form.waiting_phone)
async def process_phone_text(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await ask_email(message, state)


async def ask_email(message: types.Message, state: FSMContext):
    await message.answer(
        "Теперь напишите, пожалуйста, вашу почту.",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(Form.waiting_email)


@dp.message(Form.waiting_email)
async def process_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text.strip())

    await message.answer(
        "Благодарю! Теперь мы с вами на связи.\n\n"
        "Чтобы получить материалы, нужно вступить в канал "
        "«Бизнес со смыслом» и подтвердить участие.",
    )

    join_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Вступить в канал",
                    url="https://t.me/businesskodrosta",
                )
            ],
            [InlineKeyboardButton(text="Я вступил(а)", callback_data="check_sub")],
        ]
    )

    await message.answer(
        "Перейдите в канал по кнопке ниже, затем вернитесь в бот и нажмите «Я вступил(а)».",
        reply_markup=join_kb,
    )


# --- проверка подписки на канал ---

@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        status = member.status
    except Exception as e:
        logging.exception("Не удалось проверить подписку: %s", e)
        await callback.answer(
            "Не получилось проверить подписку. Попробуйте ещё раз чуть позже.",
            show_alert=True,
        )
        return

    if status in {
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.RESTRICTED,
    }:
        # всё ок, человек в канале
        await callback.message.answer(
            "Отлично, я вижу вас в канале 👌\n"
            "Отправляю Папку лидера и главное меню.",
            reply_markup=main_menu_kb(),
        )
        await send_leader_pack(callback.message)
        await callback.answer()
    else:
        await callback.answer(
            "Пока не вижу вас в канале. "
            "Пожалуйста, вступите и нажмите кнопку ещё раз.",
            show_alert=True,
        )


# --- папка лидера ---

async def send_leader_pack(message: types.Message):
    text = (
        "🎁 <b>Папка лидера</b>\n\n"
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
    await message.answer(text, reply_markup=leader_pack_kb())


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("Вы в главном меню.", reply_markup=main_menu_kb())


@dp.message(F.text == "📁 Папка лидера")
async def menu_leader_pack(message: types.Message):
    await send_leader_pack(message)


# --- раздел «Обо мне» ---

@dp.message(F.text == "ℹ️ Обо мне")
async def about_me(message: types.Message):
    text = (
        "ℹ️ <b>Информация о Карине Коноревой</b>\n\n"
        "• Бизнес-психолог, ментор управленческой зрелости и командный коуч.\n"
        "• 20+ лет пути от преподавателя до предпринимателя.\n"
        "• Основатель проекта «Высшая Траектория».\n"
        "• Эксперт по построению живых команд и системному росту бизнеса.\n\n"
        "Через этот бот вы получаете инструменты, которые помогают "
        "предпринимателям выходить из режима «герой-одиночка» "
        "и строить предсказуемый бизнес с опорой на команду."
    )
    await message.answer(text, reply_markup=main_menu_kb())


# --- запись на консультацию ---

@dp.message(F.text == "🧭 Записаться на консультацию")
async def consult(message: types.Message):
    text = (
        "🧭 <b>Записаться на консультацию</b>\n\n"
        "Если вы хотите разобраться с управленческой нагрузкой, командой или стратегией роста —\n"
        "можно записаться на индивидуальную консультацию.\n\n"
        "Нажмите кнопку ниже, чтобы перейти к заявке."
    )
    await message.answer(text, reply_markup=consult_kb())


# ---------------------- Инфраструктура для Render ---------------------


async def on_startup(app: web.Application):
    # запускаем long polling внутри aiohttp-приложения
    asyncio.create_task(dp.start_polling(bot))


async def handle_root(request: web.Request):
    return web.Response(text="Bot is running")


def main():
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.on_startup.append(on_startup)

    port = int(os.getenv("PORT", "10000"))
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
