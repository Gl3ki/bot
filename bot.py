import asyncio
import json
import os
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = "8973935831:AAGQRIhQiR_00xS0yxzziNDN7GEGs8oZ0kI"
USERS_FILE = "subscribers.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# --- РАБОТА С БАЗОЙ ПОДПИСЧИКОВ ---

def load_subscribers():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_subscribers(subscribers):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(subscribers), f)

subscribers = load_subscribers()

# --- INLINE-КЛАВИАТУРЫ ---

main_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Сегодня 📓", callback_data="day_today"),
            InlineKeyboardButton(text="Завтра 📁", callback_data="day_tomorrow")
        ],
        [InlineKeyboardButton(text="Выбрать день недели 🔍", callback_data="menu_days")],
        [
            InlineKeyboardButton(text="Рассылка 📩", callback_data="toggle_sub"),
            InlineKeyboardButton(text="Прочее ⚙️", callback_data="menu_other")
        ]
    ]
)

days_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Понедельник", callback_data="day_0"), InlineKeyboardButton(text="Вторник", callback_data="day_1")],
        [InlineKeyboardButton(text="Среда", callback_data="day_2"), InlineKeyboardButton(text="Четверг", callback_data="day_3")],
        [InlineKeyboardButton(text="Пятница", callback_data="day_4"), InlineKeyboardButton(text="Суббота", callback_data="day_5")],
        [InlineKeyboardButton(text="⬅️ Назад в главное меню", callback_data="menu_main")]
    ]
)

# --- ДАННЫЕ РАСПИСАНИЯ ---

SCHEDULE = {
    0: [
        {"time": "08.00 - 09.35", "week": "1 нед.", "title": "Нормирование точности и технические измерения (лаб.)", "teacher": "Давыдова Е.А.", "room": "ауд. 520, к.17"},
        {"time": "08.00 - 09.35", "week": "2 нед.", "title": "Охрана труда (лаб.)", "teacher": "Чуешков В.В.", "room": "ауд. 381, к.1"},
        {"time": "09.55 - 11.30", "week": "Все недели", "title": "Нормирование точности и технические измерения (лекция)", "teacher": "Давыдова Е.А.", "room": "ауд. 511, к.17"},
        {"time": "11.40 - 13.15", "week": "Все недели", "title": "Охрана труда (лекция)", "teacher": "Чуешков В.В.", "room": "ауд. 382, к.1"},
    ],
    1: [
        {"time": "08.00 - 09.35", "week": "Все недели", "title": "Экономика энергетики (лекция)", "teacher": "Огонезов И.А.", "room": "ауд. 428, к.8"},
        {"time": "09.55 - 11.30", "week": "Все недели", "title": "Экономика энергетики (практика)", "teacher": "Огонезов И.А.", "room": "ауд. 428, к.8"},
    ],
    2: [
        {"time": "08.00 - 09.35", "week": "Все недели", "title": "Нагнетательные и расширительные машины (лекция)", "teacher": "Рекс А.Г.", "room": "ауд. 227, к.2"},
        {"time": "09.55 - 11.30", "week": "Все недели", "title": "Нагнетательные и расширительные машины (практика)", "teacher": "Рекс А.Г.", "room": "ауд. 227, к.2"},
        {"time": "11.40 - 13.15", "week": "1 нед.", "title": "Нагнетательные и расширительные машины (консультация по КР)", "teacher": "Рекс А.Г.", "room": "ауд. 227, к.2"},
    ],
    3: [
        {"time": "08.00 - 09.35", "week": "Все недели", "title": "Энергоэффективность системы кондиционирования воздуха (лекция)", "teacher": "Иващенко Е.Ю.", "room": "ауд. 227, к.2"},
        {"time": "09.55 - 11.30", "week": "Все недели", "title": "Энергоэффективность системы кондиционирования воздуха (лекция)", "teacher": "Иващенко Е.Ю.", "room": "ауд. 227, к.2"},
        ],
    4: [
        {"time": "08.00 - 09.35", "week": "1 нед.", "title": "Энергоэффективность системы кондиционирования воздуха (лаб.)", "teacher": "Иващенко Е.Ю.", "room": "ауд. 208, к.2"},
        {"time": "09.55 - 11.30", "week": "1 нед.", "title": "Энергоэффективность системы кондиционирования воздуха (практика)", "teacher": "Иващенко Е.Ю.", "room": "ауд. 208, к.2"},
        {"time": "11.40 - 13.15", "week": "1 нед.", "title": "Энергоэффективность системы кондиционирования воздуха (консультация по КР)", "teacher": "Иващенко Е.Ю.", "room": "ауд. 208, к.2"},
    ],
    5: [
        {"time": "08.00 - 09.35", "week": "Все недели", "title": "Энергоэффективность в жилищно-коммунальном хозяйстве (лекция)", "teacher": "Янцевич И.В.", "room": "ауд. 227, к.2"},
        {"time": "09.55 - 11.30", "week": "Все недели", "title": "Энергоэффективность в жилищно-коммунальном хозяйстве (практика)", "teacher": "Янцевич И.В.", "room": "ауд. 227, к.2"},
        {"time": "11.40 - 13.15", "week": "1 нед.", "title": "Энергоэффективность в жилищно-коммунальном хозяйстве (консультация по КР)", "teacher": "Янцевич И.В.", "room": "ауд. 227, к.2"},
    ],
    6: []
}

