import os
import asyncio
import logging

from aiohttp import web

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ChatMemberStatus
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    FSInputFile,
)

logging.basicConfig(level=logging.INFO)

# ===== НАСТРОЙКИ ======================================================

TOKEN = os.getenv("BOT_TOKEN")  # Токен бота из Render

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в переменных окружения")

# Юзернейм и ссылка на канал
CHANNEL_USERNAME = "@businesskodrosta"
CHANNEL_LINK = "https://t.me/businesskodrosta"

# Ссылка на интерактивную тетрадь
TETRAD_URL = "https://tetrad-lidera.netlify.app/"

# Форма на консультацию
CONSULT_LINK = "https://forms.yandex.ru/u/69178642068ff0624a625f20/"

# Имена файлов в проекте
POLITIKA_FILE = "politika_konfidencialnosti.pdf"
SOGLASIE_FILE = "soglasie_na_obrabotku_pd.pdf"
KARTA_FILE = "karta_upravlencheskoy_zrelosti.pdf"
CHECKLIST_FILE = "checklist_zrelogo_lidera.pdf"
BOOKS_FILE = "podborka_knig_dlya_liderov.pdf"

KARINA_PHOTO_FILE = "KARINA_PHOTO_URL"

# ===== FSM ============================================================

class Registration(StatesGroup):
    waiting_for_name = State()


# ===== КНОПКИ ========================================================

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📂 Папка лидера")],
            [KeyboardButton(text="🧠 Практика дня")],
            [
                KeyboardButton(text="ℹ️ О Карине"),
                KeyboardButton(text="📍 Записаться на консультацию"),
            ],
        ],
        resize_keyboard=True,
    )


def consent_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен/Согласна", callback_data="consent_ok")]
        ]
    )


def after_name_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перейти в канал «Бизнес со смыслом»",
                    url=CHANNEL_LINK,
                )
            ],
            [InlineKeyboardButton(text="Я вступил(а)", callback_data="joined_channel")],
        ]
    )


def leaders_folder_kb() -> InlineKeyboardMarkup:
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
                    callback_data="send_karta",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📙 Чек-лист зрелого лидера",
                    callback_data="send_checklist",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Подборка книг для лидеров",
                    callback_data="send_books",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ В главное меню",
                    callback_data="back_to_menu",
                )
            ],
        ]
    )


def practice_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎯 Колесо фокуса", callback_data="practice_focus_wheel"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📤 Микроделегирование",
                    callback_data="practice_microdelegation",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💡 Откровение: точка реальности",
                    callback_data="practice_reality",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚀 Микрошаг к Высшей траектории",
                    callback_data="practice_microstep",
                )
            ],
        ]
    )


def practice_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ К другим практикам",
                    callback_data="practice_menu",
                )
            ]
        ]
    )


def about_karina_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перейти в канал «Бизнес со смыслом»",
                    url=CHANNEL_LINK,
                )
            ],
            [
                InlineKeyboardButton(
                    text="Записаться на консультацию",
                    url=CONSULT_LINK,
                )
            ],
        ]
    )


def consultation_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перейти к форме записи",
                    url=CONSULT_LINK,
                )
            ]
        ]
    )


# ===== ТЕКСТЫ =========================================================

WELCOME_TEXT = (
    "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.\n\n"
    "Перед тем как получить Папку лидера и практики, чуть-чуть формальностей:\n"
    "▪️ подтвердить согласие на обработку персональных данных.\n\n"
    "Сначала посмотрите документы по кнопкам ниже, затем нажмите «✅ Согласен/Согласна»."
)

AFTER_CONSENT_TEXT = (
    "Отлично. Напишите, пожалуйста, как к вам обращаться — ФИ."
)

AFTER_NAME_TEXT = (
    "Спасибо, {name}! Теперь мы с вами на связи.\n\n"
    "Чтобы получить материалы, нужно вступить в канал «Бизнес со смыслом» и подтвердить участие.\n\n"
    "1️⃣ Нажмите кнопку «Перейти в канал».\n"
    "2️⃣ Вступите в канал.\n"
    "3️⃣ Вернитесь в бот и нажмите «Я вступил(а)»."
)

