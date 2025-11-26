import os
import asyncio
import logging

from aiohttp import web

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ChatMemberStatus, ParseMode
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
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)

# ===== НАСТРОЙКИ ======================================================

TOKEN = os.getenv("BOT_TOKEN")  # Токен бота из переменных окружения Render
CHANNEL_USERNAME = "@businesskodrosta"  # username канала

# Ссылка на интерактивную тетрадь
TETRAD_URL = "https://tetrad-lidera.netlify.app/"

# Форма на консультацию
CONSULT_LINK = "https://forms.yandex.ru/u/69178642068ff0624a625f20/"

# База для ПРЯМЫХ PDF-ссылок (raw, а не страница GitHub)
GITHUB_BASE = (
    "https://raw.githubusercontent.com/karina71346/vysshaya-trajectory-bot/main"
)

# =====================================================================

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в переменных окружения.")

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


class Form(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_email = State()


class Practice(StatesGroup):
    # Делегирование сегодня
    deleg_zone = State()
    deleg_task = State()
    # Откровение: точка реальности
    reality_zone = State()
    reality_answers = State()
    # Колесо баланса
    wheel_human = State()
    wheel_leader = State()
    wheel_team = State()
    wheel_system = State()
    wheel_focus = State()


# ---------- КЛАВИАТУРЫ -----------------------------------------------


def main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню как INLINE, без нижней панели."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📁 Папка лидера",
                    callback_data="menu_leader_pack",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧩 Практика дня",
                    callback_data="menu_practice",
                )
            ],
            [
                InlineKeyboardButton(
                    text="ℹ️ О Карине",
                    callback_data="about_me_cb",
                ),
                InlineKeyboardButton(
                    text="🧭 Записаться на консультацию",
                    callback_data="consult_cb",
                ),
            ],
        ]
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
    """Кнопки под Папкой лидера: тетрадь + PDF + назад в главное меню."""
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
            [
                InlineKeyboardButton(
                    text="⬅️ В главное меню",
                    callback_data="back_to_menu",
                )
            ],
        ]
    )


def consult_kb() -> InlineKeyboardMarkup:
    """Кнопка на заявку плюс возврат в меню (INLINE)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оставить заявку", url=CONSULT_LINK)],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_menu")],
        ]
    )


def practice_kb() -> InlineKeyboardMarkup:
    """Меню практик дня."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎯 Делегирование сегодня",
                    callback_data="pr_delegation",
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
                    text="⚖️ Колесо баланса лидера",
                    callback_data="pr_wheel",
                )
            ],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_menu")],
        ]
    )


# ---------- СТАРТ И СБОР ДАННЫХ --------------------------------------


@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    # сбрасываем возможное старое состояние
    await state.clear()

    # сразу убираем любую старую reply-клавиатуру
    await message.answer(
        "Запускаю бот «Высшая траектория»…",
        reply_markup=ReplyKeyboardRemove(),
    )

    text = (
        "Добро пожаловать в пространство «Высшая Траектория» Карины Коноревой.\n\n"
        "Перед тем как получить Папку лидера и интерактивную тетрадь, нужно чуть-чуть формальностей:\n"
        "🔹 подтвердить согласие на обработку персональных данных.\n\n"
        "Сначала посмотрите документы, затем нажмите «Далее»."
    )
    await message.answer(text, reply_markup=consent_kb())


