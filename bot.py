import os
import asyncio
import logging
import random

from aiohttp import web

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
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

logging.basicConfig(level=logging.INFO)

# ================== НАСТРОЙКИ =======================================

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в переменных окружения.")

# Канал для проверки подписки
CHANNEL_USERNAME = "@businesskodrosta"

# Ссылка на интерактивную тетрадь
TETRAD_URL = "https://tetrad-lidera.netlify.app/"

# Форма на консультацию
CONSULT_LINK = "https://forms.yandex.ru/u/69178642068ff0624a625f20/"

# База для PDF и фото на GitHub (raw)
GITHUB_BASE = "https://raw.githubusercontent.com/karina71346/vysshaya-trajectory-bot/main"

# Фото Карины (положи файл с таким именем в репозиторий; если фото нет, бот не упадёт)
KARINA_PHOTO_URL = f"{GITHUB_BASE}/karina_konoreva.jpg"

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


# ================== СОСТОЯНИЯ ФОРМЫ ================================

class Form(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_email = State()


# ================== КЛАВИАТУРЫ =====================================

def main_menu_kb() -> ReplyKeyboardMarkup:
    """Главное меню (показываем только после завершения регистрации)."""
    return ReplyKeyboardMarkup(
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


def consent_kb() -> InlineKeyboardMarkup:
    """Кнопки под блоком согласия на ПДн."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Политика конфиденциальности",
                    url=f"{GITHUB_BASE}/politika_konfidencialnosti.pdf",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📄 Согласие на обработку персональных данных",
                    url=f"{GITHUB_BASE}/soglasie_na_obrabotku_pd.pdf",
                )
            ],
            [InlineKeyboardButton(text="Далее", callback_data="consent_continue")],
        ]
    )


def leader_pack_kb() -> InlineKeyboardMarkup:
    """Инлайн-меню внутри 'Папки лидера'."""
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
                    callback_data="lp_guide",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📙 Чек-лист зрелого лидера",
                    callback_data="lp_checklist",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Подборка книг для лидеров",
                    callback_data="lp_books",
                )
            ],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_menu")],
        ]
    )


def consult_kb() -> InlineKeyboardMarkup:
    """Кнопка на заявку + возврат в меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оставить заявку", url=CONSULT_LINK)],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_menu")],
        ]
    )


# ================== ТЕКСТЫ ==========================================

ABOUT_TEXT = (
    "ℹ️ <b>Карина Конорева</b>\n\n"
    "• Профессиональный путь 20 лет — от преподавателя до предпринимателя.\n"
    "• Основатель компании «Высшая Траектория».\n"
    "• Автор проекта «Код Роста».\n"
    "• Спикер Всемирного Бизнес-форума 2025, внесённого в книгу рекордов страны и мира.\n\n"
    "• Победитель в номинации «HR-эксперт года» премии «Лидеры Эпохи 2024».\n"
    "• Лауреат Гран-при в конкурсе на звание «Лучший по профессии» среди специалистов "
    "в области управления персоналом.\n\n"
    "• Бизнес-психолог, ментор управленческой зрелости, коуч лидеров и команд.\n"
    "• Эксперт по построению живых команд и системному росту бизнеса.\n"
    "• Член Академии социальных технологий и Российского общества «Знание».\n\n"
    "• 15+ лет опыта в создании трансформационных программ для предпринимателей и лидеров, "
    "где соединяются бизнес-стратегии, коучинг и личностный рост.\n"
    "• 26 статей в научных журналах и СМИ.\n"
    "• Автор уникальной концепции циклов бизнес-туров, где каждое путешествие — это рост, отдых "
    "и глубокое погружение в смыслы.\n"
    "• Проведено 250+ часов индивидуального и командного коучинга.\n\n"
    "🎓 Высшее образование: психология, педагогика, философия.\n"
    "📚 Дополнительное образование: коучинг, бизнес, менеджмент, финансы.\n\n"
    "<b>Философия и подход</b>\n"
    "• Создаю живые команды и системный рост бизнеса через лидеров нового типа.\n"
    "• В совместной работе компании переходят от хаотичного роста к управляемому развитию.\n"
    "• Фокус — на системе, где люди становятся источником устойчивого результата.\n"
    "• Каждый проект — баланс структуры и смысла, данных и энергии, цифр и человеческого потенциала.\n"
    "• Создаю среду, где лидер принимает решения осознанно, команда движется в едином ритме, "
    "а бизнес растёт системно и предсказуемо, высвобождая время собственника и повышая капитализацию.\n\n"
    "Через этот бот вы получаете инструменты, которые помогают предпринимателям выйти "
    "из режима «герой-одиночка» и строить предсказуемый бизнес с опорой на команду."
)

