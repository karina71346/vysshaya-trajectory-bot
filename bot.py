import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
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

# ==== НАСТРОЙКИ =======================================================

TOKEN = os.getenv("BOT_TOKEN")

# Канал
CHANNEL_USERNAME = "@businesskodrosta"
CHANNEL_LINK = "https://t.me/businesskodrosta"

# Материалы папки лидера
TETRAD_URL = "https://tetrad-lidera.netlify.app/"
GUIDE_URL = "https://raw.githubusercontent.com/karina..."  # гайд
CHECKLIST_URL = "https://raw.githubusercontent.com/karina..."  # чек-лист
BOOKS_URL = "https://raw.githubusercontent.com/karina..."  # подборка книг

# Консультация
CONSULT_LINK = "https://forms.yandex.ru/u/69178642068ff0624a625f20/"

# Файлы на сервере
POLICY_DOC_PATH = "docs/politika_konfidencialnosti.pdf"
CONSENT_DOC_PATH = "docs/soglasie_na_obrabotku_pd.pdf"
KARINA_PHOTO_PATH = "media/karina_photo.jpg"


# ==== СОСТОЯНИЯ =======================================================

class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_channel_confirm = State()


# ==== КЛАВИАТУРЫ ======================================================

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📁 Папка лидера")],
            [KeyboardButton(text="🧠 Практика дня")],
            [KeyboardButton(text="ℹ️ О Карине"),
             KeyboardButton(text="📍 Записаться на консультацию")],
        ],
        resize_keyboard=True,
    )


def pd_agree_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ознакомился(ась), продолжить",
                    callback_data="pd_agree",
                )
            ]
        ]
    )


def folder_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📘 Открыть тетрадь лидера",
                url=TETRAD_URL)],
            [InlineKeyboardButton(
                text="📗 Гайд «Карта управленческой зрелости»",
                url=GUIDE_URL)],
            [InlineKeyboardButton(
                text="📙 Чек-лист зрелого лидера",
                url=CHECKLIST_URL)],
            [InlineKeyboardButton(
                text="📚 Подборка книг для лидеров",
                url=BOOKS_URL)],
            [InlineKeyboardButton(
                text="⬅️ В главное меню",
                callback_data="back_to_main")],
        ]
    )


def karina_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Перейти в канал «Бизнес со смыслом»",
                url=CHANNEL_LINK)],
            [InlineKeyboardButton(
                text="Записаться на консультацию",
                url=CONSULT_LINK)],
        ]
    )


def practice_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🎯 Колесо фокуса",
                callback_data="practice_focus_wheel")],
            [InlineKeyboardButton(
                text="🧩 Делегирование — 1 шаг",
                callback_data="practice_delegation")],
            [InlineKeyboardButton(
                text="🔍 «Откровение: точка реальности»",
                callback_data="practice_reality")],
        ]
    )


def back_to_practices_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="⬅️ К другим практикам",
                callback_data="practice_menu")],
        ]
    )


# ==== ТЕКСТ «О КАРИНЕ» =================================================

