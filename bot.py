import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F, types
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
from aiogram.enums import ChatMemberStatus, ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.client.default import DefaultBotProperties


logging.basicConfig(level=logging.INFO)

# ================== НАСТРОЙКИ ==================

TOKEN = os.getenv("BOT_TOKEN")

# Точный @ канала, где бот ДОБАВЛЕН АДМИНОМ
CHANNEL_USERNAME = "@businesskodrosta"
# Ссылка-приглашение в канал (кнопка «Перейти в канал»)
CHANNEL_LINK = "https://t.me/businesskodrosta"

# Ссылка на интерактивную тетрадь
TETRAD_URL = "https://tetrad-lidera.netlify.app/"

# ИМЕНА ЛОКАЛЬНЫХ ФАЙЛОВ (они должны лежать рядом с bot.py на Render)
PD_POLICY_PATH = "politika_konfidencialnosti.pdf"
PD_AGREEMENT_PATH = "soglasie_na_obrabotku_pd.pdf"

GUIDE_PATH = "karta_upravlencheskoy_zrelosti.pdf"
CHECKLIST_PATH = "checklist_zrelogo_lidera.pdf"
BOOKS_PATH = "podborca_knig_liderstvo.pdf"

# Фото Карины (локальный файл)
KARINA_PHOTO_PATH = "KARINA_PHOTO_URL.jpg"

# Форма на консультацию
CONSULT_LINK = "https://forms.yandex.ru/..."  # <-- подставь свою ссылку

# ================== СОСТОЯНИЯ ==================


class Form(StatesGroup):
    waiting_for_agreement = State()
    waiting_for_name = State()
    waiting_for_subscription = State()
    main_menu = State()


# ================== ОБЪЕКТЫ БОТА ==================

bot = Bot(
    TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher()


# ================== ВСПОМОГАТЕЛЬНЫЕ КЛАВИАТУРЫ ==================


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Главное меню после подтверждения подписки."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📁 Папка лидера")],
            [KeyboardButton(text="🧠 Практика дня")],
            [
                KeyboardButton(text="ℹ️ О Карине"),
                KeyboardButton(text="📍 Записаться на консультацию"),
            ],
        ],
        resize_keyboard=True,
    )


def practices_kb() -> InlineKeyboardMarkup:
    """Список практик дня."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Колесо фокуса", callback_data="p_focus")],
            [InlineKeyboardButton(text="📤 Микроделегирование", callback_data="p_microdeleg")],
            [InlineKeyboardButton(text="💡 Откровение: точка реальности", callback_data="p_reality")],
            [InlineKeyboardButton(text="🚀 Микрошаг к Высшей траектории", callback_data="p_microstep")],
        ]
    )


def back_to_practices_kb() -> InlineKeyboardMarkup:
    """Кнопка возврата к списку практик."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ К другим практикам", callback_data="back_to_practices")]
        ]
    )


# ================== ТЕКСТЫ ==================

ABOUT_TEXT = """
Карина Конорева — бизнес-архитектор, интегральный бизнес-психолог и коуч лидеров.

Помогаю собственникам выходить из режима «героя-одиночки» и строить предсказуемый бизнес с опорой на команду.

• Профессиональный путь более 20 лет — от преподавателя до предпринимателя.
• Основатель компании «Высшая Траектория».
• Автор проекта «Бизнес-маршруты со смыслом» для лидеров и команд.
• Победитель премии «Лидеры Эпохи 2024» в номинации «HR-эксперт года».
• Лауреат Гран-при «Лучший по профессии» в управлении персоналом.
• 26 статей в научных журналах и СМИ.
• 250+ часов индивидуального и командного коучинга.

ФИЛОСОФИЯ
Создаю живые команды и системный рост бизнеса через лидеров нового типа.
Фокус — не только на людях, но и на системе, где люди становятся источником устойчивого результата.

Через этот бот вы получаете практические инструменты, которые помогают выйти из режима «герой-одиночка» и строить предсказуемый бизнес с опорой на команду.
""".strip()


# ================== ПРОВЕРКА ПОДПИСКИ ==================


async def is_subscribed(user_id: int) -> bool:
    """
    Проверка подписки на канал.
    ВАЖНО: бот должен быть админом в CHANNEL_USERNAME.
    """
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
    except TelegramForbiddenError:
        logging.warning("Бот не имеет прав на канал %s", CHANNEL_USERNAME)
        return False
    except TelegramBadRequest:
        logging.warning("Проблема с CHANNEL_USERNAME = %s", CHANNEL_USERNAME)
        return False

    return member.status in {
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    }