PRACTICES = [
    "🧠 <b>Практика дня — мини-аудит делегирования</b>\n\n"
    "1️⃣ Выпиши 5 задач, которые точно не обязан делать лично ты.\n"
    "2️⃣ Отметь, что удерживает: страх, недоверие, перфекционизм.\n"
    "3️⃣ Выбери ОДНУ задачу и передай её сегодня с понятным результатом и дедлайном.\n"
    "4️⃣ Вечером задай себе вопрос: «Что я почувствовал(а), когда НЕ сделал(а) это сам(а)?».",
    "🎯 <b>Практика дня — Колесо фокуса</b>\n\n"
    "Оцени по шкале от 1 до 10:\n"
    "• Стратегия\n• Команда\n• Деньги\n• Личное здоровье и ресурс\n\n"
    "Выбери сферу с минимальным баллом и сделай сегодня одно маленькое, но конкретное действие, "
    "которое поднимет её хотя бы на +1.",
    "🔥 <b>Практика дня — Честность с собой</b>\n\n"
    "Ответь письменно на три вопроса:\n"
    "1) Что в моём стиле управления устарело и тянет вниз?\n"
    "2) Где я до сих пор играю в «спасателя» вместо зрелого лидера?\n"
    "3) Какое одно решение я откладываю уже больше месяца?\n\n"
    "Выбери один пункт и обозначь срок, когда ты сдвинешь его с места.",
]


# ================== ХЭНДЛЕРЫ СТАРТА И РЕГИСТРАЦИИ ==================

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """Старт: убираем клавиатуру, даём блок про ПДн."""
    await state.clear()
    text = (
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.\n\n"
        "Перед тем как получить Папку лидера и интерактивную тетрадь, нужно пару формальностей:\n"
        "🔹 подтвердить согласие на обработку персональных данных.\n\n"
        "Сначала посмотрите документы, затем нажмите «Далее»."
    )
    await message.answer(text, reply_markup=ReplyKeyboardRemove())
    await message.answer("Документы ниже 👇", reply_markup=consent_kb())


@dp.callback_query(F.data == "consent_continue")
async def consent_continue(callback: types.CallbackQuery, state: FSMContext):
    """После согласия — спросить имя."""
    await callback.answer()
    await callback.message.answer(
        "Отлично. Напишите, пожалуйста, как к вам обращаться — ФИ.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(Form.waiting_name)


@dp.message(Form.waiting_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить мой номер", request_contact=True)]],
        resize_keyboard=True,
    )

    await message.answer(
        "Спасибо! Теперь отправьте, пожалуйста, ваш телефон.\n"
        "Можно нажать кнопку «Отправить мой номер» или написать его текстом.",
        reply_markup=kb,
    )
    await state.set_state(Form.waiting_phone)


@dp.message(Form.waiting_phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await ask_email(message, state)


@dp.message(Form.waiting_phone)
async def process_phone_text(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await ask_email(message, state)


async def ask_email(message: types.Message, state: FSMContext):
    await message.answer(
        "Теперь напишите, пожалуйста, вашу почту.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(Form.waiting_email)


@dp.message(Form.waiting_email)
async def process_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text.strip())

    await message.answer(
        "Благодарю! Теперь мы с вами на связи.\n\n"
        "Чтобы получить материалы, нужно вступить в канал "
        "«Бизнес со смыслом» и подтвердить участие.",
        reply_markup=ReplyKeyboardRemove(),
    )

    join_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Вступить в канал",
                    url="https://t.me/businesskodrosta",
                )
            ],
            [InlineKeyboardButton(text="Я вступил(а)", callback_data="check_sub")],
        ]
    )

    await message.answer(
        "Перейдите в канал по кнопке ниже, затем вернитесь в бот и нажмите «Я вступил(а)».",
        reply_markup=join_kb,
    )


# ================== ПРОВЕРКА ПОДПИСКИ ===============================

@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        status = member.status
    except Exception as e:
        logging.exception("Не удалось проверить подписку: %s", e)
        await callback.answer(
            "Не получилось проверить подписку. Попробуйте ещё раз чуть позже.",
            show_alert=True,
        )
        return

    if status in {
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.RESTRICTED,
    }:
        await state.clear()
        await callback.message.answer(
            "Отлично, я вижу вас в канале 👌\n"
            "Теперь вам доступно главное меню бота.",
        )
        await callback.message.answer(
            "Вы в главном меню. Выберите нужный раздел 👇",
            reply_markup=main_menu_kb(),
        )
        await callback.answer()
    else:
        await callback.answer(
            "Пока не вижу вас в канале. "
            "Пожалуйста, вступите и нажмите кнопку ещё раз.",
            show_alert=True,
        )


