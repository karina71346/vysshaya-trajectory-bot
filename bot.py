import os
import asyncio
import logging

from aiohttp import web

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus, ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

logging.basicConfig(level=logging.INFO)

# ===== НАСТРОЙКИ ======================================================

TOKEN = os.getenv("BOT_TOKEN")  # Токен бота из Render

CHANNEL_USERNAME = "@businesskodrosta"  # канал

# Ссылка на интерактивную тетрадь
TETRAD_URL = "https://tetrad-lidera.netlify.app/"

# Форма на консультацию
CONSULT_LINK = "https://forms.yandex.ru/u/69178642068ff0624a625f20/"

# База для ПРЯМЫХ PDF-ссылок (raw, а не страница GitHub)
GITHUB_BASE = "https://raw.githubusercontent.com/karina71346/vysshaya-trajectory-bot/main"

# =====================================================================

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в переменных окружения.")

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


class Form(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_email = State()


# ---------- КЛАВИАТУРЫ -----------------------------------------------

def main_menu_kb() -> ReplyKeyboardMarkup:
    """Главное меню."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📁 Папка лидера")],
            [
                KeyboardButton(text="ℹ️ О Карине"),
                KeyboardButton(text="🧭 Записаться на консультацию"),
            ],
        ],
        resize_keyboard=True,
    )


def consent_kb() -> InlineKeyboardMarkup:
    """Кнопки под блоком согласия на ПДн."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Политика конфиденциальности",
                    url=f"{GITHUB_BASE}/politika_konfidencialnosti.pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📄 Согласие на обработку персональных данных",
                    url=f"{GITHUB_BASE}/soglasie_na_obrabotku_pd.pdf",
                )
            ],
            [InlineKeyboardButton(text="Далее", callback_data="consent_continue")],
        ]
    )


def leader_pack_kb() -> InlineKeyboardMarkup:
    """Кнопки под Папкой лидера."""
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
                    callback_data="lp_guide",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📙 Чек-лист зрелого лидера",
                    callback_data="lp_checklist",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Подборка книг для лидеров",
                    callback_data="lp_books",
                )
            ],
            [
                InlineKeyboardButton(
                    text="ℹ️ О Карине",
                    callback_data="about_me_cb",
                ),
                InlineKeyboardButton(
                    text="🧭 Консультация",
                    callback_data="consult_cb",
                ),
            ],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_menu")],
        ]
    )


def consult_kb() -> InlineKeyboardMarkup:
    """Кнопка на заявку плюс возврат в меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оставить заявку", url=CONSULT_LINK)],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_menu")],
        ]
    )


# ---------- СТАРТ И СБОР ДАННЫХ --------------------------------------

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    # Чистим состояние и убираем старое меню, если оно висело
    await state.clear()
    await message.answer("Запускаю бота заново 🔄", reply_markup=ReplyKeyboardRemove())

    text = (
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.\n\n"
        "Перед тем как получить Папку лидера и интерактивную тетрадь, нужно чуть-чуть формальностей:\n"
        "🔹 подтвердить согласие на обработку персональных данных.\n\n"
        "Сначала посмотрите документы, затем нажмите «Далее»."
    )
    await message.answer(text, reply_markup=consent_kb())


@dp.callback_query(F.data == "consent_continue")
async def consent_continue(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Отлично! Давайте начнём знакомство.\n\n"
        "Напишите, пожалуйста, как к вам обращаться — ФИ.",
        reply_markup=ReplyKeyboardRemove(),
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
        reply_markup=ReplyKeyboardRemove(),
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


# ---------- ПРОВЕРКА ПОДПИСКИ ----------------------------------------

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
        # Сначала отправляем Папку лидера
        await send_leader_pack(callback.message)
        # Потом показываем главное меню
        await callback.message.answer(
            "Вы в главном меню. Выберите нужный раздел 👇",
            reply_markup=main_menu_kb(),
        )
        await callback.answer()
    else:
        await callback.answer(
            "Пока не вижу вас в канале. "
            "Пожалуйста, вступите и нажмите кнопку ещё раз.",
            show_alert=True,
        )


# ---------- ПАПКА ЛИДЕРА ---------------------------------------------

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


@dp.message(F.text == "📁 Папка лидера")
async def menu_leader_pack(message: types.Message):
    await send_leader_pack(message)


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("Вы в главном меню.", reply_markup=main_menu_kb())


# --- отправка самих PDF как файлов по клику в Папке лидера -----------

@dp.callback_query(F.data == "lp_guide")
async def send_guide(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer_document(
        document=f"{GITHUB_BASE}/karta_upravlencheskoy_zrelosti.pdf",
        caption="Гайд «Карта управленческой зрелости»",
    )


@dp.callback_query(F.data == "lp_checklist")
async def send_checklist(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer_document(
        document=f"{GITHUB_BASE}/checklist_zrelogo_lidera.pdf",
        caption="Чек-лист зрелого лидера",
    )


@dp.callback_query(F.data == "lp_books")
async def send_books(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer_document(
        document=f"{GITHUB_BASE}/podborca_knig_liderstvo.pdf",
        caption="Подборка книг для современных лидеров",
    )


# ---------- БЛОК «О КАРИНЕ» ------------------------------------------

async def send_about_me(message: types.Message):
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


@dp.message(F.text == "ℹ️ О Карине")
async def about_me(message: types.Message):
    await send_about_me(message)


@dp.callback_query(F.data == "about_me_cb")
async def cb_about_me(callback: types.CallbackQuery):
    await callback.answer()
    await send_about_me(callback.message)


# ---------- КОНСУЛЬТАЦИЯ ---------------------------------------------

async def send_consult(message: types.Message):
    text = (
        "🧭 <b>Записаться на консультацию</b>\n\n"
        "Если вы хотите разобраться с управленческой нагрузкой, командой или стратегией роста —\n"
        "можно записаться на индивидуальную консультацию.\n\n"
        "Нажмите кнопку ниже, чтобы перейти к заявке."
    )
    await message.answer(text, reply_markup=consult_kb())


@dp.message(F.text == "🧭 Записаться на консультацию")
async def consult(message: types.Message):
    await send_consult(message)


@dp.callback_query(F.data == "consult_cb")
async def cb_consult(callback: types.CallbackQuery):
    await callback.answer()
    await send_consult(callback.message)


# ---------- СЕРВЕР ДЛЯ RENDER ----------------------------------------

async def on_startup(app: web.Application):
    # Убираем вебхук, если он где-то был настроен (иначе конфликт getUpdates)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logging.warning("Не удалось удалить webhook: %s", e)

    # Запускаем поллинг
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
