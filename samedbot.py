import asyncio
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

# Вставь сюда токен своего бота от @BotFather
TOKEN = "7599682006:AAEdtVENoWngqtgZ0XuL-abXB3utXN1LrGw"
ADMIN_ID = 6737680689
# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("samed_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            liters INTEGER DEFAULT 0,
            last_time INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("samed_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT liters, last_time FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"liters": row[0], "last_time": row[1]}
    return {"liters": 0, "last_time": 0}

def update_user(user_id, liters, last_time):
    conn = sqlite3.connect("samed_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, liters, last_time) 
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET liters = ?, last_time = ?
    """, (user_id, liters, last_time, liters, last_time))
    conn.commit()
    conn.close()

# --- ХЕНДЛЕРЫ ---

@dp.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "Привет еблан! Напиши 'сомед' чтобы выебать сомеда.\n\n"
        "Напиши 'сомед' чтобы выебать сомеда. (+2л)\n"
        "Можно выебать сомеда раз в 2 часа\n\n"
        "Команды:\n"
        "/status - уровень спермы\n"
        "/time - время до заливки сомеда"
    )
    await message.answer(text)

@dp.message(Command("status"))
async def cmd_status(message: Message):
    user = get_user(message.from_user.id)
    if user["liters"] == 0:
        await message.answer("🛢️ сомед еще пуст! Напишите 'сомед' чтобы выебать сомеда")
    else:
        await message.answer(f"✅ Всего в самеде: {user['liters']}л")

@dp.message(Command("time"))
async def cmd_time(message: Message):
    user_id = message.from_user.id
    
    # Если это админ, для него кулдауна нет, сразу пишем, что еще не выебали
    if user_id == ADMIN_ID:
        await message.answer("⏰ Вы еще не выебали сомеда!")
        return

    user = get_user(user_id)
    current_time = int(time.time())
    cooldown = 2 * 60 * 60  # 2 часа в секундах
    passed_time = current_time - user["last_time"]

    if passed_time < cooldown and user["last_time"] != 0:
        remaining = cooldown - passed_time
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        
        # Если осталось меньше минуты, напишем 1 мин для красоты
        if hours == 0 and minutes == 0:
            minutes = 1
            
        time_str = f"{hours}ч {minutes}мин" if hours > 0 else f"{minutes}мин"
        await message.answer(f"⚠️ Слишком рано! Следующая заправка возможна через {time_str}")
    else:
        await message.answer("⏰ Вы еще не выебали сомеда!")

@dp.message(F.text.lower().in_({"сомед", "бензин"}))
async def handle_action(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    current_time = int(time.time())
    cooldown = 2 * 60 * 60  # 2 часа в секундах
    
    passed_time = current_time - user["last_time"]
    
    # Если пишет админ, полностью игнорируем проверку времени
    if user_id == ADMIN_ID:
        new_liters = user["liters"] + 2
        update_user(user_id, new_liters, current_time)
        await message.answer(f"✅ Вы залили в самед 2л. Всего в самеде: {new_liters}л")
        return

    if passed_time < cooldown and user["last_time"] != 0:
        remaining = cooldown - passed_time
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        if hours == 0 and minutes == 0:
            minutes = 1
            
        time_str = f"{hours}ч {minutes}мин" if hours > 0 else f"{minutes}мин"
        await message.answer(f"⚠️ Слишком рано! Следующая заправка возможна через {time_str}")
    else:
        new_liters = user["liters"] + 2
        update_user(user_id, new_liters, current_time)
        await message.answer(f"✅ Вы залили в самед 2л. Всего в самеде: {new_liters}л")

# --- ЗАПУСК БОТА ---
async def main():
    init_db()
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())