KARINA_ABOUT_TEXT = (
    "Карина Конорева — бизнес-архитектор, интегральный бизнес психолог и коуч лидеров.\n\n"
    "* Профессиональный путь 20 лет от преподавателя до предпринимателя \n"
    "* Основатель компании «Высшая Траектория»\n"
    "* Автор проекта «Код Роста»\n"
    "* Спикер Всемирного Бизнес-форума 2025 который внесен в книгу Рекордов Страны и Мира\n\n"
    "* Победитель в номинации «HR эксперт года» «Лидеры Эпохи 2024» \n\n"
    "* Лауреат Гран-При на звание «Лучший по профессии» среди специалистов в области Управления персоналом \n\n"
    "* Бизнес-психолог, ментор управленческой зрелости, коуч лидеров и команд\n"
    "*Эксперт по построению живых команд и системному росту бизнеса.\n"
    "* Член Академии социальных технологий и Российского общества «Знание» \n\n"
    "• 15+ лет опыта в создании трансформационных программ для предпринимателей и лидеров, "
    "объединяющих бизнес-стратегии, коучинговые техники и личностный рост.\n"
    "• Опубликовано 26 статей в научных журналах и СМИ.\n"
    "• Автор уникальной концепции циклов бизнес-туров, где каждое путешествие — это сочетание роста, "
    "отдыха и глубокого погружения в смыслы.\n"
    "• Проведено 250 + часов индивидуального и командного коучинга.\n\n"
    " Высшее образование: по психологии; педагогики; философии; \n"
    " Дополнительное образование: в области коучинга, бизнеса, менеджмента и финансов;\n\n"
    "ФИЛОСОФИЯ И ПОДХОД\n"
    "⚫️Создаю живые команды и системный рост бизнеса через лидеров нового типа\n"
    "⚫️В сотрудничестве со мной компании переходят от хаотичного роста к управляемому развитию.\n\n"
    "⚫️Мой фокус — не просто на людях, а на системе, в которой люди становятся источником устойчивого результата.\n\n"
    "⚫️Каждый проект — это баланс структуры и смысла, данных и энергии, цифр и человеческого потенциала.\n\n"
    "⚫️Создаю среду, где лидер принимает решения осознанно, команда движется в едином ритме, "
    "а бизнес растёт системно и предсказуемо. Высвобождая время собственника и увеличивая капитализацию компании "
    "через выстроенные процессы, сильные команды и здоровую культуру.\n"
    "Через этот бот вы получаете инструменты, которые помогают предпринимателям выходить из режима «герой-одиночка» "
    "и строить предсказуемый бизнес с опорой на команду."
)


# ==== РОУТЕР ==========================================================

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()

    text = (
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.\n\n"
        "Перед тем как получить Папку лидера и практики, немного формальностей:\n"
        "▪️ подтвердить согласие на обработку персональных данных.\n\n"
        "Сначала посмотрите документы по кнопкам ниже, затем нажмите кнопку "
        "«✅ Ознакомился(ась), продолжить»."
    )
    await message.answer(text)

    # документы
    try:
        policy = FSInputFile(POLICY_DOC_PATH)
        await message.answer_document(policy, caption="Политика конфиденциальности")
    except FileNotFoundError:
        await message.answer("⚠️ Файл политики конфиденциальности не найден на сервере.")

    try:
        consent = FSInputFile(CONSENT_DOC_PATH)
        await message.answer_document(consent, caption="Согласие на обработку персональных данных")
    except FileNotFoundError:
        await message.answer("⚠️ Файл согласия на обработку персональных данных не найден на сервере.")

    await message.answer(
        "Когда посмотрите документы, нажмите кнопку ниже, чтобы продолжить.",
        reply_markup=pd_agree_kb(),
    )


@router.callback_query(F.data == "pd_agree")
async def on_pd_agree(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(
        "Отлично. Напишите, пожалуйста, как к вам обращаться — ФИ."
    )
    await state.set_state(Registration.waiting_for_name)


@router.message(Registration.waiting_for_name)
async def on_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Напишите, пожалуйста, как к вам обращаться — текстом.")
        return

    await state.update_data(user_name=name)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Перейти в канал «Бизнес со смыслом»",
                url=CHANNEL_LINK)],
            [InlineKeyboardButton(
                text="✅ Я вступил(а) в канал",
                callback_data="joined_channel")],
        ]
    )

    await message.answer(
        f"{name}, благодарю! Теперь мы с вами на связи.\n\n"
        "Чтобы получить материалы, нужно вступить в канал «Бизнес со смыслом» и подтвердить участие.",
        reply_markup=kb,
    )
    await state.set_state(Registration.waiting_for_channel_confirm)


