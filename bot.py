import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
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

# ================= НАСТРОЙКИ ======================

TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_USERNAME = "@businesskodrosta"
CHANNEL_LINK = f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"

TETRAD_URL = "https://tetrad-lidera.netlify.app/"
CONSULT_LINK = "https://forms.yandex.ru/admin/69178642068ff0624a625f20/settings?tab=access&preview=true"  # здесь твоя форма

# Файлы (ИМЕНА ДОЛЖНЫ СОВПАДАТЬ С ТЕМ, ЧТО В РЕПО)
POLICY_PATH = "politika_konfidencialnosti.pdf"
CONSENT_PATH = "soglasie_na_obrabotku_pd.pdf"

GUIDE_PATH = "karta_upravlencheskoy_zrelosti.pdf"
CHECKLIST_PATH = "checklist_zrelogo_lidera.pdf"
BOOKS_PATH = "podborca_knig_liderstvo.pdf"

KARINA_PHOTO_PATH = "karina_photo.jpg"

KARINA_BIO_TEXT = (
    "Карина Конорева — бизнес-архитектор, интегральный бизнес-психолог и коуч лидеров.\n"
    "Помогаю собственникам выходить из режима «героя-одиночки» и строить предсказуемый бизнес "
    "с опорой на команду.\n\n"
    "Опыт:\n"
    "• Профессиональный путь 20 лет от преподавателя до предпринимателя"
    "• Основатель компании «Высшая Траектория».\n"
    "• Спикер Всемирного Бизнес-форума 2025 который внесен в книгу Рекордов Страны и Мира.\n"
    "• Победитель в номинации «HR эксперт года» «Лидеры Эпохи 2024».\n"
    "• Член Академии социальных технологий и Российского общества «Знание».\n"
    "• 10+ лет управленческого опыта на позиции HRD.\n"
    "• Автор 26 статей в научных журналах и СМИ.\n"
    "• 250+ часов индивидуального и командного коучинга.\n\n"
    "Фокус — живые команды, системный рост и лидеры нового типа, "
    "которые создают предсказуемый результат, опираясь не только на себя, но и на систему."
)

# ================= FSM ===========================

class Form(StatesGroup):
    waiting_for_name = State()


# ================= КЛАВИАТУРЫ ====================

def main_menu_keyboard() -> ReplyKeyboardMarkup:
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


def leader_pack_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📘 Открыть тетрадь лидера", url=TETRAD_URL)],
            [
                InlineKeyboardButton(
                    text="📗 Гайд «Карта управленческой зрелости»",
                    callback_data="leader_guide",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📙 Чек-лист зрелого лидера",
                    callback_data="leader_checklist",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Подборка книг для лидеров",
                    callback_data="leader_books",
                )
            ],
        ]
    )


def practice_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎯 Колесо фокуса", callback_data="pr_focus_wheel"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📤 Микроделегирование", callback_data="pr_microdelegation"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💡 Откровение: точка реальности",
                    callback_data="pr_reality_point",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚀 Микрошаг к Высшей траектории",
                    callback_data="pr_microstep",
                )
            ],
        ]
    )


def back_to_practices_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ К другим практикам", callback_data="pr_back"
                )
            ]
        ]
    )


# ================= РОУТЕР ========================

router = Router()


# -------- /start --------
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()

    # ВАЖНО: убираем старую клавиатуру, чтобы меню не торчало сразу
    welcome_text = (
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.\n\n"
        "Перед тем как получить Папку лидера и практики, чуть-чуть формальностей:\n"
        "▪ подтвердить согласие на обработку персональных данных.\n\n"
        "Сначала посмотрите документы, затем нажмите кнопку «✅ Согласен/Согласна» ниже."
    )
    await message.answer(welcome_text, reply_markup=ReplyKeyboardRemove())

    # Отправляем документы
    await message.answer_document(
        FSInputFile(POLICY_PATH),
        caption="Политика конфиденциальности",
    )
    await message.answer_document(
        FSInputFile(CONSENT_PATH),
        caption="Согласие на обработку персональных данных",
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен/Согласна", callback_data="consent_yes")]
        ]
    )
    await message.answer(
        "Когда посмотрите документы, нажмите кнопку ниже, чтобы продолжить.",
        reply_markup=kb,
    )


# -------- Нажали «Согласен/Согласна» --------
@router.callback_query(F.data == "consent_yes")
async def consent_yes(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Form.waiting_for_name)
    await callback.message.answer(
        "Отлично. Напишите, пожалуйста, как к вам обращаться — ФИ."
    )


# -------- Обработка имени --------
@router.message(Form.waiting_for_name)
async def process_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    await state.clear()

    text = (
        f"Спасибо, {name}! Теперь мы с вами на связи.\n\n"
        "Чтобы получить материалы, нужно вступить в канал «Бизнес со смыслом» "
        "и подтвердить участие.\n\n"
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
            [InlineKeyboardButton(text="Я вступил(а)", callback_data="joined_channel")],
        ]
    )

    await message.answer(text, reply_markup=kb)