DAYS_NAMES = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

def format_day_schedule(day_index: int) -> str:
    lessons = SCHEDULE.get(day_index, [])
    if not lessons:
        return f"📅 {DAYS_NAMES[day_index]}:\n🎉 Выходной! Пар нет."
    
    text = f"📅 {DAYS_NAMES[day_index]}:\n\n"
    for item in lessons:
        week_info = f" ({item['week']})" if item['week'] != "Все недели" else ""
        text += f"⏰ {item['time']}{week_info}\n"
        text += f"📚 {item['title']}\n"
        text += f"👨‍🏫 {item['teacher']} | 📍 {item['room']}\n\n"
    return text

# Универсальное редактирование сообщения по кнопке
async def update_message(callback: types.CallbackQuery, text: str, reply_markup=None):
    try:
        await callback.message.edit_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer()

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass

    await message.answer(
        "Выберите желаемое действие...\n\n🎲 *Или просто тыкайте на кнопочки!*",
        reply_markup=main_keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "menu_main")
async def back_to_main_menu(callback: types.CallbackQuery):
    await update_message(
        callback,
        "Главное меню:",
        reply_markup=main_keyboard
    )

@dp.callback_query(F.data == "day_today")
async def today_button(callback: types.CallbackQuery):
    tz = pytz.timezone("Europe/Moscow")
    today = datetime.now(tz).weekday()
    await update_message(callback, format_day_schedule(today), reply_markup=main_keyboard)

@dp.callback_query(F.data == "day_tomorrow")
async def tomorrow_button(callback: types.CallbackQuery):
    tz = pytz.timezone("Europe/Moscow")
    tomorrow = (datetime.now(tz).weekday() + 1) % 7
    await update_message(callback, format_day_schedule(tomorrow), reply_markup=main_keyboard)

@dp.callback_query(F.data == "menu_days")
async def choose_day_menu(callback: types.CallbackQuery):
    await update_message(
        callback,
        "Выберите интересующий день недели из меню ниже 👇",
        reply_markup=days_keyboard
    )

@dp.callback_query(F.data.startswith("day_"))
async def show_specific_day(callback: types.CallbackQuery):
    day_index = int(callback.data.split("_")[1])
    await update_message(callback, format_day_schedule(day_index), reply_markup=days_keyboard)

@dp.callback_query(F.data == "toggle_sub")
async def toggle_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in subscribers:
        subscribers.remove(user_id)
        save_subscribers(subscribers)
        await update_message(callback, "❌ Вы отписались от утренней рассылки расписания.", reply_markup=main_keyboard)
    else:
        subscribers.add(user_id)
        save_subscribers(subscribers)
        await update_message(callback, "✅ Вы успешно подписались на рассылку!\nКаждое утро в 06:00 (МСК) вам будет приходить расписание на текущий день.", reply_markup=main_keyboard)

@dp.callback_query(F.data == "menu_other")
async def other_button(callback: types.CallbackQuery):
    await update_message(callback, "Группа: 10802123\nФакультет: ФТУГ (БНТУ)\nКурс: 4\nПритензии сюда: 9112380178176089", reply_markup=main_keyboard)

# --- АВТОМАТИЧЕСКАЯ РАССЫЛКА ---

async def send_daily_schedule():
    tz = pytz.timezone("Europe/Moscow")
    today = datetime.now(tz).weekday()
    schedule_text = f"☀️ Доброе утро! Расписание на сегодня:\n\n" + format_day_schedule(today)
    
    for user_id in list(subscribers):
        try:
            await bot.send_message(user_id, schedule_text, reply_markup=main_keyboard, parse_mode="Markdown")
        except Exception:
            subscribers.remove(user_id)
            save_subscribers(subscribers)

async def main():
    scheduler.add_job(send_daily_schedule, 'cron', hour=6, minute=0)
    scheduler.start()
    
    print("Бот на Inline-кнопках запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())