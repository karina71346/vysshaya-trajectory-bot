import os
import asyncio
import logging

from aiohttp import web
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
    FSInputFile,
)
from aiogram.enums import ChatMemberStatus

logging.basicConfig(level=logging.INFO)

# ===== НАСТРОЙКИ ======================================================

TOKEN = os.getenv("BOT_TOKEN")  # токен из Render

CHANNEL_USERNAME = "@businesskodrosta"
CHANNEL_URL = "https://t.me/businesskodrosta"

# Ссылка на интерактивную тетрадь
TETRAD_URL = "https://tetrad-lidera.netlify.app/"

# Форма на консультацию
CONSULT_LINK = "https://forms.yandex.ru/u/69178642068ff0624a625f20/"

# Локальные файлы в репозитории
KARINA_PHOTO_FILE = "KARINA_PHOTO_URL.jpg"

PRIVACY_POLICY_FILE = "politika_konfidencialnosti.pdf"
PD_AGREEMENT_FILE = "soglasie_na_obrabotku_pd.pdf"

GUIDE_FILE = "karta_upravlencheskoy_zrelosti.pdf"
CHECKLIST_FILE = "checklist_zrelogo_lidera.pdf"
BOOKS_FILE = "podborka_knig_dlya_liderov.pdf"


# ===== СОСТОЯНИЯ ======================================================

class RegStates(StatesGroup):
    waiting_consent = State()
    waiting_name = State()
    finished = State()


# ===== КЛАВИАТУРЫ =====================================================

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
            [
                InlineKeyboardButton(
                    text="Политика конфиденциальности",
                    callback_data="show_policy",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Согласие на обработку персональных данных",
                    callback_data="show_pd_agreement",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Согласен/Согласна",
                    callback_data="consent_yes",
                )
            ],
        ]
    )


def leader_folder_kb() -> InlineKeyboardMarkup:
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
            [
                InlineKeyboardButton(
                    text="↩️ В главное меню",
                    callback_data="back_to_main",
                )
            ],
        ]
    )


def practice_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎯 Колесо фокуса",
                    callback_data="practice_focus_wheel",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧩 Делегирование + матрица Эйзенхауэра",
                    callback_data="practice_delegation",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧠 Откровение: точка реальности",
                    callback_data="practice_reality_point",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Коуч-вопрос дня",
                    callback_data="practice_question_of_day",
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ В главное меню",
                    callback_data="back_to_main",
                )
            ],
        ]
    )


def about_buttons_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перейти в канал «Бизнес со смыслом»",
                    url=CHANNEL_URL,
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


# ===== ВСПОМОГАТЕЛЬНОЕ =================================================

async def send_safe_document(message: types.Message, file_path: str, caption: str):
    """
    Отправка документа так, чтобы бот не падал, если файла нет.
    """
    try:
        doc = FSInputFile(file_path)
        await message.answer_document(document=doc, caption=caption)
    except Exception as e:
        logging.error("Не удалось отправить файл %s: %s", file_path, e)
        await message.answer(f"Файл пока недоступен: {caption}")


# ===== ХЕНДЛЕРЫ РЕГИСТРАЦИИ ============================================

async def on_start(message: types.Message, state: FSMContext):
    await state.set_state(RegStates.waiting_consent)
    text = (
        "Добро пожаловать в пространство <b>«Высшая Траектория» Карины Коноревой</b>.\n\n"
        "Перед тем как получить <b>Папку лидера</b> и практики, немного формальностей:\n"
        "▪️ подтвердить согласие на обработку персональных данных.\n\n"
        "Сначала посмотрите документы по кнопкам ниже, затем нажмите "
        "«✅ Согласен/Согласна»."
    )
    await message.answer(text, reply_markup=consent_kb(), parse_mode="HTML")


async def handle_policy(call: types.CallbackQuery):
    await call.answer()
    await send_safe_document(
        call.message,
        PRIVACY_POLICY_FILE,
        "Политика конфиденциальности",
    )


async def handle_pd_agreement(call: types.CallbackQuery):
    await call.answer()
    await send_safe_document(
        call.message,
        PD_AGREEMENT_FILE,
        "Согласие на обработку персональных данных",
    )


async def handle_consent_yes(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(RegStates.waiting_name)
    await call.message.answer(
        "Спасибо! Напишите, пожалуйста, как к вам обращаться — ФИО или имя.",
        reply_markup=ReplyKeyboardRemove(),
    )


async def handle_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(RegStates.finished)
    user_name = message.text.strip()

    text = (
        f"{user_name}, благодарю! Теперь мы с вами на связи.\n\n"
        "Чтобы получить материалы, вступите, пожалуйста, в канал "
        "«Бизнес со смыслом» и подтвердите участие.\n\n"
        "После вступления нажмите кнопку «Я вступил(а)»."
    )

    join_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перейти в канал «Бизнес со смыслом»",
                    url=CHANNEL_URL,
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Я вступил(а)",
                    callback_data="joined_channel",
                )
            ],
        ]
    )

    await message.answer(text, reply_markup=join_kb)


