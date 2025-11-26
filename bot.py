import os
import logging
import random

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)

logging.basicConfig(level=logging.INFO)

# ===== НАСТРОЙКИ ======================================================

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в переменных окружения.")

# Канал, в который проверяем подписку
CHANNEL_USERNAME = "@businesskodrosta"

# Ссылка на интерактивную тетрадь
TETRAD_URL = "https://tetrad-lidera.netlify.app/"

# Ссылка на форму для консультации
CONSULT_LINK = "https://forms.yandex.ru/u/69178642068ff0624a625f20/"

# Названия файлов (должны лежать рядом с bot.py в репозитории)
POLICY_PDF = "politika_konfidencialnosti.pdf"
AGREEMENT_PDF = "soglasie_na_obrabotku_pd.pdf"
KARTA_PDF = "karta_upravlencheskoy_zrelosti.pdf"
CHECKLIST_PDF = "checklist_zrelogo_lidera.pdf"
BOOKS_PDF = "podborca_knig_liderstvo.pdf"

# Фото Карина – файл в репозитории
KARINA_PHOTO_FILE = "KARINA_PHOTO_URL"

# ===== ТЕКСТЫ =========================================================

WELCOME_TEXT = (
    "<b>Добро пожаловать в пространство «Высшая Траектория» Карина Коноревой.</b>\n\n"
    "Перед тем как получить Папку лидера и интерактивную тетрадь, нужно чуть-чуть формальностей:\n"
    "🔹 подтвердить согласие на обработку персональных данных.\n\n"
    "Сначала посмотрите документы, затем нажмите «Далее»."
)

ASK_NAME_TEXT = "Как к вам можно обращаться? Напишите, пожалуйста, ваше имя."
ASK_PHONE_TEXT = (
    "Отправьте, пожалуйста, номер телефона.\n"
    "Можно просто написать его в ответ или нажать кнопку «📱 Отправить номер»."
)
ASK_EMAIL_TEXT = "Напишите, пожалуйста, ваш e-mail (куда удобно получать материалы и ссылки)."

AFTER_FORM_TEXT = (
    "Благодарю! Теперь мы с вами на связи.\n\n"
    "Чтобы получить материалы, нужно вступить в канал «Бизнес со смыслом» и подтвердить участие."
)

ASK_CHANNEL_TEXT = (
    "Перейдите в канал по кнопке ниже, затем вернитесь в бота и нажмите «Я вступил(а)»."
)

MAIN_MENU_TEXT = "Вы в главном меню. Выберите нужный раздел 👇"

PAPKA_TEXT = (
    "📁 <b>Папка лидера</b>\n\n"
    "Здесь собраны материалы, которые помогут навести порядок в делегировании и управлении:\n"
    "• интерактивная тетрадь лидера по делегированию;\n"
    "• гайд «Карта управленческой зрелости»;\n"
    "• чек-лист зрелого лидера;\n"
    "• подборка книг для современных лидеров."
)

ABOUT_KARINA_TEXT = (
    "<b>Карина Конорева</b>\n\n"
    "• Профессиональный путь 20 лет: от преподавателя до предпринимателя.\n"
    "• Основатель компании «Высшая Траектория».\n"
    "• Автор проекта «Код Роста».\n"
    "• Спикер Всемирного Бизнес-форума 2025, который внесен в книгу Рекордов Страны и Мира.\n\n"
    "• Победитель в номинации «HR эксперт года» премии «Лидеры Эпохи 2024».\n"
    "• Лауреат Гран-При на звание «Лучший по профессии» среди специалистов в области Управления персоналом.\n\n"
    "• Бизнес-психолог, ментор управленческой зрелости, коуч лидеров и команд.\n"
    "• Эксперт по построению живых команд и системному росту бизнеса.\n"
    "• Член Академии социальных технологий и Российского общества «Знание».\n\n"
    "• 15+ лет опыта в создании трансформационных программ для предпринимателей и лидеров, "
    "объединяющих бизнес-стратегии, коучинговые техники и личностный рост.\n"
    "• Опубликовано 26 статей в научных журналах и СМИ.\n"
    "• Автор уникальной концепции циклов бизнес-туров, где каждое путешествие — сочетание роста, отдыха "
    "и глубокого погружения в смыслы.\n"
    "• Проведено 250+ часов индивидуального и командного коучинга.\n\n"
    "🎓 <b>Образование</b>\n"
    "• Высшее: психология, педагогика, философия.\n"
    "• Дополнительное: коучинг, бизнес, менеджмент, финансы.\n\n"
    "<b>Философия и подход</b>\n"
    "• Создаю живые команды и системный рост бизнеса через лидеров нового типа.\n"
    "• Компании переходят от хаотичного роста к управляемому развитию.\n"
    "• Фокус не только на людях, а на системе, где люди становятся источником устойчивого результата.\n\n"
    "Каждый проект — баланс структуры и смысла, данных и энергии, цифр и человеческого потенциала.\n\n"
    "Создаю среду, где лидер принимает решения осознанно, команда движется в едином ритме, "
    "а бизнес растёт системно и предсказуемо — высвобождая время собственника и увеличивая капитализацию "
    "через выстроенные процессы, сильные команды и здоровую культуру.\n\n"
    "Через этот бот вы получаете инструменты, которые помогают предпринимателям выходить из режима "
    "«герой-одиночка» и строить предсказуемый бизнес с опорой на команду."
)