# ================== /start ==================


@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()

    # Прячем меню, чтобы не светилось заранее
    await message.answer(
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.",
        reply_markup=ReplyKeyboardRemove(),
    )

    text = (
        "Перед тем как получить Папку лидера и практики, чуть-чуть формальностей:\n"
        "▪️ подтвердить согласие на обработку персональных данных.\n\n"
        "Сначала посмотрите документы по кнопкам ниже, затем нажмите «✅ Согласен/Согласна»."
    )
    await message.answer(text)

    # Отправляем два PDF с ПД
    await message.answer_document(
        types.FSInputFile(PD_POLICY_PATH),
        caption="Политика конфиденциальности",
    )
    await message.answer_document(
        types.FSInputFile(PD_AGREEMENT_PATH),
        caption="Согласие на обработку персональных данных",
    )

    agree_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен/Согласна", callback_data="agree_pd")]
        ]
    )
    await message.answer(
        "Когда посмотрите документы, нажмите кнопку ниже, чтобы продолжить.",
        reply_markup=agree_kb,
    )

    await state.set_state(Form.waiting_for_agreement)


# ================== СОГЛАСИЕ НА ПД ==================


@dp.callback_query(F.data == "agree_pd", Form.waiting_for_agreement)
async def agree_pd(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Отлично. Напишите, пожалуйста, как к вам обращаться — ФИ.")
    await state.set_state(Form.waiting_for_name)


# ================== ИМЯ ПОЛЬЗОВАТЕЛЯ ==================


@dp.message(Form.waiting_for_name)
async def save_name(message: types.Message, state: FSMContext):
    full_name = message.text.strip()
    await state.update_data(full_name=full_name)

    text = (
        f"Спасибо, {full_name}! Теперь мы с вами на связи.\n\n"
        "Чтобы получить материалы, нужно вступить в канал «Бизнес со смыслом» и подтвердить участие:\n\n"
        "1️⃣ Нажмите кнопку «Перейти в канал».\n"
        "2️⃣ Вступите в канал.\n"
        "3️⃣ Вернитесь в бот и нажмите «Я вступил(а)»."
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перейти в канал «Бизнес со смыслом»",
                    url=CHANNEL_LINK,
                )
            ],
            [
                InlineKeyboardButton(
                    text="Я вступил(а)",
                    callback_data="joined_channel",
                )
            ],
        ]
    )

    await message.answer(text, reply_markup=kb)
    await state.set_state(Form.waiting_for_subscription)


# ================== ПРОВЕРКА ПОДПИСКИ ==================


@dp.callback_query(F.data == "joined_channel", Form.waiting_for_subscription)
async def joined_channel(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id

    if not await is_subscribed(user_id):
        await callback.message.answer(
            "Пока Telegram не видит вас в канале.\n"
            "Убедитесь, что вы подписаны именно на канал «Бизнес со смыслом» "
            "и попробуйте ещё раз чуть позже."
        )
        return

    await callback.message.answer(
        "Отлично! Доступ к материалам открыт. Выберите раздел в меню ниже 👇",
        reply_markup=main_menu_kb(),
    )
    await state.set_state(Form.main_menu)


# ================== ПАПКА ЛИДЕРА ==================


@dp.message(F.text == "📁 Папка лидера", Form.main_menu)
async def folder_leader(message: types.Message):
    text = (
        "📂 *Папка лидера*\n\n"
        "Здесь собраны ключевые материалы, которые помогают навести порядок "
        "в управлении и двигаться к предсказуемому росту."
    )

    kb = InlineKeyboardMarkup(
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
                    callback_data="open_guide",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📙 Чек-лист зрелого лидера",
                    callback_data="open_checklist",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Подборка книг для лидеров",
                    callback_data="open_books",
                )
            ],
        ]
    )

    await message.answer(text, reply_markup=kb)


