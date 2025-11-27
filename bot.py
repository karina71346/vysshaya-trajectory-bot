import os
import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    FSInputFile,
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# ---------------------------------------------------------------------------
# НАСТРОЙКИ
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN не задана")

# Канал
CHANNEL_USERNAME = "@businesskodrosta"
CHANNEL_LINK = "https://t.me/businesskodrosta"

# Ссылки
TETRAD_URL = "https://tetrad-lidera.netlify.app/"
CONSULT_LINK = "https://forms.yandex.ru/u/69178642068ff0624a625f20/"

# Файлы (должны лежать рядом с bot.py)
BASE_DIR = Path(__file__).parent

POLICY_FILE = BASE_DIR / "politika_konfidencialnosti.pdf"
CONSENT_FILE = BASE_DIR / "soglasie_na_obrabotku_pd.pdf"

GUIDE_FILE = BASE_DIR / "karta_upravlencheskoy_zrelosti.pdf"
CHECKLIST_FILE = BASE_DIR / "checklist_zrelogo_lidera.pdf"
BOOKS_FILE = BASE_DIR / "podborca_knig_liderstvo.pdf"

KARINA_PHOTO_FILE = BASE_DIR / "KARINA_PHOTO_URL.jpg"

# Текст о Карине (можно править только здесь)
ABOUT_KARINA_TEXT = (
    "Карина Конорева — бизнес-архитектор, интегральный бизнес-психолог и коуч лидеров.\n\n"
    "Помогаю собственникам выходить из режима «героя-одиночки» и строить предсказуемый бизнес "
    "с опорой на живую, сильную команду.\n\n"
    "• 18+ лет практики в роли интегрального бизнес-психолога\n"
    "• 15+ лет опыта в развитии персонала и бизнес-процессов\n"
    "• 10 лет управленческого опыта на позиции HRD\n"
    "• Автор 26 статей в научных журналах и СМИ\n"
    "• 250+ часов индивидуального и командного коучинга\n\n"
    "Через этот бот вы получаете практические инструменты, которые помогают выйти из режима "
    "«герой-одиночка» и строить предсказуемый, устойчивый бизнес с опорой на команду."
)

# ---------------------------------------------------------------------------
# СОСТОЯНИЯ И ПАМЯТЬ
# ---------------------------------------------------------------------------


class Onboarding(StatesGroup):
    waiting_for_agree = State()
    waiting_for_name = State()


# Простая in-memory «база», отмечаем прошёл человек онбординг или нет
onboarded_users: dict[int, bool] = {}


def is_onboarded(user_id: int) -> bool:
    return onboarded_users.get(user_id, False)


def set_onboarded(user_id: int, value: bool = True) -> None:
    onboarded_users[user_id] = value


# ---------------------------------------------------------------------------
# КЛАВИАТУРЫ
# ---------------------------------------------------------------------------

def kb_agree_pd() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен/Согласна", callback_data="agree_pd")]
        ]
    )


def kb_join_channel() -> InlineKeyboardMarkup:
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
                    text="Я вступил(а)", callback_data="joined_channel"
                )
            ],
        ]
    )


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


def kb_leader_folder() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📘 Открыть тетрадь лидера", url=TETRAD_URL
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
            [
                InlineKeyboardButton(
                    text="⬅️ В главное меню", callback_data="back_to_menu"
                )
            ],
        ]
    )


def kb_practices() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Колесо фокуса", callback_data="pr_focus")],
            [
                InlineKeyboardButton(
                    text="📤 Микроделегирование", callback_data="pr_deleg"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💡 Откровение: точка реальности",
                    callback_data="pr_reality",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚀 Микрошаг к Высшей траектории",
                    callback_data="pr_step",
                )
            ],
        ]
    )


def kb_back_to_practices() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ К другим практикам", callback_data="back_to_practices"
                )
            ]
        ]
    )


def kb_about_karina() -> InlineKeyboardMarkup:
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
                    text="Записаться на консультацию", url=CONSULT_LINK
                )
            ],
        ]
    )


def kb_consultation() -> InlineKeyboardMarkup:
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


# ---------------------------------------------------------------------------
# РОУТЕР
# ---------------------------------------------------------------------------

router = Router()


# ---------------------------------------------------------------------------
# /START — ОНБОРДИНГ
# ---------------------------------------------------------------------------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    set_onboarded(user_id, False)
    await state.clear()

    # убираем клавиатуру, если была
    await message.answer(
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.",
        reply_markup=ReplyKeyboardRemove(),
    )

    text = (
        "Перед тем как получить Папку лидера и практики, чуть-чуть формальностей:\n"
        "▪️ подтвердить согласие на обработку персональных данных.\n\n"
        "Сначала посмотрите документы по кнопкам ниже, затем нажмите "
        "кнопку «✅ Согласен/Согласна»."
    )
    await message.answer(text)

    # отправляем два PDF
    try:
        await message.answer_document(
            document=FSInputFile(POLICY_FILE),
            caption="Политика конфиденциальности",
        )
        await message.answer_document(
            document=FSInputFile(CONSENT_FILE),
            caption="Согласие на обработку персональных данных",
        )
    except Exception as e:
        logging.exception("Не удалось отправить документы по ПД: %s", e)
        await message.answer(
            "Не удалось отправить документы. Если проблема повторяется, напишите Карине напрямую."
        )

    await message.answer(
        "Когда посмотрите документы, нажмите кнопку ниже, чтобы продолжить.",
        reply_markup=kb_agree_pd(),
    )

    await state.set_state(Onboarding.waiting_for_agree)