CONSULT_TEXT = (
    "🧭 <b>Запись на консультацию</b>\n\n"
    "Работаем с управленческой зрелостью, делегированием, системой управления и командой, "
    "чтобы бизнес перестал держаться только на одном человеке и вышел на предсказуемую траекторию роста.\n\n"
    "Нажмите кнопку ниже, чтобы оставить заявку на консультацию."
)

PRACTICE_MENU_TEXT = "🧠 <b>Практика дня</b>\n\nВыберите, что актуально на сегодня 👇"

PRACTICE_DELEGATION = (
    "🧩 <b>Практика дня — мини-аудит делегирования</b>\n\n"
    "1️⃣ Выпишите 5 задач, которые вы точно не обязаны делать лично.\n"
    "2️⃣ Напротив каждой отметьте, почему до сих пор не делегируете:\n"
    "   • страх, что сделают хуже;\n"
    "   • недоверие;\n"
    "   • «быстрее сделаю сам(а)»;\n"
    "   • нет подходящего человека;\n"
    "   • другая причина.\n\n"
    "3️⃣ Выберите одну задачу и сегодня передайте её с понятным результатом и дедлайном.\n"
    "4️⃣ Вечером ответьте себе:\n"
    "   • Что я почувствовал(а), когда НЕ сделал(а) это сам(а)?\n"
    "   • Что самое страшное реально случилось?\n"
    "   • Какой вывод я делаю про своё лидерство?"
)

PRACTICE_FOCUS = (
    "🎯 <b>Практика дня — Колесо фокуса лидера</b>\n\n"
    "Оцените по шкале от 1 до 10, насколько вас устраивает сейчас:\n"
    "• стратегия бизнеса;\n"
    "• команда и делегирование;\n"
    "• деньги и прибыль;\n"
    "• личный ресурс (энергия, здоровье, отдых).\n\n"
    "1️⃣ Отметьте цифры в заметках или тетради.\n"
    "2️⃣ Найдите зону с самым низким баллом.\n"
    "3️⃣ Запишите одно конкретное действие, которое поднимет этот сектор хотя бы на +1 в ближайшие 24 часа.\n"
    "4️⃣ Поставьте себе напоминание и сделайте это действие сегодня."
)

PRACTICE_REALITY = (
    "🔍 <b>Практика дня — «Откровение: точка реальности»</b>\n\n"
    "Ответьте письменно:\n"
    "1️⃣ Где я реально нахожусь сейчас в бизнесе — по цифрам, процессам и команде?\n"
    "2️⃣ Чего я боюсь признать про своё лидерство?\n"
    "3️⃣ Какое решение я откладываю уже больше месяца — и чем мне это «выгодно»?\n\n"
    "В конце задайте себе вопрос:\n"
    "«Если я встану во взрослую позицию лидера, что я сделаю по-другому в ближайшие 7 дней?»"
)

FALLBACK_TEXT = (
    "Я сейчас работаю через меню внизу экрана.\n"
    "Пожалуйста, выберите подходящий раздел 👇"
)

# ===== КЛАВИАТУРЫ =====================================================


# Инлайн-клава под приветствием (документы + Далее)
consent_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📄 Политика конфиденциальности",
                callback_data="doc_policy",
            )
        ],
        [
            InlineKeyboardButton(
                text="📄 Согласие на обработку персональных данных",
                callback_data="doc_agreement",
            )
        ],
        [
            InlineKeyboardButton(
                text="➡️ Далее",
                callback_data="consent_continue",
            )
        ],
    ]
)

# Клава для отправки телефона
phone_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Отправить номер", request_contact=True)],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

# Главное меню (reply-клава)
main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📁 Папка лидера")],
        [KeyboardButton(text="🧠 Практика дня")],
        [
            KeyboardButton(text="ℹ️ О Карине"),
            KeyboardButton(text="🧭 Записаться на консультацию"),
        ],
    ],
    resize_keyboard=True,
)

