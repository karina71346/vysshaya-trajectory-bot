import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
    FSInputFile,
)

# ========================= НАСТРОЙКИ =========================

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в переменных окружения.")

CHANNEL_USERNAME = "@businesskodrosta"
CHANNEL_LINK = "https://t.me/businesskodrosta"

# Если хочешь получать заявки себе в личку — задай ADMIN_CHAT_ID
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Локальные файлы
POLICY_FILE = "politika_konfidencialnosti.pdf"
CONSENT_FILE = "soglasie_na_obrabotku_pd.pdf"

GUIDE_FILE = "karta_upravlencheskoy_zrelosti.pdf"
CHECKLIST_FILE = "checklist_zrelogo_lidera.pdf"
BOOKS_FILE = "podborca_knig_liderstvo.pdf"

KARINA_PHOTO_FILE = "KARINA_PHOTO_URL.jpg"

TETRAD_URL = "https://tetrad-lidera.netlify.app/"
CONSULT_LINK = "https://forms.yandex.ru/u/69178642068ff0624a625f20/"

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

logging.basicConfig(level=logging.INFO)


# ========================= СОСТОЯНИЯ =========================

class RegForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_email = State()


# ========================= КЛАВИАТУРЫ =========================

main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📁 Папка лидера"),
            KeyboardButton(text="🧭 Практика дня"),
        ],
        [
            KeyboardButton(text="ℹ️ О Карине"),
            KeyboardButton(text="📍 Записаться на консультацию"),
        ],
    ],
    resize_keyboard=True,
)

remove_kb = ReplyKeyboardRemove()

docs_next_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Ознакомился(ась), продолжить",
                callback_data="docs_next",
            )
        ]
    ]
)

channel_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📲 Вступить в канал", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="✅ Я вступил(а)", callback_data="joined_channel")],
    ]
)

leader_folder_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📗 Открыть тетрадь лидера", url=TETRAD_URL)],
        [InlineKeyboardButton(
            text="📘 Гайд «Карта управленческой зрелости»",
            callback_data="open_guide",
        )],
        [InlineKeyboardButton(
            text="📋 Чек-лист зрелого лидера",
            callback_data="open_checklist",
        )],
        [InlineKeyboardButton(
            text="📚 Подборка книг для лидеров",
            callback_data="open_books",
        )],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_menu")],
    ]
)

practice_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(
            text="🎯 Колесо фокуса лидера",
            callback_data="p_focus",
        )],
        [InlineKeyboardButton(
            text="🧩 Делегирование: матрица приоритетов",
            callback_data="p_delegate_matrix",
        )],
        [InlineKeyboardButton(
            text="🌀 Делегирование: радар зоны контроля",
            callback_data="p_delegate_radar",
        )],
        [InlineKeyboardButton(
            text="🔍 «Откровение»: точка реальности",
            callback_data="p_reality",
        )],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_menu")],
    ]
)

about_karina_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📲 Перейти в канал", url=CHANNEL_LINK)],
        [InlineKeyboardButton(
            text="📍 Записаться на консультацию",
            callback_data="go_consult",
        )],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_menu")],
    ]
)

consult_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(
            text="📍 Записаться на консультацию",
            url=CONSULT_LINK,
        )],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_menu")],
    ]
)

# ========================= ТЕКСТЫ =========================

WELCOME_TEXT = (
    "Добро пожаловать в пространство <b>«Высшая Траектория»</b> Карины Коноревой.\n\n"
    "Перед тем как получить <b>Папку лидера</b> и интерактивную тетрадь, немного формальностей:\n"
    "◽ подтвердить согласие на обработку персональных данных.\n\n"
    "Сначала посмотрите документы, затем нажмите кнопку "
    "<b>«Ознакомился(ась), продолжить»</b> ниже."
)

ASK_NAME_TEXT = "Как к вам обращаться? Напишите, пожалуйста, имя и фамилию."
ASK_PHONE_TEXT = (
    "Теперь ваш номер телефона.\n"
    "Можно нажать кнопку ниже «Отправить мой телефон» или написать номер текстом."
)
ASK_EMAIL_TEXT = "И последний шаг — ваш рабочий e-mail, на который удобно получать материалы."

CHANNEL_INVITE_TEXT = (
    "Спасибо! Последний шаг — материалы доступны участникам канала "
    "<b>«Бизнес со смыслом»</b>.\n\n"
    "1) Нажмите кнопку <b>«Вступить в канал»</b>.\n"
    "2) Вернитесь в бот и нажмите <b>«Я вступил(а)»</b>."
)