async def handle_joined_channel(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()

    member = await bot.get_chat_member(
        chat_id=CHANNEL_USERNAME,
        user_id=call.from_user.id,
    )

    if member.status not in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    ):
        await call.message.answer(
            "Пока не вижу вас в канале «Бизнес со смыслом».\n"
            "Пожалуйста, вступите в канал и затем снова нажмите «Я вступил(а)».",
        )
        return

    await state.set_state(RegStates.finished)
    await call.message.answer(
        "Супер, доступ открыт! Ниже — главное меню бота.",
        reply_markup=main_menu_kb(),
    )


# ===== ОСНОВНОЕ МЕНЮ ===================================================

async def handle_unknown_message(message: types.Message):
    await message.answer(
        "Пока я понимаю только команды из меню. Выберите нужный раздел на клавиатуре ниже.",
        reply_markup=main_menu_kb(),
    )


async def handle_leader_folder(message: types.Message):
    await message.answer(
        "📂 <b>Папка лидера</b>\n\n"
        "Выберите, что открыть:",
        reply_markup=leader_folder_kb(),
        parse_mode="HTML",
    )


async def handle_leader_guide(call: types.CallbackQuery):
    await call.answer()
    await send_safe_document(
        call.message,
        GUIDE_FILE,
        "Гайд «Карта управленческой зрелости»",
    )


async def handle_leader_checklist(call: types.CallbackQuery):
    await call.answer()
    await send_safe_document(
        call.message,
        CHECKLIST_FILE,
        "Чек-лист зрелого лидера",
    )


async def handle_leader_books(call: types.CallbackQuery):
    await call.answer()
    await send_safe_document(
        call.message,
        BOOKS_FILE,
        "Подборка книг для лидеров",
    )


async def handle_practice_menu(message: types.Message):
    await message.answer(
        "🧠 <b>Практика дня</b>\n\n"
        "Выберите формат, который сейчас больше всего откликается:",
        reply_markup=practice_menu_kb(),
        parse_mode="HTML",
    )


# ===== ПРАКТИКИ =======================================================

async def handle_practice_focus_wheel(call: types.CallbackQuery):
    await call.answer()
    text = (
        "🎯 <b>Практика дня — Колесо фокуса</b>\n\n"
        "Оцени по шкале от 1 до 10:\n"
        "• Стратегия\n"
        "• Команда\n"
        "• Деньги\n"
        "• Личное здоровье и ресурс\n\n"
        "Выбери сферу с минимальным баллом и сделай сегодня одно маленькое, "
        "но конкретное действие, которое поднимет её хотя бы на +1."
    )
    await call.message.answer(text, parse_mode="HTML")


async def handle_practice_delegation(call: types.CallbackQuery):
    await call.answer()
    text = (
        "🧩 <b>Практика — Делегирование + Матрица Эйзенхауэра</b>\n\n"
        "1) Выпиши до 10 задач, которые сейчас висят на тебе.\n"
        "2) Разложи их по матрице:\n"
        "   🔴 Срочное / Важное — сделай лично или передай под контролем.\n"
        "   🟢 Не срочное / Важное — запланируй и делегируй с пояснением смысла.\n"
        "   ⚪ Срочное / Не важное — делегируй полностью.\n"
        "   ⚫ Не срочное / Не важное — смело вычеркивай.\n\n"
        "3) Выбери одну задачу, которую ты прямо сегодня можешь передать "
        "человеку, который сделает хотя бы на 70% так же хорошо, как ты.\n"
        "Это будет твоим шагом к выходу из режима «герой-одиночка»."
    )
    await call.message.answer(text, parse_mode="HTML")


async def handle_practice_reality_point(call: types.CallbackQuery):
    await call.answer()
    text = (
        "🧠 <b>Откровение: точка реальности</b>\n\n"
        "Ответь честно письменно:\n"
        "• Где я сейчас на самом деле как лидер и предприниматель?\n"
        "• Чего я избегаю видеть в своём бизнесе или команде?\n"
        "• Какая правда про меня как руководителя может быть неприятной, "
        "но освободит энергию, если я её признаю?\n\n"
        "В конце запиши один конкретный шаг, который ты сделаешь в ближайшие 72 часа, "
        "исходя из этой честной точки реальности."
    )
    await call.message.answer(text, parse_mode="HTML")


async def handle_practice_question_of_day(call: types.CallbackQuery):
    await call.answer()
    text = (
        "💬 <b>Коуч-вопрос дня</b>\n\n"
        "Представь, что через год твой бизнес стал в 2–3 раза устойчивее и спокойнее.\n"
        "Команда работает как система, прибыль предсказуема, а ты дышишь свободнее.\n\n"
        "Вопрос: <b>что ты перестал(а) делать</b> как руководитель, "
        "чтобы это стало возможным?\n\n"
        "Запиши 1–3 пункта и выбери один маленький шаг, который можешь сделать уже сегодня."
    )
    await call.message.answer(text, parse_mode="HTML")