AFTER_JOIN_OK_TEXT = (
    "Здорово! Telegram видит вас в канале «Бизнес со смыслом».\n\n"
    "Открываю доступ к материалам. Выберите раздел на клавиатуре ниже 👇"
)

AFTER_JOIN_FAIL_TEXT = (
    "Пока Telegram не видит вас в канале «Бизнес со смыслом».\n\n"
    "Проверьте, что вы действительно подписались, затем ещё раз нажмите «Я вступил(а)»."
)

LEADERS_FOLDER_TEXT = (
    "📂 Папка лидера\n\n"
    "Здесь собраны ключевые материалы, которые помогут навести порядок в управлении "
    "и двигаться к предсказуемому росту."
)

PRACTICE_CHOICE_TEXT = (
    "🧠 Практика дня\n\n"
    "Выберите практику на сегодня:"
)

PRACTICE_FOCUS_WHEEL_TEXT = (
    "🎯 Практика дня — Колесо фокуса\n\n"
    "Оцени по шкале от 1 до 10:\n"
    "• Стратегия\n"
    "• Команда\n"
    "• Деньги\n"
    "• Личное здоровье и ресурс\n\n"
    "Выбери сферу с минимальным баллом и сделай сегодня одно маленькое, "
    "но конкретное действие, которое поднимет её хотя бы на +1."
)

PRACTICE_MICRODELEGATION_TEXT = (
    "📤 Практика дня — Микроделегирование\n\n"
    "1️⃣ Выпиши 5 задач, которые забирают у тебя больше всего энергии, но не требуют твоей уникальной экспертизы.\n"
    "2️⃣ Выбери 1 задачу и передай её сотруднику, добавив понятный критерий результата и срок.\n"
    "3️⃣ Зафиксируй в календаре короткий слёт на проверку.\n\n"
    "Сфокусируйся сегодня на том, чтобы не «передумать и забрать обратно» 🙂"
)

PRACTICE_REALITY_TEXT = (
    "💡 Практика дня — «Откровение: точка реальности»\n\n"
    "Ответь честно письменно на три вопроса:\n"
    "1. Где я реально сейчас в бизнесе и в роли лидера?\n"
    "2. Чего я избегаю видеть или признавать?\n"
    "3. Какое одно признание изменит мои решения уже на этой неделе?\n\n"
    "Не ищи «правильный ответ» — ищи честный."
)

PRACTICE_MICROSTEP_TEXT = (
    "🚀 Практика дня — Микрошаг к Высшей траектории\n\n"
    "Представь себя через 2 года, когда бизнес работает более предсказуемо, а команда усиливает тебя.\n\n"
    "Запиши:\n"
    "1. Что в твоём дне обязательно присутствует?\n"
    "2. Чего в нём больше нет?\n"
    "3. Какой один шаг ты можешь сделать уже сегодня, чтобы приблизиться к этой картине?\n\n"
    "Сделай этот шаг до конца дня."
)