MAIN_MENU_TEXT = (
    "Готово ✅\n\n"
    "Вы в <b>главном меню</b>. Выберите раздел:\n"
    "• 📁 <b>Папка лидера</b> — тетрадь, гайд, чек-лист и подборка книг.\n"
    "• 🧭 <b>Практика дня</b> — короткие упражнения 10–15 минут.\n"
    "• ℹ️ <b>О Карине</b> — кто ведёт вас по траектории.\n"
    "• 📍 <b>Записаться на консультацию</b> — перейти к заявке."
)

ABOUT_KARINA_TEXT = (
    "<b>Карина Конорева</b>\n\n"
    "• Профессиональный путь 20 лет: от преподавателя до предпринимателя.\n"
    "• Основатель компании «Высшая Траектория».\n"
    "• Автор проекта «Код Роста».\n"
    "• Спикер Всемирного Бизнес-форума 2025, внесённого в Книгу рекордов страны и мира.\n\n"
    "• Победитель в номинации «HR-эксперт года» премии «Лидеры Эпохи 2024».\n"
    "• Лауреат Гран-При конкурса на звание «Лучший по профессии» среди специалистов в области управления персоналом.\n\n"
    "• Бизнес-психолог, ментор управленческой зрелости, коуч лидеров и команд.\n"
    "• Эксперт по построению живых команд и системному росту бизнеса.\n"
    "• Член Академии социальных технологий и Российского общества «Знание».\n\n"
    "• 15+ лет опыта в создании трансформационных программ для предпринимателей и лидеров, "
    "объединяющих бизнес-стратегии, коучинговые техники и личностный рост.\n"
    "• Опубликовано 26 статей в научных журналах и СМИ.\n"
    "• Автор концепции циклов бизнес-туров, где каждое путешествие — сочетание роста, отдыха и глубокого погружения в смыслы.\n"
    "• Проведено 250+ часов индивидуального и командного коучинга.\n\n"
    "Образование:\n"
    "• Высшее: психология, педагогика, философия.\n"
    "• Дополнительное: коучинг, бизнес, менеджмент, финансы.\n\n"
    "<b>Философия и подход</b>\n"
    "— Создаю живые команды и системный рост бизнеса через лидеров нового типа.\n"
    "— Компании переходят от хаотичного роста к управляемому развитию.\n"
    "— Фокус не только на людях, но и на системе, где люди становятся источником устойчивого результата.\n\n"
    "Каждый проект — баланс структуры и смысла, данных и энергии, цифр и человеческого потенциала.\n\n"
    "Через этот бот вы получаете инструменты, которые помогают предпринимателям выйти из режима "
    "«герой-одиночка» и строить предсказуемый бизнес с опорой на команду."
)

PRACTICE_MENU_TEXT = (
    "🧭 <b>Практика дня</b>\n\n"
    "Выберите, что актуально сегодня (10–15 минут работы):"
)

PRACTICE_FOCUS_TEXT = (
    "🎯 <b>Колесо фокуса лидера</b>\n\n"
    "1) Нарисуйте круг и разделите его на 8 секторов: Бизнес, Команда, Деньги, Здоровье, Энергия, Семья, Развитие, Радость.\n"
    "2) По шкале от 1 до 10 отметьте, насколько вы удовлетворены каждой сферой <b>сейчас</b>.\n"
    "3) Соедините точки — посмотрите, где колесо «проваливается».\n"
    "4) Ответьте письменно:\n"
    "   • Что даёт мне сейчас максимум энергии?\n"
    "   • Какая одна сфера, если вырастет на 1–2 пункта, сильнее всего повлияет на остальные?\n"
    "   • Какой один конкретный шаг я сделаю в ближайшие 72 часа?\n"
)

PRACTICE_DELEGATE_MATRIX_TEXT = (
    "🧩 <b>Делегирование: матрица приоритетов</b>\n\n"
    "1) Выпишите 10–15 задач, которые крутятся у вас в голове.\n"
    "2) Разнесите их по матрице:\n"
    "   • Важно/Срочно\n"
    "   • Важно/Не срочно\n"
    "   • Не важно/Срочно\n"
    "   • Не важно/Не срочно\n"
    "3) Далее:\n"
    "   • Важно/Срочно — делаю лично или под своим плотным контролем.\n"
    "   • Важно/Не срочно — планирую в календаре и даю контекст команде.\n"
    "   • Не важно/Срочно — делегирую.\n"
    "   • Не важно/Не срочно — смело вычёркиваю.\n"
    "4) Завершите практику вопросом: "
    "<i>«Что я продолжаю держать на себе просто из привычки, а не из здравого смысла?»</i>"
)