@dp.callback_query(F.data == "open_guide")
async def send_guide(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer_document(
        types.FSInputFile(GUIDE_PATH),
        caption="Гайд «Карта управленческой зрелости»",
    )


@dp.callback_query(F.data == "open_checklist")
async def send_checklist(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer_document(
        types.FSInputFile(CHECKLIST_PATH),
        caption="Чек-лист зрелого лидера",
    )


@dp.callback_query(F.data == "open_books")
async def send_books(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer_document(
        types.FSInputFile(BOOKS_PATH),
        caption="Подборка книг для лидеров",
    )


# ================== ПРАКТИКА ДНЯ ==================


@dp.message(F.text == "🧠 Практика дня", Form.main_menu)
async def practice_day(message: types.Message):
    await message.answer("Выбери практику на сегодня:", reply_markup=practices_kb())


@dp.callback_query(F.data == "back_to_practices")
async def back_to_practices(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Выбери практику на сегодня:", reply_markup=practices_kb()
    )


@dp.callback_query(F.data == "p_focus")
async def practice_focus(callback: types.CallbackQuery):
    await callback.answer()
    text = (
        "🎯 *Практика дня — Колесо фокуса*\n\n"
        "Оцени по шкале от 1 до 10:\n"
        "• Стратегия\n"
        "• Команда\n"
        "• Деньги\n"
        "• Личное здоровье и ресурс\n\n"
        "Выбери сферу с минимальным баллом и сделай сегодня одно маленькое, "
        "но конкретное действие, которое поднимет её хотя бы на +1."
    )
    await callback.message.answer(text, reply_markup=back_to_practices_kb())


@dp.callback_query(F.data == "p_microdeleg")
async def practice_microdeleg(callback: types.CallbackQuery):
    await callback.answer()
    text = (
        "📤 *Практика дня — Микроделегирование*\n\n"
        "1. Выпиши 5 задач, которые ты делаешь сам(а), но их можно поручить другим.\n"
        "2. Выбери одну самую безопасную и простую.\n"
        "3. Передай её человеку из команды с понятным критерием результата и сроком.\n"
        "4. Отслеживай не идеальность, а факт передачи — это уже шаг к разгрузке."
    )
    await callback.message.answer(text, reply_markup=back_to_practices_kb())


@dp.callback_query(F.data == "p_reality")
async def practice_reality(callback: types.CallbackQuery):
    await callback.answer()
    text = (
        "💡 *Практика дня — Откровение: точка реальности*\n\n"
        "Ответь честно на 3 вопроса:\n"
        "1) Где я сейчас как лидер по шкале от 1 до 10?\n"
        "2) Что в моей управленческой привычке мешает расти компании?\n"
        "3) Какое одно решение я могу принять уже сегодня, чтобы перестать тормозить рост?\n\n"
        "Запиши ответы и вернись к ним через неделю."
    )
    await callback.message.answer(text, reply_markup=back_to_practices_kb())


@dp.callback_query(F.data == "p_microstep")
async def practice_microstep(callback: types.CallbackQuery):
    await callback.answer()
    text = (
        "🚀 *Практика дня — Микрошаг к Высшей траектории*\n\n"
        "Представь свою компанию через 3 года, если всё сложится оптимально.\n"
        "• Как выглядит команда?\n"
        "• Как выглядит твоя роль?\n"
        "• Какие ключевые решения уже приняты?\n\n"
        "Теперь выбери один микрошаг, который можно сделать за 15–30 минут сегодня, "
        "чтобы приблизиться к этой картинке. И сделай его в ближайшие 24 часа."
    )
    await callback.message.answer(text, reply_markup=back_to_practices_kb())


# ================== О КАРИНЕ ==================


@dp.message(F.text == "ℹ️ О Карине", Form.main_menu)
async def about_karina(message: types.Message):
    await message.answer_photo(
        types.FSInputFile(KARINA_PHOTO_PATH),
        caption="Карина Конорева — бизнес-архитектор, интегральный бизнес-психолог и коуч лидеров.",
    )

    kb = InlineKeyboardMarkup(
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

    await message.answer(ABOUT_TEXT, reply_markup=kb)


# ================== ЗАПИСЬ НА КОНСУЛЬТАЦИЮ ==================


@dp.message(F.text == "📍 Записаться на консультацию", Form.main_menu)
async def consult(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перейти к форме записи",
                    url=CONSULT_LINK,
                )
            ]
        ]
    )
    await message.answer(
        "Чтобы записаться на консультацию, перейдите по ссылке ниже:",
        reply_markup=kb,
    )


# ================== НЕИЗВЕСТНЫЕ СООБЩЕНИЯ ==================


@dp.message()
async def unknown_message(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == Form.main_menu.state:
        await message.answer(
            "Пока я понимаю только команды из меню. "
            "Выберите нужный раздел на клавиатуре ниже 👇"
        )
    else:
        await message.answer(
            "Чтобы продолжить работу, используйте кнопки или введите команду /start."
        )


# ================== ЗАПУСК ==================


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
