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
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage


# ========= НАСТРОЙКИ (ОБНОВИ ССЫЛКИ ПОД СЕБЯ) =========

# Ссылка на интерактивную тетрадь (Netlify)
NOTEBOOK_URL = "https://tetrad-lidera.netlify.app/"

# PDF «Карта управленческой зрелости»
GUIDE_URL = "https://YOUR_HOST/karta_upravlencheskoy_zrelosti.pdf"

# PDF «Чек-лист зрелого лидера»
CHECKLIST_URL = "https://YOUR_HOST/checklist_zrelogo_lidera.pdf"

# PDF/страница с подборкой книг
BOOKS_URL = "https://YOUR_HOST/books_for_leaders.pdf"

# Публиный канал
CHANNEL_URL = "https://t.me/businesskodrosta"

# Политика и согласие на ПД (можно оставить GitHub raw или свои ссылки)
POLICY_URL = "https://raw.githubusercontent.com/karina71346/vysshaya-trajectory-bot/main/politika_konfidencialnosti.pdf"
CONSENT_URL = "https://raw.githubusercontent.com/karina71346/vysshaya-trajectory-bot/main/soglasie_na_obrabotku_pd.pdf"


# ========= БАЗОВАЯ НАСТРОЙКА БОТА =========

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN (переменная окружения).")

bot = Bot(TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())


# ========= FSM СОСТОЯНИЯ =========

class LeadForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_email = State()


# ========= КЛАВИАТУРЫ =========