PRACTICE_DELEGATE_RADAR_TEXT = (
    "🌀 <b>Делегирование: радар зоны контроля</b>\n\n"
    "Нарисуйте три круга:\n"
    "   1) Я управляю напрямую.\n"
    "   2) Я влияю.\n"
    "   3) Я отпускаю.\n\n"
    "1) Выпишите 10–12 текущих задач и людей.\n"
    "2) Разложите по кругам.\n"
    "3) Посмотрите, где вы держите то, что пора отпустить, "
    "и где вас не хватает там, где нужна ваша позиция лидера.\n"
    "4) Вопрос в завершение: <i>«Если бы я доверял(а) команде на 20% больше, "
    "что бы я делегировал(а) уже сегодня?»</i>"
)

PRACTICE_REALITY_TEXT = (
    "🔍 <b>«Откровение»: точка реальности</b>\n\n"
    "Ответьте письменно (5–10 минут):\n\n"
    "1) В какой точке я нахожусь сейчас как лидер? В бизнесе? В деньгах? В команде?\n"
    "2) Что я делаю регулярно, что меня незаметно ослабляет?\n"
    "3) Что я избегаю видеть или признавать в своей роли руководителя?\n"
    "4) Если честно, куда я веду свой бизнес такой стратегией ещё на год вперёд?\n"
    "5) Какую одну новую роль я беру на себя уже сейчас (стратег, архитектор системы, наставник и т.п.)?\n\n"
    "Завершите практику одной фразой: <b>«Моя новая точка опоры как лидера — …»</b>"
)


# ========================= ХЭЛПЕРЫ =========================

async def send_main_menu(message: Message) -> None:
    await message.answer(MAIN_MENU_TEXT, reply_markup=main_menu_kb)


async def send_leader_folder(message: Message) -> None:
    await message.answer(
        "📁 <b>Папка лидера</b>\n\n"
        "Здесь собраны материалы, которые помогут перейти от хаотичного роста к системному:\n"
        "— интерактивная тетрадь лидера;\n"
        "— гайд «Карта управленческой зрелости»;\n"
        "— чек-лист зрелого лидера;\n"
        "— подборка книг для современных лидеров.\n\n"
        "Выберите, что открыть:",
        reply_markup=leader_folder_kb,
    )


# ========================= ОБРАБОТЧИКИ =========================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=remove_kb)

    try:
        await message.answer_document(
            FSInputFile(POLICY_FILE),
            caption="Политика конфиденциальности",
        )
        await message.answer_document(
            FSInputFile(CONSENT_FILE),
            caption="Согласие на обработку персональных данных",
        )
    except Exception as e:
        logging.exception("Ошибка при отправке документов: %s", e)

    await message.answer(
        "Когда посмотрите документы, нажмите кнопку ниже, чтобы продолжить.",
        reply_markup=docs_next_kb,
    )


