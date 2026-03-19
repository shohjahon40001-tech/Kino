import logging
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- RENDER UCHUN UYG'OTUVCHI QISM (FLASK) ---
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot holati: Faol ✅"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT SOZLAMALARI ---
API_TOKEN = '8613693212:AAGPxSce8tQEHI-iSLR3YGJalr40PdyQFSc'
ADMIN_ID = 6363065057  # O'zingizning Telegram ID raqamingizni yozing
ADMIN_PASSWORD = "Shohjahon"

# Ma'lumotlar bazasini yaratish
conn = sqlite3.connect('kino_bazasi.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS movies
                  (code TEXT PRIMARY KEY, file_id TEXT, name TEXT)''')
conn.commit()

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class AdminStates(StatesGroup):
    waiting_for_password = State()
    adding_movie_code = State()
    adding_movie_file = State()
    deleting_movie = State()

# --- FOYDALANUVCHILAR UCHUN ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(f"👋 Salom {message.from_user.first_name}!\n🎬 Kino kodini yuboring:")

@dp.message(F.text.isdigit())
async def get_movie(message: types.Message):
    cursor.execute("SELECT file_id, name FROM movies WHERE code = ?", (message.text,))
    res = cursor.fetchone()
    if res:
        await message.answer_video(res[0], caption=f"🎬 Nomi: {res[1]}\n🆔 Kod: {message.text}")
    else:
        await message.answer("❌ Bu kod bilan kino topilmadi.")

# --- ADMIN PANEL ---
@dp.message(Command("admin"))
async def admin_login(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🔑 Admin parolini kiriting:")
        await state.set_state(AdminStates.waiting_for_password)

@dp.message(AdminStates.waiting_for_password)
async def check_pass(message: types.Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        kb = [
            [types.KeyboardButton(text="➕ Kino qo'shish")],
            [types.KeyboardButton(text="🗑 Kino o'chirish")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("✅ Xush kelibsiz!", reply_markup=keyboard)
        await state.clear()
    else:
        await message.answer("❌ Xato parol!")

@dp.message(F.text == "➕ Kino qo'shish")
async def add_movie_start(message: types.Message, state: FSMContext):
    await message.answer("Kino kodini kiriting:")
    await state.set_state(AdminStates.adding_movie_code)

@dp.message(AdminStates.adding_movie_code)
async def add_code(message: types.Message, state: FSMContext):
    await state.update_data(m_code=message.text)
    await message.answer("Kino faylini yuboring:")
    await state.set_state(AdminStates.adding_movie_file)

@dp.message(AdminStates.adding_movie_file, F.video)
async def add_file(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cursor.execute("INSERT OR REPLACE INTO movies VALUES (?, ?, ?)",
                   (data['m_code'], message.video.file_id, "Kino"))
    conn.commit()
    await message.answer(f"✅ Saqlandi! Kod: {data['m_code']}")
    await state.clear()

# --- ISHGA TUSHIRISH ---
async def main():
    logging.basicConfig(level=logging.INFO)
    keep_alive() # Mana shu funksiya Render'da botni uyg'oq saqlaydi
    print("🚀 Bot Render uchun tayyor holatda ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