# Инлайн-клава Папки лидера
papka_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📘 Открыть тетрадь лидера", url=TETRAD_URL
            )
        ],
        [
            InlineKeyboardButton(
                text="📗 Гайд «Карта управленческой зрелости»",
                callback_data="doc_karta",
            )
        ],
        [
            InlineKeyboardButton(
                text="📙 Чек-лист зрелого лидера",
                callback_data="doc_checklist",
            )
        ],
        [
            InlineKeyboardButton(
                text="📚 Подборка книг для лидеров",
                callback_data="doc_books",
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

# Инлайн-клава Практики дня
practice_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🧩 Делегирование", callback_data="pr_delegation"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎯 Колесо фокуса", callback_data="pr_focus_wheel"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔍 Откровение: точка реальности",
                callback_data="pr_reality",
            )
        ],
        [
            InlineKeyboardButton(
                text="🎲 Случайная практика", callback_data="pr_random"
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

# Инлайн-клава под блоком «О Карине»
about_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📲 В канал «Бизнес со смыслом»",
                url="https://t.me/businesskodrosta",
            )
        ],
        [
            InlineKeyboardButton(
                text="🧭 Записаться на консультацию",
                url=CONSULT_LINK,
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

# Инлайн-клава под приглашением в канал
channel_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📲 Вступить в канал",
                url="https://t.me/businesskodrosta",
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Я вступил(а)",
                callback_data="check_sub",
            )
        ],
    ]
)

# Инлайн-клава под консультацией
consult_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🧭 Оставить заявку", url=CONSULT_LINK
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

# ===== FSM СОСТОЯНИЯ ==================================================


class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_email = State()
    waiting_for_channel = State()


# ===== ИНИЦИАЛИЗАЦИЯ БОТА =============================================


bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ========================================


async def send_pdf(
    message: types.Message, file_name: str, caption: str
) -> None:
    """Безопасно отправляем PDF, не роняя бота, если файл не найден."""
    try:
        pdf = FSInputFile(file_name)
        await message.answer_document(pdf, caption=caption)
    except Exception as e:
        logging.warning("Не удалось отправить PDF %s: %s", file_name, e)
        await message.answer(
            "Файл временно недоступен. Попробуйте позже или напишите Карине."
        )


async def is_subscribed(user_id: int) -> bool:
    """Проверка подписки на канал."""
    try:
        member = await bot.get_chat_member(
            chat_id=CHANNEL_USERNAME, user_id=user_id
        )
        return member.status not in (
            ChatMemberStatus.LEFT,
            ChatMemberStatus.KICKED,
        )
    except TelegramBadRequest:
        return False
    except Exception as e:
        logging.warning("Ошибка при проверке подписки: %s", e)
        return False


# ===== ХЕНДЛЕРЫ =======================================================