@dp.callback_query(F.data == "consent_continue")
async def consent_continue(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Отлично! Давайте начнём знакомство.\n\n"
        "Напишите, пожалуйста, как к вам обращаться — ФИ.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(Form.waiting_name)


@dp.message(Form.waiting_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())

    # здесь reply-клавиатура уместна: только для отправки контакта
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить мой номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
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
    # сохраняем e-mail (валидации пока нет)
    await state.update_data(email=message.text.strip())

    # анкета закончена, очищаем состояние
    await state.clear()

    await message.answer(
        "Благодарю! Теперь мы с вами на связи.\n\n"
        "Чтобы получить материалы, нужно вступить в канал "
        "«Бизнес со смыслом» и подтвердить участие.",
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


# ---------- ПРОВЕРКА ПОДПИСКИ ----------------------------------------


@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery):
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
        await callback.message.answer(
            "Отлично, я вижу вас в канале 👌\n"
            "Отправляю Папку лидера.",
        )
        await send_leader_pack(callback.message)
        # Только после выдачи Папки показываем ГЛАВНОЕ МЕНЮ (inline)
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


# ---------- ПАПКА ЛИДЕРА ---------------------------------------------


async def send_leader_pack(message: types.Message):
    text = (
        "🎁 <b>Папка лидера</b>\n\n"
        "Здесь собраны ключевые материалы для роста управленческой зрелости:\n\n"
        "✅ Интерактивная тетрадь лидера по делегированию\n"
        "→ вы поймёте, где ваша главная точка перегруза и как её передать уже на этой неделе.\n\n"
        "✅ Гайд «Карта управленческой зрелости»\n"
        "→ вы найдёте, на каком уровне управления застряли и как выйти выше.\n\n"
        "✅ Чек-лист зрелого лидера\n"
        "→ вы проверите: насколько вы не спасатель, а действительно стратег.\n\n"
        "✅ Подборка книг для современных лидеров\n"
        "→ чтобы не искать, а сразу читать, что действительно помогает масштабироваться.\n"
    )
    await message.answer(text, reply_markup=leader_pack_kb())


@dp.callback_query(F.data == "menu_leader_pack")
async def cb_menu_leader_pack(callback: types.CallbackQuery):
    await callback.answer()
    await send_leader_pack(callback.message)


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("Вы в главном меню.", reply_markup=main_menu_kb())


# --- отправка самих PDF как файлов по клику в Папке лидера ---


@dp.callback_query(F.data == "lp_guide")
async def send_guide(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer_document(
        document=f"{GITHUB_BASE}/karta_upravlencheskoy_zrelosti.pdf",
        caption="Гайд «Карта управленческой зрелости»",
    )


@dp.callback_query(F.data == "lp_checklist")
async def send_checklist(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer_document(
        document=f"{GITHUB_BASE}/checklist_zrelogo_lidera.pdf",
        caption="Чек-лист зрелого лидера",
    )


@dp.callback_query(F.data == "lp_books")
async def send_books(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer_document(
        document=f"{GITHUB_BASE}/podborca_knig_liderstvo.pdf",
        caption="Подборка книг для современных лидеров",
    )


# ---------- БЛОК «О КАРИНЕ» ------------------------------------------


async def send_about_me(message: types.Message):
    text = (
        "ℹ️ <b>Информация о Карине Коноревой</b>\n\n"
        "• Бизнес-психолог, ментор управленческой зрелости и командный коуч.\n"
        "• 20+ лет пути: от преподавателя до предпринимателя.\n"
        "• Основатель проекта «Высшая Траектория».\n"
        "• Эксперт по построению живых команд и системному росту бизнеса.\n\n"
        "Через этот бот вы получаете инструменты, которые помогают "
        "предпринимателям выходить из режима «герой-одиночка» "
        "и строить предсказуемый бизнес с опорой на команду."
    )
    await message.answer(text, reply_markup=main_menu_kb())


@dp.callback_query(F.data == "about_me_cb")
async def cb_about_me(callback: types.CallbackQuery):
    await callback.answer()
    await send_about_me(callback.message)


# ---------- КОНСУЛЬТАЦИЯ ---------------------------------------------


async def send_consult(message: types.Message):
    text = (
        "🧭 <b>Записаться на консультацию</b>\n\n"
        "Если вы хотите разобраться с управленческой нагрузкой, командой или стратегией роста —\n"
        "можно записаться на индивидуальную консультацию.\n\n"
        "Нажмите кнопку ниже, чтобы перейти к заявке."
    )
    await message.answer(text, reply_markup=consult_kb())


@dp.callback_query(F.data == "consult_cb")
async def cb_consult(callback: types.CallbackQuery):
    await callback.answer()
    await send_consult(callback.message)


# ---------- ПРАКТИКА ДНЯ ---------------------------------------------


@dp.callback_query(F.data == "menu_practice")
async def practice_entry(callback: types.CallbackQuery, state: FSMContext):
    # чистим возможные старые состояния практик / форм
    await state.clear()
    text = (
        "🧩 <b>Практика дня</b>\n\n"
        "Что ты берёшь сегодня — прокачать руку делегирования, голову лидера "
        "или баланс жизни?\n\n"
        "Выбери формат практики (10–15 минут):"
    )
    await callback.message.answer(text, reply_markup=practice_kb())
    await callback.answer()


# --- 🎯 Делегирование сегодня ---


@dp.callback_query(F.data == "pr_delegation")
async def pr_delegation_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    text = (
        "🎯 <b>Практика «Делегирование сегодня»</b>\n\n"
        "Где сегодня больше всего застреваешь?\n\n"
        "▫️ Операционка\n"
        "▫️ Клиенты / продажи\n"
        "▫️ Команда\n"
        "▫️ Личное (быт, семья и т.д.)\n\n"
        "Напиши коротко, в какой зоне у тебя сегодня больше всего нагрузки."
    )
    await callback.message.answer(text)
    await state.set_state(Practice.deleg_zone)


@dp.message(Practice.deleg_zone)
async def pr_delegation_zone(message: types.Message, state: FSMContext):
    await state.update_data(deleg_zone=message.text.strip())
    text = (
        "Напиши одну задачу, которую ты всё ещё тянешь сам(а), "
        "хотя её уже можно делегировать."
    )
    await message.answer(text)
    await state.set_state(Practice.deleg_task)


@dp.message(Practice.deleg_task)
async def pr_delegation_task(message: types.Message, state: FSMContext):
    await state.update_data(deleg_task=message.text.strip())
    text = (
        "Что ты уже сделал(а) с этой задачей сегодня?\n\n"
        "Выбери вариант — честно с собой 🤝"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="+1 — просто делегировал(а)",
                    callback_data="deleg_p1",
                )
            ],
            [
                InlineKeyboardButton(
                    text="+2 — делегировал(а) + обозначил(а) результат",
                    callback_data="deleg_p2",
                )
            ],
            [
                InlineKeyboardButton(
                    text="+3 — заполнил(а) «паспорт задачи»",
                    callback_data="deleg_p3",
                )
            ],
            [
                InlineKeyboardButton(
                    text="+5 — не влезал(а) до срока и получил(а) результат",
                    callback_data="deleg_p5",
                )
            ],
        ]
    )
    await message.answer(text, reply_markup=kb)


async def _finish_delegation(callback: types.CallbackQuery, state: FSMContext, points: int):
    await callback.answer()
    text = (
        f"🎯 Твой ход зафиксирован (+{points} балл(ов)).\n\n"
        "Сегодня ты сделал(а) шаг как стратег, а не как герой-одиночка.\n\n"
        "Мини-вопрос для закрепления:\n"
        "Что станет возможным, если ты будешь так делать 30 дней подряд?\n\n"
        "Можешь ответить в одном-двух предложениях — это уже смена траектории."
    )
    await callback.message.answer(text, reply_markup=main_menu_kb())
    await state.clear()


@dp.callback_query(F.data == "deleg_p1")
async def deleg_p1(callback: types.CallbackQuery, state: FSMContext):
    await _finish_delegation(callback, state, 1)


@dp.callback_query(F.data == "deleg_p2")
async def deleg_p2(callback: types.CallbackQuery, state: FSMContext):
    await _finish_delegation(callback, state, 2)


@dp.callback_query(F.data == "deleg_p3")
async def deleg_p3(callback: types.CallbackQuery, state: FSMContext):
    await _finish_delegation(callback, state, 3)


@dp.callback_query(F.data == "deleg_p5")
async def deleg_p5(callback: types.CallbackQuery, state: FSMContext):
    await _finish_delegation(callback, state, 5)


# --- 🔍 Откровение: точка реальности ---


@dp.callback_query(F.data == "pr_reality")
async def pr_reality_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    text = (
        "🔍 <b>Практика «Откровение: точка реальности»</b>\n\n"
        "В какой зоне сейчас нужнее всего честное «сканирование»?\n\n"
        "▫️ Я как лидер\n"
        "▫️ Я и команда\n"
        "▫️ Я и бизнес-модель\n"
        "▫️ Я и моя жизнь вне бизнеса\n\n"
        "Напиши, какую зону выбираешь."
    )
    await callback.message.answer(text)
    await state.set_state(Practice.reality_zone)


@dp.message(Practice.reality_zone)
async def pr_reality_zone(message: types.Message, state: FSMContext):
    await state.update_data(reality_zone=message.text.strip())
    text = (
        "Спасибо. Теперь ответь на три вопроса в одном сообщении (можно списком):\n\n"
        "1️⃣ Где я прямо сейчас *делаю вид*, что всё ок, хотя знаю, что это не так?\n"
        "2️⃣ Чего я боюсь, если признаю реальность такой, какая она есть?\n"
        "3️⃣ Если бы я смотрел(а) на это как лидер, а не как уставший человек — "
        "какой был бы мой следующий шаг?\n\n"
        "Напиши свои ответы одним сообщением."
    )
    await message.answer(text)
    await state.set_state(Practice.reality_answers)


@dp.message(Practice.reality_answers)
async def pr_reality_answers(message: types.Message, state: FSMContext):
    await state.update_data(reality_answers=message.text.strip())
    await state.clear()
    text = (
        "🔓 Ты уже сделал(а) больше, чем большинство — честно посмотрел(а) на реальность.\n\n"
        "Если хочешь развернуть это в план действий — приходи с этим откровением на сессию "
        "или вернись к тетради лидера.\n\n"
        "🧭 В главном меню есть раздел с консультацией и практиками."
    )
    await message.answer(text, reply_markup=main_menu_kb())


# --- ⚖️ Колесо баланса лидера ---


@dp.callback_query(F.data == "pr_wheel")
async def pr_wheel_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    text = (
        "⚖️ <b>Колесо баланса лидера</b>\n\n"
        "Мы посмотрим на 4 ключевые зоны:\n"
        "1) Я как человек\n"
        "2) Я как лидер\n"
        "3) Команда\n"
        "4) Система управления\n\n"
        "Оцени каждую по шкале от 1 до 10.\n\n"
        "1️⃣ Я как человек (ресурс, здоровье, «я как живой»).\n"
        "Напиши число от 1 до 10."
    )
    await callback.message.answer(text)
    await state.set_state(Practice.wheel_human)


def _parse_score(text: str):
    """Пытаемся распарсить оценку от 1 до 10. Если не получилось — None."""
    try:
        value = int(text.strip())
    except ValueError:
        return None
    if 1 <= value <= 10:
        return value
    return None


@dp.message(Practice.wheel_human)
async def wheel_human(message: types.Message, state: FSMContext):
    value = _parse_score(message.text)
    if value is None:
        await message.answer("Пожалуйста, напиши число от 1 до 10.")
        return
    await state.update_data(wheel_human=value)
    text = (
        "2️⃣ Я как лидер (фокус, решения, внутренняя опора).\n"
        "Напиши число от 1 до 10."
    )
    await message.answer(text)
    await state.set_state(Practice.wheel_leader)


@dp.message(Practice.wheel_leader)
async def wheel_leader(message: types.Message, state: FSMContext):
    value = _parse_score(message.text)
    if value is None:
        await message.answer("Пожалуйста, напиши число от 1 до 10.")
        return
    await state.update_data(wheel_leader=value)
    text = (
        "3️⃣ Команда (доверие, ответственность, роли).\n"
        "Напиши число от 1 до 10."
    )
    await message.answer(text)
    await state.set_state(Practice.wheel_team)


@dp.message(Practice.wheel_team)
async def wheel_team(message: types.Message, state: FSMContext):
    value = _parse_score(message.text)
    if value is None:
        await message.answer("Пожалуйста, напиши число от 1 до 10.")
        return
    await state.update_data(wheel_team=value)
    text = (
        "4️⃣ Система управления (процессы, метрики, предсказуемость).\n"
        "Напиши число от 1 до 10."
    )
    await message.answer(text)
    await state.set_state(Practice.wheel_system)


@dp.message(Practice.wheel_system)
async def wheel_system(message: types.Message, state: FSMContext):
    value = _parse_score(message.text)
    if value is None:
        await message.answer("Пожалуйста, напиши число от 1 до 10.")
        return
    await state.update_data(wheel_system=value)
    data = await state.get_data()

    h = data.get("wheel_human")
    l = data.get("wheel_leader")
    t = data.get("wheel_team")
    s = data.get("wheel_system")

    text = (
        "Твои оценки:\n"
        f"• Я как человек: {h}/10\n"
        f"• Я как лидер: {l}/10\n"
        f"• Команда: {t}/10\n"
        f"• Система управления: {s}/10\n\n"
        "🎯 Фокус зрелого лидера — не только гореть, но и подтягивать слабое звено.\n\n"
        "Выбери одну зону как фокус ближайших 7 дней и напиши её текстом "
        "(например: «Система управления»)."
    )
    await message.answer(text)
    await state.set_state(Practice.wheel_focus)


@dp.message(Practice.wheel_focus)
async def wheel_focus(message: types.Message, state: FSMContext):
    focus = message.text.strip()
    await state.clear()
    text = (
        f"Отличный выбор: «{focus}».\n\n"
        "В ближайшие 7 дней задавай себе один вопрос каждый день:\n"
        "«Что я могу сделать сегодня на +1 балл именно в этой зоне?»\n\n"
        "Можешь использовать бот как напоминание: заходи в «Практика дня» "
        "и фиксируй свои шаги."
    )
    await message.answer(text, reply_markup=main_menu_kb())


# ---------- СЕРВЕР ДЛЯ RENDER ----------------------------------------


async def on_startup(app: web.Application):
    # запускаем aiogram-поллинг внутри aiohttp-приложения
    asyncio.create_task(
        dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    )


async def handle_root(request: web.Request):
    # простой ответ для health-check Render
    return web.Response(text="Bot is running")


def main():
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.on_startup.append(on_startup)

    port = int(os.getenv("PORT", "10000"))
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
