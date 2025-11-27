import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ НАСТРОЙКИ ============

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN не задана")

# username канала и ссылка на канал
CHANNEL_USERNAME = "@businesskodrosta"
CHANNEL_LINK = "https://t.me/businesskodrosta"

# Ссылка на интерактивную тетрадь
TETRAD_URL = "https://tetrad-lidera.netlify.app/"

# Ссылка на форму записи на консультацию
CONSULT_LINK = "https://forms.yandex.ru/u/69178642068ff0624a625f20/"

# Имена файлов (НЕ МЕНЯТЬ)
PD_POLICY_FILE = "politika_konfidencialnosti.pdf"
PD_AGREEMENT_FILE = "soglasie_na_obrabotku_pd.pdf"
GUIDE_FILE = "karta_upravlencheskoy_zrelosti.pdf"
CHECKLIST_FILE = "checklist_zrelogo_lidera.pdf"
BOOKS_FILE = "podborca_knig_liderstvo.pdf"

# Фото Карина
KARINA_PHOTO_FILE = "KARINA_PHOTO_URL.jpg"


# ============ СОСТОЯНИЯ ============

class Onboarding(StatesGroup):
    waiting_for_agree = State()
    waiting_for_name = State()


# ============ КЛАВИАТУРЫ ============

def main_menu_kb() -> ReplyKeyboardMarkup:
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


def practices_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Колесо фокуса", callback_data="pr_focus")],
            [InlineKeyboardButton(text="📤 Микроделегирование", callback_data="pr_deleg")],
            [InlineKeyboardButton(text="💡 Откровение: точка реальности", callback_data="pr_reality")],
            [InlineKeyboardButton(text="🚀 Микрошаг к Высшей траектории", callback_data="pr_step")],
        ]
    )


def leader_folder_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📘 Открыть тетрадь лидера", url=TETRAD_URL)],
            [InlineKeyboardButton(text="📗 Гайд «Карта управленческой зрелости»",
                                  callback_data="open_guide")],
            [InlineKeyboardButton(text="📙 Чек-лист зрелого лидера",
                                  callback_data="open_checklist")],
            [InlineKeyboardButton(text="📚 Подборка книг для лидеров",
                                  callback_data="open_books")],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_menu")],
        ]
    )


def about_karina_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Перейти в канал «Бизнес со смыслом»",
                url=CHANNEL_LINK
            )],
            [InlineKeyboardButton(
                text="Записаться на консультацию",
                url=CONSULT_LINK
            )],
        ]
    )


def agree_pd_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен/Согласна", callback_data="agree_pd")]
        ]
    )


def join_channel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Перейти в канал «Бизнес со смыслом»",
                url=CHANNEL_LINK
            )],
            [InlineKeyboardButton(text="Я вступил(а)", callback_data="joined_channel")],
        ]
    )


# ============ ПРОВЕРКА ПОДПИСКИ ============

async def is_user_subscribed(bot: Bot, user_id: int) -> bool:
    """
    Проверяем, состоит ли пользователь в канале.
    """
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
    except TelegramBadRequest as e:
        # Ошибка типа "chat not found" и т.п.
        logger.error("BadRequest при проверке подписки: %s", e)
        return False
    except TelegramForbiddenError as e:
        # Если бота выгнали из канала или нет прав
        logger.error("Forbidden при проверке подписки: %s", e)
        return False
    except Exception as e:
        logger.error("Неизвестная ошибка при проверке подписки: %s", e)
        return False

    return member.status in {
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
    }