# -------- Проверка подписки --------
@router.callback_query(F.data == "joined_channel")
async def joined_channel(callback: CallbackQuery, bot: Bot) -> None:
    user_id = callback.from_user.id

    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
    except Exception as e:
        # Любая ошибка проверки — пишем в лог и даём понятный текст
        logging.exception("Ошибка проверки подписки: %r", e)
        await callback.message.answer(
            "Не удалось проверить подписку. "
            "Убедитесь, что бот добавлен в канал и повторите попытку чуть позже."
        )
        await callback.answer()
        return

    if member.status in {
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
    }:
        await callback.answer("Подписка подтверждена ✅", show_alert=False)
        await callback.message.answer(
            "Отлично! Материалы разблокированы. Ниже появилось меню бота.",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await callback.answer()
        await callback.message.answer(
            "Пока Telegram не видит вас в канале. "
            "Пожалуйста, вступите в «Бизнес со смыслом» и нажмите «Я вступил(а)» ещё раз."
        )


# ================= ПАПКА ЛИДЕРА ==================

@router.message(F.text == "📁 Папка лидера")
async def folder_leader(message: Message) -> None:
    text = (
        "Здесь собраны ключевые материалы, которые помогают навести порядок в управлении "
        "и двигаться к предсказуемому росту."
    )
    await message.answer(text, reply_markup=leader_pack_keyboard())


@router.callback_query(F.data == "leader_guide")
async def send_guide(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer_document(
        FSInputFile(GUIDE_PATH),
        caption="Гайд «Карта управленческой зрелости»",
    )


@router.callback_query(F.data == "leader_checklist")
async def send_checklist(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer_document(
        FSInputFile(CHECKLIST_PATH),
        caption="Чек-лист зрелого лидера",
    )


@router.callback_query(F.data == "leader_books")
async def send_books(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        await callback.message.answer_document(
            FSInputFile(BOOKS_PATH),
            caption="Подборка книг для лидеров",
        )
    except Exception as e:
        logging.exception("Не удалось отправить подборку книг: %r", e)
        await callback.message.answer(
            "Не удалось отправить файл с книгами. Проверь, что файл "
            f"«{BOOKS_PATH}» лежит рядом с bot.py и имя совпадает."
        )


# ================= ПРАКТИКА ДНЯ ==================

@router.message(F.text == "🧠 Практика дня")
async def practice_menu(message: Message) -> None:
    await message.answer("Выбери практику на сегодня:", reply_markup=practice_menu_keyboard())


@router.callback_query(F.data == "pr_back")
async def practices_back(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Выбери практику на сегодня:", reply_markup=practice_menu_keyboard()
    )


@router.callback_query(F.data == "pr_focus_wheel")
async def practice_focus(callback: CallbackQuery) -> None:
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
    await callback.message.answer(text, reply_markup=back_to_practices_keyboard())


@router.callback_query(F.data == "pr_microdelegation")
async def practice_microdelegation(callback: CallbackQuery) -> None:
    await callback.answer()
    text = (
        "📤 Практика дня — Микроделегирование\n\n"
        "1. Выпиши 3 операции, которые съедают у тебя больше всего энергии.\n"
        "2. Отметь, что из этого можно делегировать хотя бы на 30–50%.\n"
        "3. Выбери одну задачу и сегодня же передай её с понятным результатом и сроком."
    )
    await callback.message.answer(text, reply_markup=back_to_practices_keyboard())


@router.callback_query(F.data == "pr_reality_point")
async def practice_reality(callback: CallbackQuery) -> None:
    await callback.answer()
    text = (
        "💡 Практика дня — Откровение: точка реальности\n\n"
        "Ответь честно на три вопроса:\n"
        "1) Что в моём управлении сейчас работает хуже всего?\n"
        "2) Чем я лично это поддерживаю (своим поведением или решениями)?\n"
        "3) Какое одно решение я готов(а) принять в течение недели, чтобы изменить ситуацию?"
    )
    await callback.message.answer(text, reply_markup=back_to_practices_keyboard())


@router.callback_query(F.data == "pr_microstep")
async def practice_microstep(callback: CallbackQuery) -> None:
    await callback.answer()
    text = (
        "🚀 Практика дня — Микрошаг к Высшей траектории\n\n"
        "Представь, что через год твой бизнес стал более предсказуемым и спокойным для тебя.\n"
        "Что ты делаешь иначе как лидер?\n"
        "Запиши один микрошаг, который можно сделать уже сегодня, чтобы приблизиться к этой картинке."
    )
    await callback.message.answer(text, reply_markup=back_to_practices_keyboard())


# ================= О КАРИНЕ ======================

@router.message(F.text == "ℹ️ О Карине")
async def about_karina(message: Message) -> None:
    # сначала пытаемся отправить фото, если вдруг файла нет — просто текст
    try:
        photo = FSInputFile(KARINA_PHOTO_PATH)
        await message.answer_photo(photo, caption=KARINA_BIO_TEXT)
    except Exception as e:
        logging.exception("Не удалось отправить фото Карины: %r", e)
        await message.answer(KARINA_BIO_TEXT)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перейти в канал «Бизнес со смыслом»", url=CHANNEL_LINK
                )
            ],
            [
                InlineKeyboardButton(
                    text="Записаться на консультацию", url=CONSULT_LINK
                )
            ],
        ]
    )
    await message.answer(
        "Через этот бот вы получаете практические инструменты для системного роста.",
        reply_markup=kb,
    )


# ================= ЗАПИСЬ НА КОНСУЛЬТАЦИЮ =======

@router.message(F.text == "📍 Записаться на консультацию")
async def consult(message: Message) -> None:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перейти к форме записи", url=CONSULT_LINK
                )
            ]
        ]
    )
    await message.answer(
        "Чтобы записаться на консультацию, перейдите по ссылке:",
        reply_markup=kb,
    )


# ================= ПРОЧИЙ ТЕКСТ ==================

@router.message(StateFilter(None))
async def fallback(message: Message) -> None:
    await message.answer(
        "Пока я понимаю только команды из меню. "
        "Пожалуйста, воспользуйтесь кнопками ниже или введите /start."
    )


# ================= ЗАПУСК ========================

async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    if not TOKEN:
        raise RuntimeError("Не найден BOT_TOKEN в переменных окружения.")

    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