@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    # Сбрасываем состояние и прячем старую клавиатуру
    await state.clear()
    await message.answer(
        WELCOME_TEXT,
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer(
        "Ознакомьтесь с документами ниже и нажмите «Далее».",
        reply_markup=consent_kb,
    )


# --- Документы ПДн ---


@dp.callback_query(F.data == "doc_policy")
async def cb_policy(callback: types.CallbackQuery):
    await callback.answer()
    await send_pdf(
        callback.message,
        POLICY_PDF,
        "Политика конфиденциальности.",
    )


@dp.callback_query(F.data == "doc_agreement")
async def cb_agreement(callback: types.CallbackQuery):
    await callback.answer()
    await send_pdf(
        callback.message,
        AGREEMENT_PDF,
        "Согласие на обработку персональных данных.",
    )


@dp.callback_query(F.data == "consent_continue")
async def cb_consent_continue(
    callback: types.CallbackQuery, state: FSMContext
):
    await callback.answer()
    await callback.message.answer(
        ASK_NAME_TEXT, reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Registration.waiting_for_name)


# --- Имя ---


@dp.message(Registration.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        await message.answer("Пожалуйста, напишите ваше имя текстом.")
        return

    await state.update_data(name=name)
    await message.answer(ASK_PHONE_TEXT, reply_markup=phone_kb)
    await state.set_state(Registration.waiting_for_phone)


# --- Телефон ---


@dp.message(Registration.waiting_for_phone, F.contact)
async def process_phone_contact(
    message: types.Message, state: FSMContext
):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await message.answer(
        ASK_EMAIL_TEXT, reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Registration.waiting_for_email)


@dp.message(Registration.waiting_for_phone)
async def process_phone_text(message: types.Message, state: FSMContext):
    phone = (message.text or "").strip()
    if not phone:
        await message.answer(
            "Пожалуйста, отправьте номер телефона текстом или через кнопку."
        )
        return
    await state.update_data(phone=phone)
    await message.answer(
        ASK_EMAIL_TEXT, reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Registration.waiting_for_email)


# --- Email ---


@dp.message(Registration.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    email = (message.text or "").strip()
    if not email or "@" not in email:
        await message.answer(
            "Похоже, это не похоже на e-mail. Отправьте, пожалуйста, корректный адрес."
        )
        return

    await state.update_data(email=email)

    await message.answer(AFTER_FORM_TEXT)
    await message.answer(ASK_CHANNEL_TEXT, reply_markup=channel_kb)
    await state.set_state(Registration.waiting_for_channel)


# --- Проверка подписки ---


@dp.callback_query(F.data == "check_sub")
async def cb_check_sub(
    callback: types.CallbackQuery, state: FSMContext
):
    await callback.answer()
    user_id = callback.from_user.id
    if await is_subscribed(user_id):
        await state.clear()
        await callback.message.answer(
            "Отлично, вижу вас в канале. Можно переходить к материалам."
        )
        await callback.message.answer(
            MAIN_MENU_TEXT, reply_markup=main_menu_kb
        )
    else:
        await callback.answer(
            "Пока не вижу вас в канале. Пожалуйста, вступите и нажмите кнопку ещё раз.",
            show_alert=True,
        )


# --- Главное меню: Папка лидера ---


@dp.message(F.text == "📁 Папка лидера")
async def menu_papka(message: types.Message):
    await message.answer(PAPKA_TEXT, reply_markup=papka_kb)


@dp.callback_query(F.data == "doc_karta")
async def cb_doc_karta(callback: types.CallbackQuery):
    await callback.answer()
    await send_pdf(
        callback.message,
        KARTA_PDF,
        "Гайд «Карта управленческой зрелости».",
    )


@dp.callback_query(F.data == "doc_checklist")
async def cb_doc_checklist(callback: types.CallbackQuery):
    await callback.answer()
    await send_pdf(
        callback.message,
        CHECKLIST_PDF,
        "Чек-лист зрелого лидера.",
    )


@dp.callback_query(F.data == "doc_books")
async def cb_doc_books(callback: types.CallbackQuery):
    await callback.answer()
    await send_pdf(
        callback.message,
        BOOKS_PDF,
        "Подборка книг для современных лидеров.",
    )


# --- Главное меню: Практика дня ---


@dp.message(F.text == "🧠 Практика дня")
async def menu_practice(message: types.Message):
    await message.answer(PRACTICE_MENU_TEXT, reply_markup=practice_kb)


@dp.callback_query(F.data == "pr_delegation")
async def cb_pr_delegation(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(PRACTICE_DELEGATION)


@dp.callback_query(F.data == "pr_focus_wheel")
async def cb_pr_focus(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(PRACTICE_FOCUS)


@dp.callback_query(F.data == "pr_reality")
async def cb_pr_reality(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(PRACTICE_REALITY)


@dp.callback_query(F.data == "pr_random")
async def cb_pr_random(callback: types.CallbackQuery):
    await callback.answer()
    practice = random.choice(
        [PRACTICE_DELEGATION, PRACTICE_FOCUS, PRACTICE_REALITY]
    )
    await callback.message.answer("🎲 Случайный выбор практики:")
    await callback.message.answer(practice)


# --- Главное меню: О Карине ---


@dp.message(F.text == "ℹ️ О Карине")
async def menu_about(message: types.Message):
    # Пытаемся отправить фото
    try:
        photo = FSInputFile(KARINA_PHOTO_FILE)
        await message.answer_photo(photo)
    except Exception as e:
        logging.warning("Не удалось отправить фото Карина: %s", e)

    await message.answer(ABOUT_KARINA_TEXT, reply_markup=about_kb)


# --- Главное меню: Записаться на консультацию ---


@dp.message(F.text == "🧭 Записаться на консультацию")
async def menu_consult(message: types.Message):
    await message.answer(CONSULT_TEXT, reply_markup=consult_kb)


# --- Общий callback «назад в меню» ---


@dp.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        MAIN_MENU_TEXT, reply_markup=main_menu_kb
    )


# --- Фолбек: любые сообщения вне регистрации и меню ---


@dp.message(StateFilter(None))
async def fallback(message: types.Message):
    # Если это не одна из известных кнопок – мягко возвращаем в меню
    text = (message.text or "").strip()
    known_commands = {
        "📁 Папка лидера",
        "🧠 Практика дня",
        "ℹ️ О Карине",
        "🧭 Записаться на консультацию",
        "/start",
    }
    if text in known_commands:
        return  # эти обрабатываются выше

    await message.answer(FALLBACK_TEXT, reply_markup=main_menu_kb)


# ===== ЗАПУСК =========================================================


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