@router.callback_query(F.data == "docs_next")
async def docs_next(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(ASK_NAME_TEXT)
    await state.set_state(RegForm.waiting_for_name)


@router.message(RegForm.waiting_for_name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    contact_kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Отправить мой телефон",
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(ASK_PHONE_TEXT, reply_markup=contact_kb)
    await state.set_state(RegForm.waiting_for_phone)


@router.message(RegForm.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.contact.phone_number)
    await message.answer(ASK_EMAIL_TEXT, reply_markup=remove_kb)
    await state.set_state(RegForm.waiting_for_email)


@router.message(RegForm.waiting_for_phone)
async def process_phone_text(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.text.strip())
    await message.answer(ASK_EMAIL_TEXT, reply_markup=remove_kb)
    await state.set_state(RegForm.waiting_for_email)


@router.message(RegForm.waiting_for_email)
async def process_email(message: Message, state: FSMContext) -> None:
    await state.update_data(email=message.text.strip())
    data = await state.get_data()

    if ADMIN_CHAT_ID:
        try:
            text = (
                "🆕 Новая регистрация в боте:\n\n"
                f"Имя: {data.get('name')}\n"
                f"Телефон: {data.get('phone')}\n"
                f"Email: {data.get('email')}\n"
                f"Username: @{message.from_user.username or 'нет'}\n"
                f"User ID: {message.from_user.id}"
            )
            await bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=text)
        except Exception as e:
            logging.exception("Не удалось отправить данные администратору: %s", e)

    await message.answer(CHANNEL_INVITE_TEXT, reply_markup=channel_kb)
    await state.clear()


@router.callback_query(F.data == "joined_channel")
async def joined_channel(callback: CallbackQuery) -> None:
    await callback.answer("Отлично, доступ открыт!")
    await send_main_menu(callback.message)


# ---------- ПАПКА ЛИДЕРА ----------

@router.message(F.text == "📁 Папка лидера")
async def folder_entry(message: Message) -> None:
    await send_leader_folder(message)


@router.callback_query(F.data == "open_guide")
async def open_guide(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        await callback.message.answer_document(
            FSInputFile(GUIDE_FILE),
            caption="Гайд «Карта управленческой зрелости»",
        )
    except Exception as e:
        logging.exception("Ошибка при отправке GUIDE_FILE: %s", e)
        await callback.message.answer("Файл временно недоступен. Попробуйте позже.")


@router.callback_query(F.data == "open_checklist")
async def open_checklist(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        await callback.message.answer_document(
            FSInputFile(CHECKLIST_FILE),
            caption="Чек-лист зрелого лидера",
        )
    except Exception as e:
        logging.exception("Ошибка при отправке CHECKLIST_FILE: %s", e)
        await callback.message.answer("Файл временно недоступен. Попробуйте позже.")


@router.callback_query(F.data == "open_books")
async def open_books(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        await callback.message.answer_document(
            FSInputFile(BOOKS_FILE),
            caption="Подборка книг для современных лидеров",
        )
    except Exception as e:
        logging.exception("Ошибка при отправке BOOKS_FILE: %s", e)
        await callback.message.answer("Файл временно недоступен. Попробуйте позже.")


# ---------- ПРАКТИКА ДНЯ ----------

@router.message(F.text == "🧭 Практика дня")
async def practice_menu(message: Message) -> None:
    await message.answer(PRACTICE_MENU_TEXT, reply_markup=practice_menu_kb)


@router.callback_query(F.data == "p_focus")
async def practice_focus(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(PRACTICE_FOCUS_TEXT)


@router.callback_query(F.data == "p_delegate_matrix")
async def practice_delegate_matrix(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(PRACTICE_DELEGATE_MATRIX_TEXT)


@router.callback_query(F.data == "p_delegate_radar")
async def practice_delegate_radar(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(PRACTICE_DELEGATE_RADAR_TEXT)


@router.callback_query(F.data == "p_reality")
async def practice_reality(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(PRACTICE_REALITY_TEXT)


# ---------- О КАРИНЕ ----------

@router.message(F.text == "ℹ️ О Карине")
async def about_karina(message: Message) -> None:
    try:
        photo = FSInputFile(KARINA_PHOTO_FILE)
        await message.answer_photo(
            photo=photo,
            caption=ABOUT_KARINA_TEXT,
            reply_markup=about_karina_kb,
        )
    except Exception as e:
        logging.exception("Не удалось отправить фото Карины: %s", e)
        await message.answer(ABOUT_KARINA_TEXT, reply_markup=about_karina_kb)


@router.callback_query(F.data == "go_consult")
async def callback_consult(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Чтобы записаться на консультацию, перейдите по ссылке ниже 👇",
        reply_markup=consult_kb,
    )


# ---------- КОНСУЛЬТАЦИЯ ИЗ МЕНЮ ----------

@router.message(F.text == "📍 Записаться на консультацию")
async def consult_from_menu(message: Message) -> None:
    await message.answer(
        "Чтобы записаться на консультацию, перейдите по ссылке ниже 👇",
        reply_markup=consult_kb,
    )


# ---------- В ГЛАВНОЕ МЕНЮ ----------

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await send_main_menu(callback.message)


# ---------- ОБЩИЙ ФОЛЛБЭК ----------

@router.message()
async def fallback(message: Message) -> None:
    await message.answer(
        "Чтобы продолжить, используйте, пожалуйста, кнопки внизу экрана.\n"
        "Если что-то пошло не так — отправьте команду /start.",
        reply_markup=main_menu_kb,
    )


# ========================= ЗАПУСК =========================

async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