# ================== ПАПКА ЛИДЕРА ====================================

async def send_leader_pack(message: types.Message):
    text = (
        "🎁 <b>Папка лидера</b>\n\n"
        "Здесь собраны ключевые материалы для роста управленческой зрелости:\n\n"
        "✅ Интерактивная тетрадь лидера по делегированию —\n"
        "   поймёте, где главная точка перегруза и что передать уже на этой неделе.\n\n"
        "✅ Гайд «Карта управленческой зрелости» —\n"
        "   увидите, на каком уровне управления находитесь сейчас и куда расти.\n\n"
        "✅ Чек-лист зрелого лидера —\n"
        "   проверите, действуете ли как стратег, а не как спасатель.\n\n"
        "✅ Подборка книг для современных лидеров —\n"
        "   чтобы не искать, а сразу читать то, что действительно помогает масштабироваться.\n\n"
        "Нажмите нужный пункт ниже 👇"
    )
    await message.answer(text, reply_markup=leader_pack_kb())


@dp.message(F.text == "📁 Папка лидера")
async def menu_leader_pack(message: types.Message):
    await send_leader_pack(message)


@dp.callback_query(F.data == "lp_guide")
async def send_guide(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer_document(
        document=f"{GITHUB_BASE}/karta_upravlencheskoy_zrelosti.pdf",
        caption="Гайд «Карта управленческой зрелости».",
    )


@dp.callback_query(F.data == "lp_checklist")
async def send_checklist(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer_document(
        document=f"{GITHUB_BASE}/checklist_zrelogo_lidera.pdf",
        caption="Чек-лист зрелого лидера.",
    )


@dp.callback_query(F.data == "lp_books")
async def send_books(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer_document(
        document=f"{GITHUB_BASE}/podborca_knig_liderstvo.pdf",
        caption="Подборка книг для современных лидеров.",
    )


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Вы в главном меню. Выберите раздел 👇",
        reply_markup=main_menu_kb(),
    )


# ================== ПРАКТИКА ДНЯ ====================================

@dp.message(F.text == "🧠 Практика дня")
async def practice_of_the_day(message: types.Message):
    practice = random.choice(PRACTICES)
    await message.answer(practice)


# ================== О КАРИНЕ ========================================

async def send_about_me(message: types.Message):
    # Пытаемся отправить фото, но если файла нет или URL не работает —
    # просто пропускаем, чтобы бот не упал.
    try:
        await message.answer_photo(
            photo=KARINA_PHOTO_URL,
            caption="Карина Конорева — бизнес-психолог и ментор управленческой зрелости.",
        )
    except TelegramBadRequest as e:
        logging.warning("Не удалось отправить фото Карины: %s", e)

    await message.answer(ABOUT_TEXT, reply_markup=main_menu_kb())


@dp.message(F.text == "ℹ️ О Карине")
async def about_me(message: types.Message):
    await send_about_me(message)


# ================== КОНСУЛЬТАЦИЯ ====================================

async def send_consult(message: types.Message):
    text = (
        "🧭 <b>Записаться на консультацию</b>\n\n"
        "Если хотите разобраться с управленческой нагрузкой, командой или стратегией роста —\n"
        "можно записаться на индивидуальную консультацию.\n\n"
        "Нажмите кнопку ниже, чтобы перейти к заявке."
    )
    await message.answer(text, reply_markup=consult_kb())


@dp.message(F.text == "🧭 Записаться на консультацию")
async def consult(message: types.Message):
    await send_consult(message)


@dp.callback_query(F.data == "consult_cb")
async def cb_consult(callback: types.CallbackQuery):
    await callback.answer()
    await send_consult(callback.message)


# ================== ФОЛЛБЭК НА ЛЮБОЕ ДРУГОЕ СООБЩЕНИЕ ===============

@dp.message()
async def fallback(message: types.Message):
    """Если человек пишет что-то своё — мягко возвращаем в меню."""
    await message.answer(
        "Я сейчас отвечаю через кнопки меню внизу экрана.\n"
        "Пожалуйста, выберите раздел, который вам интересен 👇",
        reply_markup=main_menu_kb(),
    )


# ================== ИНТЕГРАЦИЯ С RENDER (aiohttp + polling) =========

async def on_startup(app: web.Application):
    logging.info("==> Стартуем polling бота")
    asyncio.create_task(dp.start_polling(bot))


async def handle_root(request: web.Request):
    return web.Response(text="Bot is running")


def main():
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.on_startup.append(on_startup)

    port = int(os.getenv("PORT", "10000"))
    logging.info("==> Запуск web-сервера на порту %s", port)
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