def pd_inline_kb() -> InlineKeyboardMarkup:
    """
    Клавиатура для первого шага: ПД + кнопка «Далее».
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Политика конфиденциальности",
                    url=POLICY_URL,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛡 Согласие на обработку персональных данных",
                    url=CONSENT_URL,
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Далее",
                    callback_data="pd_accepted",
                )
            ],
        ]
    )


main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📂 Папка лидера")],
        [
            KeyboardButton(text="ℹ️ Информация о Карине"),
            KeyboardButton(text="🧭 Записаться на консультацию"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие…",
)


def phone_request_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Отправить мой номер",
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Отправьте номер или напишите его…",
    )


def channel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Вступить в канал", url=CHANNEL_URL)]
        ]
    )


def notebook_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔷 Открыть тетрадь лидера",
                    url=NOTEBOOK_URL,
                )
            ]
        ]
    )


# ========= ХЕНДЛЕРЫ =========

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    """
    Старт: ПД + согласие.
    """
    await state.clear()

    text = (
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.\n\n"
        "Перед тем как получить интерактивную тетрадь лидера, нужно совсем чуть-чуть формальностей:\n"
        "🔹 Подтвердите, что вы согласны на обработку персональных данных (обязательное требование).\n"
        "🔹 После этого мы продолжим.\n\n"
        "🛡 Нажимая кнопку «Далее», вы даёте согласие на обработку персональных данных "
        "и принимаете условия Политики конфиденциальности."
    )
    await message.answer(text, reply_markup=pd_inline_kb())


@dp.callback_query(F.data == "pd_accepted")
async def on_pd_accepted(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Пользователь нажал «Далее» после ПД.
    """
    await callback.answer()
    await callback.message.answer(
        "Отлично! Давайте начнём знакомство.\n\n"
        "Напишите, пожалуйста, как к вам обращаться (Имя и, при желании, Фамилия).",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(LeadForm.waiting_for_name)


@dp.message(LeadForm.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Напишите, пожалуйста, как к вам обращаться 🙌")
        return

    await state.update_data(name=name)

    await message.answer(
        "Спасибо, {0}! Теперь давайте оставим контактный телефон.\n\n"
        "Можно нажать кнопку «Отправить мой номер» или просто написать номер в ответном сообщении."
        .format(name),
        reply_markup=phone_request_kb(),
    )
    await state.set_state(LeadForm.waiting_for_phone)


@dp.message(LeadForm.waiting_for_phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext) -> None:
    phone = message.contact.phone_number
    await state.update_data(phone=phone)

    await message.answer(
        "Приняла номер: <b>{0}</b>.\n\nТеперь напишите, пожалуйста, вашу почту, "
        "чтобы я могла отправлять вам полезные материалы."
        .format(phone),
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(LeadForm.waiting_for_email)


@dp.message(LeadForm.waiting_for_phone, F.text)
async def process_phone_text(message: types.Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()
    if not phone:
        await message.answer("Пришлите номер или нажмите кнопку «Отправить мой номер» 😊")
        return

    await state.update_data(phone=phone)

    await message.answer(
        "Спасибо! Номер <b>{0}</b> сохранила.\n\nТеперь напишите, пожалуйста, вашу почту."
        .format(phone),
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(LeadForm.waiting_for_email)


@dp.message(LeadForm.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext) -> None:
    email = (message.text or "").strip()
    await state.update_data(email=email)

    data = await state.get_data()
    logging.info("Новая заявка: %s", data)

    await message.answer(
        "Благодарю! Теперь мы с вами на связи 🙌\n\n"
        "Сейчас вы можете:\n"
        "• вступить в мой канал «Бизнес со смыслом»;\n"
        "• открыть Папку лидера;\n"
        "• узнать подробнее обо мне или записаться на консультацию.",
        reply_markup=main_menu_kb,
    )

    await message.answer(
        "Вот ссылка на канал «Бизнес со смыслом»:",
        reply_markup=channel_kb(),
    )

    await state.clear()


# ---- Главное меню ----

async def send_leader_pack(message: types.Message) -> None:
    """
    Папка лидера: ссылки на материалы.
    """
    text = (
        "<b>🎁 Папка лидера</b>\n\n"
        "Здесь собраны ключевые материалы для роста управленческой зрелости:\n\n"
        f"✅ <b><a href=\"{NOTEBOOK_URL}\">Интерактивная тетрадь лидера по делегированию</a></b>\n"
        "→ вы поймёте, где ваша главная точка перегруза и как её передать уже на этой неделе.\n\n"
        f"✅ <b><a href=\"{GUIDE_URL}\">Гайд «Карта управленческой зрелости»</a></b>\n"
        "→ вы найдёте, на каком уровне управления застряли и как выйти выше.\n\n"
        f"✅ <b><a href=\"{CHECKLIST_URL}\">Чек-лист зрелого лидера</a></b>\n"
        "→ вы проверите, насколько вы не спасатель, а действительно стратег.\n\n"
        f"✅ <b><a href=\"{BOOKS_URL}\">Подборка книг для современных лидеров</a></b>\n"
        "→ чтобы не искать, а сразу читать то, что помогает масштабироваться.\n\n"
        "Все материалы открываются в браузере — а дальше вы уже решаете, что сохранить себе."
    )

    await message.answer(text, disable_web_page_preview=False)
    # Отдельная кнопка для тетради
    await message.answer("Жмите, чтобы открыть тетрадь лидера 👇", reply_markup=notebook_inline_kb())


@dp.message(F.text == "📂 Папка лидера")
async def on_leader_pack(message: types.Message) -> None:
    await send_leader_pack(message)


@dp.message(F.text == "ℹ️ Информация о Карине")
async def about_karina(message: types.Message) -> None:
    text = (
        "👋 На связи Карина Конорева.\n\n"
        "Я предприниматель, бизнес-психолог, командный коуч и трекер управленческой зрелости.\n"
        "Помогаю собственникам выйти из режима «герой-одиночка» и собрать систему, "
        "которая даёт предсказуемый результат через живые команды и зрелое управление.\n\n"
        "Мой путь:\n"
        "• 20+ лет от преподавателя до предпринимателя;\n"
        "• 18 лет практики как интегральный бизнес-психолог;\n"
        "• 10+ лет — развитие команд и HR-функции;\n"
        "• федеральный спикер, «HR-эксперт года» по версии PERSONO.\n\n"
        "В боте я собираю практичные инструменты, которые реально работают у лидеров и команд с амбициями."
    )
    await message.answer(text)


@dp.message(F.text == "🧭 Записаться на консультацию")
async def book_consult(message: types.Message) -> None:
    text = (
        "🧭 Запись на индивидуальную консультацию.\n\n"
        "Напишите, пожалуйста, в одном сообщении:\n"
        "• ваш запрос (что сейчас болит в бизнесе / команде);\n"
        "• масштаб бизнеса и роль (собственник, СЕО, руководитель направления);\n"
        "• удобный способ связи (телефон, Telegram, e-mail).\n\n"
        "После этого я свяжусь с вами лично и предложу варианты формата и времени."
    )
    await message.answer(text)


@dp.message(Command("menu"))
async def cmd_menu(message: types.Message) -> None:
    await message.answer("Главное меню:", reply_markup=main_menu_kb)


# ========= ПРОСТОЙ ХТТП-СЕРВЕР ДЛЯ RENDER =========

async def healthcheck(request: web.Request) -> web.Response:
    return web.Response(text="Bot is running")


async def on_startup(app: web.Application) -> None:
    app["bot_task"] = asyncio.create_task(dp.start_polling(bot))
    logging.info("Bot polling started")


async def on_shutdown(app: web.Application) -> None:
    bot_task = app.get("bot_task")
    if bot_task:
        bot_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await bot_task
    logging.info("Bot polling stopped")


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", healthcheck)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app


if __name__ == "__main__":
    import contextlib

    port = int(os.getenv("PORT", 10000))
    logging.info(f"Starting web app on port {port}")
    web.run_app(create_app(), host="0.0.0.0", port=port)