# ===== О КАРИНЕ И КОНСУЛЬТАЦИЯ ========================================

async def handle_about(message: types.Message):
    photo = None
    try:
        photo = FSInputFile(KARINA_PHOTO_FILE)
    except Exception as e:
        logging.error("Не удалось загрузить фото Карины: %s", e)

    about_text = (
        "<b>Карина Конорева</b> — бизнес-архитектор, интегральный бизнес-психолог и коуч лидеров.\n\n"
        "• Профессиональный путь 20 лет от преподавателя до предпринимателя\n"
        "• Основатель компании «Высшая Траектория»\n"
        "• Автор проекта «Код Роста»\n"
        "• Спикер Всемирного Бизнес-форума 2025, внесённого в книгу рекордов страны и мира\n"
        "• Победитель в номинации «HR эксперт года» премии «Лидеры Эпохи 2024»\n"
        "• Лауреат Гран-При «Лучший по профессии» среди специалистов в области управления персоналом\n"
        "• Бизнес-психолог, ментор управленческой зрелости, коуч лидеров и команд\n"
        "• Эксперт по построению живых команд и системному росту бизнеса\n"
        "• Член Академии социальных технологий и Российского общества «Знание»\n"
        "• 15+ лет опыта в создании трансформационных программ для предпринимателей и лидеров\n"
        "• 26 статей в научных журналах и СМИ\n"
        "• 250+ часов индивидуального и командного коучинга\n\n"
        "<b>Философия</b>\n"
        "Создаю живые команды и системный рост бизнеса через лидеров нового типа.\n"
        "Фокус — не только на людях, но и на системе, где люди становятся источником устойчивого результата.\n\n"
        "Через этот бот вы получаете практические инструменты, которые помогают выйти из режима "
        "«герой-одиночка» и строить предсказуемый бизнес с опорой на команду."
    )

    if photo:
        await message.answer_photo(
            photo=photo,
            caption=about_text,
            reply_markup=about_buttons_kb(),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            about_text,
            reply_markup=about_buttons_kb(),
            parse_mode="HTML",
        )


async def handle_consult(message: types.Message):
    await message.answer(
        "Чтобы записаться на консультацию с Кариной Коноревой, перейдите по кнопке ниже:",
        reply_markup=about_buttons_kb(),
    )


# ===== РЕГИСТРАЦИЯ ХЕНДЛЕРОВ =========================================

def register_handlers(dp: Dispatcher, bot: Bot):
    dp.message.register(on_start, CommandStart())

    dp.callback_query.register(handle_policy, F.data == "show_policy")
    dp.callback_query.register(handle_pd_agreement, F.data == "show_pd_agreement")
    dp.callback_query.register(handle_consent_yes, F.data == "consent_yes")

    dp.message.register(handle_name, RegStates.waiting_name)
    dp.callback_query.register(handle_joined_channel, F.data == "joined_channel")

    dp.message.register(handle_leader_folder, F.text == "📂 Папка лидера")
    dp.callback_query.register(handle_leader_guide, F.data == "leader_guide")
    dp.callback_query.register(handle_leader_checklist, F.data == "leader_checklist")
    dp.callback_query.register(handle_leader_books, F.data == "leader_books")

    dp.message.register(handle_practice_menu, F.text == "🧠 Практика дня")
    dp.callback_query.register(
        handle_practice_focus_wheel, F.data == "practice_focus_wheel"
    )
    dp.callback_query.register(
        handle_practice_delegation, F.data == "practice_delegation"
    )
    dp.callback_query.register(
        handle_practice_reality_point, F.data == "practice_reality_point"
    )
    dp.callback_query.register(
        handle_practice_question_of_day, F.data == "practice_question_of_day"
    )

    dp.message.register(handle_about, F.text == "ℹ️ О Карине")
    dp.message.register(handle_consult, F.text == "📍 Записаться на консультацию")

    dp.message.register(handle_unknown_message)


# ===== ЗАПУСК НА RENDER (WEB + POLLING) ================================

async def on_startup(bot: Bot):
    logging.info("Бот запущен")


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    register_handlers(dp, bot)

    app = web.Application()

    async def handle(request):
        return web.Response(text="OK")

    app.router.add_get("/", handle)

    async def on_startup_app(app_):
        await on_startup(bot)

    app.on_startup.append(on_startup_app)

    async def runner():
        await dp.start_polling(bot)

    loop = asyncio.get_event_loop()
    loop.create_task(runner())

    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))


if __name__ == "__main__":
    asyncio.run(main())