@router.callback_query(F.data == "joined_channel")
async def on_joined_channel(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await callback.answer()
    user_id = callback.from_user.id

    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in {
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        }:
            data = await state.get_data()
            name = data.get("user_name") or callback.from_user.full_name

            await callback.message.answer(
                f"Отлично, {name}! Папка лидера и практики теперь доступны в главном меню.\n\n"
                "Выберите нужный раздел на клавиатуре ниже.",
                reply_markup=main_menu_kb(),
            )
            await state.clear()
            return

        await callback.message.answer(
            "Пока не вижу вас в канале. Пожалуйста, вступите и нажмите кнопку ещё раз."
        )

    except TelegramBadRequest:
        await callback.message.answer(
            "Не удалось автоматически проверить подписку на канал, "
            "но вы всё равно можете пользоваться ботом.",
            reply_markup=main_menu_kb(),
        )
        await state.clear()


# ==== ПАПКА ЛИДЕРА ====================================================

@router.message(F.text == "📁 Папка лидера")
async def show_leader_folder(message: Message) -> None:
    await message.answer(
        "📁 Папка лидера — собрала для тебя ключевые материалы для роста управленческой зрелости.",
        reply_markup=folder_kb(),
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Вы в главном меню. Выберите нужный раздел.",
        reply_markup=main_menu_kb(),
    )


# ==== ПРАКТИКА ДНЯ ====================================================

@router.message(F.text == "🧠 Практика дня")
async def practice_entry(message: Message) -> None:
    await message.answer(
        "Выбери, какая практика сегодня больше откликается:",
        reply_markup=practice_menu_kb(),
    )


@router.callback_query(F.data == "practice_menu")
async def practice_menu_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Выбери, какая практика сегодня больше откликается:",
        reply_markup=practice_menu_kb(),
    )


@router.callback_query(F.data == "practice_focus_wheel")
async def practice_focus_wheel(callback: CallbackQuery) -> None:
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
    await callback.message.answer(text, reply_markup=back_to_practices_kb())


@router.callback_query(F.data == "practice_delegation")
async def practice_delegation(callback: CallbackQuery) -> None:
    await callback.answer()
    text = (
        "🧩 Практика дня — Делегирование, один шаг\n\n"
        "1. Выпиши 3 задачи, которые ты делаешь сам(а) по привычке.\n"
        "2. Отметь напротив каждой: «оставить себе» / «делегировать» / «прекратить».\n"
        "3. Выбери одну задачу для делегирования и сегодня:\n"
        "   • выбери человека,\n"
        "   • объясни контекст и ожидаемый результат,\n"
        "   • договорись о сроке и формате отчёта.\n\n"
        "Вечером задай себе вопрос: «Что оказалось проще, чем я думал(а), а что сложнее?»"
    )
    await callback.message.answer(text, reply_markup=back_to_practices_kb())


@router.callback_query(F.data == "practice_reality")
async def practice_reality(callback: CallbackQuery) -> None:
    await callback.answer()
    text = (
        "🔍 Практика дня — «Откровение: точка реальности»\n\n"
        "Ответь письменно на вопросы:\n"
        "1. Где я реально сейчас как лидер и где мой бизнес? Без приукрашиваний.\n"
        "2. Чего я больше всего боюсь, если в ближайшие 6–12 месяцев ничего не менять?\n"
        "3. Какой факт о бизнесе или команде мне неприятно признавать, и я от него отворачиваюсь?\n\n"
        "Заверши: «Шаг, который я готов(а) сделать в ближайшие 24 часа, несмотря на страх: ...»"
    )
    await callback.message.answer(text, reply_markup=back_to_practices_kb())


# ==== О КАРИНЕ ========================================================

@router.message(F.text == "ℹ️ О Карине")
async def about_karina(message: Message) -> None:
    try:
        photo = FSInputFile(KARINA_PHOTO_PATH)
        await message.answer_photo(
            photo,
            caption="Карина Конорева — бизнес-архитектор и бизнес-психолог.",
        )
        await message.answer(KARINA_ABOUT_TEXT, reply_markup=karina_kb())
    except FileNotFoundError:
        await message.answer(KARINA_ABOUT_TEXT, reply_markup=karina_kb())


# ==== КОНСУЛЬТАЦИЯ ====================================================

@router.message(F.text == "📍 Записаться на консультацию")
async def consultation(message: Message) -> None:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Записаться через форму",
                url=CONSULT_LINK)]
        ]
    )
    await message.answer(
        "Чтобы записаться на консультацию, перейдите по кнопке ниже и заполните короткую форму.",
        reply_markup=kb,
    )


# ==== ФОЛБЭК ==========================================================

@router.message()
async def fallback(message: Message) -> None:
    await message.answer(
        "Пока я понимаю только команды из меню. Выберите нужный раздел на клавиатуре ниже.",
        reply_markup=main_menu_kb(),
    )


# ==== ЗАПУСК БОТА =====================================================

async def main() -> None:
    bot = Bot(TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    logging.info("==> Запуск опроса для бота")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