# ============ ХЕНДЛЕРЫ ============

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    /start — отправляем документы по ПД и просим подтвердить.
    Главное меню НЕ показываем.
    """
    await state.clear()
    await state.set_state(Onboarding.waiting_for_agree)

    welcome_text = (
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.\n\n"
        "Перед тем как получить Папку лидера и практики, чуть-чуть формальностей:\n"
        "▪️ подтвердить согласие на обработку персональных данных.\n\n"
        "Сначала посмотрите документы по кнопкам ниже, затем нажмите «✅ Согласен/Согласна»."
    )

    await message.answer(welcome_text, reply_markup=types.ReplyKeyboardRemove())

    # Отправляем два PDF-документа
    await message.answer_document(
        FSInputFile(PD_POLICY_FILE),
        caption="Политика конфиденциальности",
    )

    await message.answer_document(
        FSInputFile(PD_AGREEMENT_FILE),
        caption="Согласие на обработку персональных данных",
    )

    await message.answer(
        "Когда посмотрите документы, нажмите кнопку ниже, чтобы продолжить.",
        reply_markup=agree_pd_kb(),
    )


@dp.message(Onboarding.waiting_for_agree)
async def wait_agree(message: Message):
    """
    Пользователь пишет что-то до того, как нажал «Согласен/Согласна».
    Меню не показываем, мягко возвращаем к шагу.
    """
    await message.answer(
        "Пожалуйста, сначала посмотрите документы и нажмите кнопку «✅ Согласен/Согласна» под ними."
    )


@dp.callback_query(F.data == "agree_pd")
async def on_agree_pd(callback: CallbackQuery, state: FSMContext):
    """
    Пользователь нажал «Согласен/Согласна» — просим имя.
    """
    await state.set_state(Onboarding.waiting_for_name)
    await callback.message.answer(
        "Отлично. Напишите, пожалуйста, как к вам обращаться — ФИ."
    )
    await callback.answer()


@dp.message(Onboarding.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    """
    Получаем имя и отправляем инструкцию по вступлению в канал.
    """
    name = (message.text or "").strip()
    if not name:
        await message.answer("Пожалуйста, напишите, как к вам обращаться — ФИ.")
        return

    await state.clear()

    text = (
        f"Спасибо, {name}! Теперь мы с вами на связи.\n\n"
        "Чтобы получить материалы, нужно вступить в канал «Бизнес со смыслом» "
        "и подтвердить участие.\n\n"
        "1️⃣ Нажмите кнопку «Перейти в канал».\n"
        "2️⃣ Вступите в канал.\n"
        "3️⃣ Вернитесь в бот и нажмите «Я вступил(а)»."
    )

    await message.answer(text, reply_markup=join_channel_kb())


@dp.callback_query(F.data == "joined_channel")
async def on_joined_channel(callback: CallbackQuery, bot: Bot):
    """
    Обработка нажатия «Я вступил(а)» — проверяем подписку.
    Если всё ок, показываем главное меню.
    """
    user_id = callback.from_user.id

    is_member = await is_user_subscribed(bot, user_id)

    if not is_member:
        # Показываем алерт, меню НЕ выдаём
        await callback.answer(
            "Не удалось проверить подписку или вы ещё не вступили в канал. "
            "Проверьте, что вы действительно подписались, и попробуйте ещё раз.",
            show_alert=True,
        )
        return

    # Убираем старую инлайн-клавиатуру
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    await callback.message.answer(
        "Отлично! Доступ к материалам открыт. Ниже появилось главное меню 👇",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


# ---------- ПАПКА ЛИДЕРА ----------

@dp.message(F.text == "📁 Папка лидера")
async def folder_handler(message: Message):
    text = (
        "Здесь собраны ключевые материалы, которые помогают навести порядок в управлении "
        "и двигаться к предсказуемому росту."
    )
    await message.answer(text, reply_markup=leader_folder_kb())


@dp.callback_query(F.data == "open_guide")
async def send_guide(callback: CallbackQuery):
    await callback.message.answer_document(
        FSInputFile(GUIDE_FILE),
        caption="Гайд «Карта управленческой зрелости»",
    )
    await callback.answer()


@dp.callback_query(F.data == "open_checklist")
async def send_checklist(callback: CallbackQuery):
    await callback.message.answer_document(
        FSInputFile(CHECKLIST_FILE),
        caption="Чек-лист зрелого лидера",
    )
    await callback.answer()


@dp.callback_query(F.data == "open_books")
async def send_books(callback: CallbackQuery):
    await callback.message.answer_document(
        FSInputFile(BOOKS_FILE),
        caption="Подборка книг для лидеров",
    )
    await callback.answer()


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.answer(
        "Вы вернулись в главное меню.", reply_markup=main_menu_kb()
    )
    await callback.answer()


# ---------- ПРАКТИКА ДНЯ ----------

@dp.message(F.text == "🧠 Практика дня")
async def practice_menu(message: Message):
    await message.answer(
        "Выбери практику на сегодня:", reply_markup=practices_menu_kb()
    )


async def send_practice_text(callback: CallbackQuery, title: str, body: str):
    kb_back = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ К другим практикам", callback_data="back_to_practices")]
        ]
    )
    await callback.message.answer(f"🎯 Практика дня — {title}\n\n{body}", reply_markup=kb_back)
    await callback.answer()


@dp.callback_query(F.data == "back_to_practices")
async def back_to_practices(callback: CallbackQuery):
    await callback.message.answer(
        "Выбери практику на сегодня:", reply_markup=practices_menu_kb()
    )
    await callback.answer()


@dp.callback_query(F.data == "pr_focus")
async def pr_focus(callback: CallbackQuery):
    body = (
        "Оцени по шкале от 1 до 10:\n"
        "• Стратегия\n"
        "• Команда\n"
        "• Деньги\n"
        "• Личное здоровье и ресурс\n\n"
        "Выбери сферу с минимальным баллом и сделай сегодня одно маленькое, "
        "но конкретное действие, которое поднимет её хотя бы на +1."
    )
    await send_practice_text(callback, "Колесо фокуса", body)


@dp.callback_query(F.data == "pr_deleg")
async def pr_deleg(callback: CallbackQuery):
    body = (
        "Вспомни одну задачу, которую ты всё ещё делаешь сам(а), "
        "хотя её можно передать.\n\n"
        "1️⃣ Определи, кому в команде она ближе всего по зоне ответственности.\n"
        "2️⃣ Сформулируй ожидаемый результат и критерии успеха.\n"
        "3️⃣ Передай задачу и назначь контрольную точку.\n\n"
        "Вечером зафиксируй, что получилось и что можно улучшить в следующей передаче."
    )
    await send_practice_text(callback, "Микроделегирование", body)


@dp.callback_query(F.data == "pr_reality")
async def pr_reality(callback: CallbackQuery):
    body = (
        "Ответь честно на три вопроса:\n"
        "1. Что в моём бизнесе сейчас работает хуже всего?\n"
        "2. Какую цену я плачу за то, что это долго не решаю?\n"
        "3. Какой первый шаг я могу сделать в течение 48 часов?\n\n"
        "Запиши ответы и выбери один конкретный шаг — сделай его сегодня."
    )
    await send_practice_text(callback, "Откровение: точка реальности", body)


@dp.callback_query(F.data == "pr_step")
async def pr_step(callback: CallbackQuery):
    body = (
        "Представь свою «Высшую траекторию» на год вперёд: каким ты хочешь видеть бизнес и себя?\n\n"
        "Теперь сформулируй один микрошаг, который приблизит тебя к этой картинке "
        "на 1% уже сегодня. Сделай его и зафиксируй результат в тетради лидера."
    )
    await send_practice_text(callback, "Микрошаг к Высшей траектории", body)


# ---------- О КАРИНЕ ----------

@dp.message(F.text == "ℹ️ О Карине")
async def about_karina(message: Message):
    caption = (
        "Карина Конорева — бизнес-архитектор, интегральный бизнес-психолог и коуч лидеров.\n\n"
        "Помогаю собственникам выходить из режима «героя-одиночки» и строить предсказуемый "
        "бизнес с опорой на живую, сильную команду.\n\n"
        "Через этот бот вы получаете практические инструменты, которые помогают навести порядок "
        "в управлении, выстроить команду и двигаться к устойчивому росту."
    )

    await message.answer_photo(
        FSInputFile(KARINA_PHOTO_FILE),
        caption=caption,
        reply_markup=about_karina_kb(),
    )


# ---------- ЗАПИСЬ НА КОНСУЛЬТАЦИЮ ----------

@dp.message(F.text == "📍 Записаться на консультацию")
async def consult_handler(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Перейти к форме записи",
                url=CONSULT_LINK,
            )]
        ]
    )
    await message.answer(
        "Чтобы записаться на консультацию, перейдите по ссылке:",
        reply_markup=kb,
    )


# ---------- ЛЮБОЙ ДРУГОЙ ТЕКСТ (ПОСЛЕ ОНБОРДИНГА) ----------

@dp.message()
async def fallback(message: Message):
    """
    Любой текст вне онбординга.
    """
    await message.answer(
        "Пока я понимаю только команды из меню. "
        "Выберите нужный раздел на клавиатуре ниже или введите /start.",
        reply_markup=main_menu_kb(),
    )


# ============ ЗАПУСК ============

async def main():
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