ABOUT_KARINA_TEXT = (
    "*Карина Конорева* — бизнес-архитектор, интегральный бизнес-психолог и коуч лидеров.\n\n"
    "*Опыт и роли:*\n"
    "• Профессиональный путь 20 лет — от преподавателя до предпринимателя.\n"
    "• Основатель компании «Высшая Траектория».\n"
    "• Автор проекта «Код Роста».\n"
    "• Спикер Всемирного Бизнес-форума 2025, внесённого в книгу рекордов страны и мира.\n"
    "• Победитель в номинации «HR-эксперт года» премии «Лидеры Эпохи 2024».\n"
    "• Лауреат Гран-При в конкурсе «Лучший по профессии» среди специалистов в области управления персоналом.\n"
    "• Бизнес-психолог, ментор управленческой зрелости, коуч лидеров и команд.\n"
    "• Эксперт по построению живых команд и системному росту бизнеса.\n"
    "• Член Академии социальных технологий и Российского общества «Знание».\n\n"
    "• 15+ лет опыта создания трансформационных программ для предпринимателей и лидеров.\n"
    "• Автор 26 статей в научных журналах и СМИ.\n"
    "• 250+ часов индивидуального и командного коучинга.\n\n"
    "*Образование:*\n"
    "• Высшее образование: психология, педагогика, философия.\n"
    "• Дополнительное образование: коучинг, бизнес, менеджмент, финансы.\n\n"
    "*Философия и подход:*\n"
    "• Создаю живые команды и системный рост бизнеса через лидеров нового типа.\n"
    "• Перевожу компании от хаотичного роста к управляемому развитию.\n"
    "• Фокус — не только на людях, но и на системе, где люди становятся источником устойчивого результата.\n"
    "• Каждый проект — баланс структуры и смысла, данных и энергии, цифр и человеческого потенциала.\n"
    "• Через этот бот вы получаете инструменты, которые помогают выйти из режима «герой-одиночка» "
    "и строить предсказуемый бизнес с опорой на команду."
)

UNKNOWN_TEXT = (
    "Пока я понимаю только команды из меню.\n"
    "Выберите нужный раздел на клавиатуре ниже."
)

# ===== БОТ И ДИСПЕТЧЕР ================================================

bot = Bot(TOKEN, parse_mode="Markdown")
dp = Dispatcher()


# ===== ХЕНДЛЕРЫ =======================================================

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()

    # Приветствие и описание формальностей
    await message.answer(WELCOME_TEXT)

    # Отправка документов
    try:
        await message.answer_document(FSInputFile(POLITIKA_FILE), caption="Политика конфиденциальности")
    except Exception as e:
        logging.warning(f"Не удалось отправить {POLITIKA_FILE}: {e}")

    try:
        await message.answer_document(FSInputFile(SOGLASIE_FILE), caption="Согласие на обработку персональных данных")
    except Exception as e:
        logging.warning(f"Не удалось отправить {SOGLASIE_FILE}: {e}")

    await message.answer(
        "Когда посмотрите документы, нажмите кнопку ниже, чтобы продолжить.",
        reply_markup=consent_kb(),
    )