@router.callback_query(F.data == "agree_pd")
async def cb_agree_pd(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Onboarding.waiting_for_name)
    await callback.message.answer(
        "Отлично. Напишите, пожалуйста, как к вам обращаться — ФИ."
    )


@router.message(Onboarding.waiting_for_name)
async def process_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer(
            "Напишите, пожалуйста, как к вам обращаться — хотя бы имя 🙂"
        )
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

    await message.answer(text, reply_markup=kb_join_channel())


@router.callback_query(F.data == "joined_channel")
async def cb_joined_channel(
    callback: CallbackQuery, bot: Bot
) -> None:
    user_id = callback.from_user.id

    try:
        member = await bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id,
        )
        status = member.status
    except Exception as e:
        logging.exception("Не удалось проверить подписку: %s", e)
        await callback.answer(
            "Не удалось проверить подписку. Проверьте, что бот добавлен в канал и попробуйте позже.",
            show_alert=True,
        )
        return

    if status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
    ):
        set_onboarded(user_id, True)
        await callback.answer("Подписка подтверждена!", show_alert=False)

        # убираем кнопки «Перейти в канал / Я вступил(а)»
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

        await callback.message.answer(
            "Отлично! Доступ к материалам открыт. Ниже появилось главное меню 👇",
            reply_markup=main_menu_kb(),
        )
    else:
        await callback.answer(
            "Телеграм пока не видит вас среди подписчиков.\n"
            "Проверьте, что вы вступили в канал, и попробуйте ещё раз.",
            show_alert=True,
        )


# ---------------------------------------------------------------------------
# ХЕЛПЕР: ПРОВЕРКА ОНБОРДИНГА
# ---------------------------------------------------------------------------

async def ensure_onboarded(message: Message) -> bool:
    """
    Возвращает True, если пользователь прошёл онбординг.
    Если нет — подсказывает, что делать, и возвращает False.
    """
    user_id = message.from_user.id
    if is_onboarded(user_id):
        return True

    await message.answer(
        "Чтобы получить доступ к материалам, сначала пройдите короткий ввод.\n"
        "Нажмите /start и следуйте шагам."
    )
    return False


# ---------------------------------------------------------------------------
# ГЛАВНОЕ МЕНЮ — ПАПКА ЛИДЕРА
# ---------------------------------------------------------------------------

@router.message(F.text == "📁 Папка лидера")
async def menu_leader_folder(message: Message) -> None:
    if not await ensure_onboarded(message):
        return

    text = (
        "Здесь собраны ключевые материалы, которые помогают навести порядок "
        "в управлении и двигаться к предсказуемому росту."
    )
    await message.answer(text, reply_markup=kb_leader_folder())