@dp.callback_query(F.data == "consent_ok")
async def consent_ok(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(AFTER_CONSENT_TEXT)
    await state.set_state(Registration.waiting_for_name)


@dp.message(Registration.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    await state.clear()

    await message.answer(
        AFTER_NAME_TEXT.format(name=name),
        reply_markup=after_name_kb(),
    )


@dp.callback_query(F.data == "joined_channel")
async def joined_channel(callback: types.CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id

    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in {
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        }:
            await callback.message.answer(
                AFTER_JOIN_OK_TEXT,
                reply_markup=main_menu_kb(),
            )
        else:
            await callback.message.answer(AFTER_JOIN_FAIL_TEXT)
    except Exception as e:
        logging.warning(f"Ошибка при проверке подписки: {e}")
        await callback.message.answer(
            "Не удалось проверить подписку. Попробуйте ещё раз чуть позже."
        )


# --- Папка лидера -----------------------------------------------------

@dp.message(F.text == "📂 Папка лидера")
async def leaders_folder(message: types.Message):
    await message.answer(LEADERS_FOLDER_TEXT, reply_markup=leaders_folder_kb())


@dp.callback_query(F.data == "send_karta")
async def send_karta(callback: types.CallbackQuery):
    await callback.answer()
    try:
        await callback.message.answer_document(
            FSInputFile(KARTA_FILE),
            caption="Гайд «Карта управленческой зрелости»",
        )
    except Exception as e:
        logging.warning(f"Не удалось отправить {KARTA_FILE}: {e}")
        await callback.message.answer("Файл пока недоступен.")
        

@dp.callback_query(F.data == "send_checklist")
async def send_checklist(callback: types.CallbackQuery):
    await callback.answer()
    try:
        await callback.message.answer_document(
            FSInputFile(CHECKLIST_FILE),
            caption="Чек-лист зрелого лидера",
        )
    except Exception as e:
        logging.warning(f"Не удалось отправить {CHECKLIST_FILE}: {e}")
        await callback.message.answer("Файл пока недоступен.")


@dp.callback_query(F.data == "send_books")
async def send_books(callback: types.CallbackQuery):
    await callback.answer()
    try:
        await callback.message.answer_document(
            FSInputFile(BOOKS_FILE),
            caption="Подборка книг для лидеров",
        )
    except Exception as e:
        logging.warning(f"Не удалось отправить {BOOKS_FILE}: {e}")
        await callback.message.answer("Файл пока недоступен.")


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Вы в главном меню. Выберите раздел на клавиатуре ниже.",
        reply_markup=main_menu_kb(),
    )


# --- Практика дня -----------------------------------------------------

@dp.message(F.text == "🧠 Практика дня")
async def practice_day(message: types.Message):
    await message.answer(PRACTICE_CHOICE_TEXT, reply_markup=practice_menu_kb())


@dp.callback_query(F.data == "practice_menu")
async def show_practice_menu(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(PRACTICE_CHOICE_TEXT, reply_markup=practice_menu_kb())


@dp.callback_query(F.data == "practice_focus_wheel")
async def practice_focus_wheel(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        PRACTICE_FOCUS_WHEEL_TEXT, reply_markup=practice_back_kb()
    )


@dp.callback_query(F.data == "practice_microdelegation")
async def practice_microdelegation(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        PRACTICE_MICRODELEGATION_TEXT, reply_markup=practice_back_kb()
    )


@dp.callback_query(F.data == "practice_reality")
async def practice_reality(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        PRACTICE_REALITY_TEXT, reply_markup=practice_back_kb()
    )


@dp.callback_query(F.data == "practice_microstep")
async def practice_microstep(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        PRACTICE_MICROSTEP_TEXT, reply_markup=practice_back_kb()
    )


# --- О Карине ---------------------------------------------------------

@dp.message(F.text == "ℹ️ О Карине")
async def about_karina(message: types.Message):
    # Фото
    try:
        photo = FSInputFile(KARINA_PHOTO_FILE)
        await message.answer_photo(photo=photo)
    except Exception as e:
        logging.warning(f"Не удалось отправить фото {KARINA_PHOTO_FILE}: {e}")

    # Текст
    await message.answer(ABOUT_KARINA_TEXT, reply_markup=about_karina_kb())


# --- Консультация -----------------------------------------------------

@dp.message(F.text == "📍 Записаться на консультацию")
async def consultation(message: types.Message):
    await message.answer(
        "Чтобы записаться на консультацию, перейдите по ссылке:",
        reply_markup=consultation_kb(),
    )


# --- /version для проверки --------------------------------------------

@dp.message(Command("version"))
async def cmd_version(message: types.Message):
    await message.answer("VERSION: no-phone-email + full-practices-menu")


# --- Фолбек -----------------------------------------------------------

@dp.message()
async def unknown_message(message: types.Message):
    await message.answer(UNKNOWN_TEXT, reply_markup=main_menu_kb())


# ===== МАЛЕНЬКИЙ ВЕБ-СЕРВЕР ДЛЯ RENDER ===============================

async def handle_root(request):
    return web.Response(text="Vysshaya Traektoriya bot is running")


async def start_web_app():
    app = web.Application()
    app.router.add_get("/", handle_root)

    port = int(os.getenv("PORT", 8000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    # держим сервер живым
    while True:
        await asyncio.sleep(3600)


# ===== ЗАПУСК =========================================================

async def main():
    await asyncio.gather(
        dp.start_polling(bot),
        start_web_app(),
    )


if __name__ == "__main__":
    asyncio.run(main())