@router.callback_query(F.data == "open_guide")
async def cb_open_guide(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        await callback.message.answer_document(
            document=FSInputFile(GUIDE_FILE),
            caption="Гайд «Карта управленческой зрелости»",
        )
    except Exception as e:
        logging.exception("Ошибка при отправке гайда: %s", e)
        await callback.message.answer(
            "Файл гайда временно недоступен. Попробуйте позже."
        )


@router.callback_query(F.data == "open_checklist")
async def cb_open_checklist(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        await callback.message.answer_document(
            document=FSInputFile(CHECKLIST_FILE),
            caption="Чек-лист зрелого лидера",
        )
    except Exception as e:
        logging.exception("Ошибка при отправке чек-листа: %s", e)
        await callback.message.answer(
            "Файл чек-листа временно недоступен. Попробуйте позже."
        )


@router.callback_query(F.data == "open_books")
async def cb_open_books(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        await callback.message.answer_document(
            document=FSInputFile(BOOKS_FILE),
            caption="Подборка книг для лидеров",
        )
    except Exception as e:
        logging.exception("Ошибка при отправке подборки книг: %s", e)
        await callback.message.answer(
            "Файл с подборкой книг временно недоступен. Попробуйте позже."
        )


@router.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Вы вернулись в главное меню.", reply_markup=main_menu_kb()
    )


# ---------------------------------------------------------------------------
# ГЛАВНОЕ МЕНЮ — ПРАКТИКА ДНЯ
# ---------------------------------------------------------------------------

@router.message(F.text == "🧠 Практика дня")
async def menu_practice_of_day(message: Message) -> None:
    if not await ensure_onboarded(message):
        return

    await message.answer(
        "Выбери практику на сегодня:", reply_markup=kb_practices()
    )


@router.callback_query(F.data == "back_to_practices")
async def cb_back_to_practices(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Выбери практику на сегодня:", reply_markup=kb_practices()
    )


@router.callback_query(F.data == "pr_focus")
async def cb_pr_focus(callback: CallbackQuery) -> None:
    await callback.answer()
    text = (
        "🎯 Практика дня — Колесо фокуса\n\n"
        "Оцени по шкале от 1 до 10:\n"
        "• Стратегия\n"
        "• Команда\n"
        "• Деньги\n"
        "• Личное здоровье и ресурс\n\n"
        "Выбери сферу с минимальным баллом и сделай сегодня одно маленькое, "
        "но конкретное действие, которое поднимет её хотя бы на +1."
    )
    await callback.message.answer(text, reply_markup=kb_back_to_practices())


@router.callback_query(F.data == "pr_deleg")
async def cb_pr_deleg(callback: CallbackQuery) -> None:
    await callback.answer()
    text = (
        "📤 Практика дня — Микроделегирование\n\n"
        "Выпиши 3 задачи, которые вы регулярно делаете сами, хотя их мог бы "
        "делать кто-то из команды.\n\n"
        "Выбери одну задачу и передай её сегодня: обозначь ожидаемый результат, "
        "критерии и срок. Вечером зафиксируй, что сработало, а что улучшить "
        "в следующем делегировании."
    )
    await callback.message.answer(text, reply_markup=kb_back_to_practices())


@router.callback_query(F.data == "pr_reality")
async def cb_pr_reality(callback: CallbackQuery) -> None:
    await callback.answer()
    text = (
        "💡 Практика дня — Откровение: точка реальности\n\n"
        "Ответь честно на три вопроса:\n"
        "1) Что в управлении я откладываю уже больше месяца?\n"
        "2) Какую цену за это платит мой бизнес и команда?\n"
        "3) Какой один разговор или решение я могу сделать сегодня, "
        "чтобы сдвинуть ситуацию хотя бы на 10%?\n\n"
        "Запиши ответы и сделай этот один шаг."
    )
    await callback.message.answer(text, reply_markup=kb_back_to_practices())


@router.callback_query(F.data == "pr_step")
async def cb_pr_step(callback: CallbackQuery) -> None:
    await callback.answer()
    text = (
        "🚀 Практика дня — Микрошаг к Высшей траектории\n\n"
        "Представь свой бизнес через 3 года: как выглядит команда, "
        "система управления и твоя роль?\n\n"
        "Выбери один элемент из этого образа (например, регулярные стратегические "
        "сессии, сильный зам, прозрачная отчётность) и запиши один микрошаг, "
        "который ты можешь сделать в течение ближайших 24 часов, чтобы стать к "
        "этому на шаг ближе."
    )
    await callback.message.answer(text, reply_markup=kb_back_to_practices())


# ---------------------------------------------------------------------------
# ГЛАВНОЕ МЕНЮ — О КАРИНЕ
# ---------------------------------------------------------------------------

@router.message(F.text == "ℹ️ О Карине")
async def menu_about_karina(message: Message) -> None:
    if not await ensure_onboarded(message):
        return

    # сначала фото, потом текст с кнопками
    try:
        await message.answer_photo(
            photo=FSInputFile(KARINA_PHOTO_FILE),
            caption=ABOUT_KARINA_TEXT,
            reply_markup=kb_about_karina(),
        )
    except Exception as e:
        logging.exception("Ошибка при отправке фото Карины: %s", e)
        await message.answer(ABOUT_KARINA_TEXT, reply_markup=kb_about_karina())


# ---------------------------------------------------------------------------
# ГЛАВНОЕ МЕНЮ — ЗАПИСАТЬСЯ НА КОНСУЛЬТАЦИЮ
# ---------------------------------------------------------------------------

@router.message(F.text == "📍 Записаться на консультацию")
async def menu_consultation(message: Message) -> None:
    if not await ensure_onboarded(message):
        return

    text = "Чтобы записаться на консультацию, перейдите по ссылке:"
    await message.answer(text, reply_markup=kb_consultation())


# ---------------------------------------------------------------------------
# ПРОЧИЙ ТЕКСТ
# ---------------------------------------------------------------------------

@router.message()
async def fallback(message: Message) -> None:
    # если человек не прошёл онбординг — возвращаем к /start
    if not is_onboarded(message.from_user.id):
        await message.answer(
            "Пока я понимаю только команды из меню онбординга.\n"
            "Нажмите /start и пройдите короткий путь подключения."
        )
        return

    # если онбординг пройден — подсказываем про меню
    await message.answer(
        "Пока я понимаю только команды из меню. "
        "Выберите нужный раздел на клавиатуре ниже или введите /start.",
        reply_markup=main_menu_kb(),
    )


# ---------------------------------------------------------------------------
# ЗАПУСК
# ---------------------------------------------------------------------------

async def main() -> None:
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
