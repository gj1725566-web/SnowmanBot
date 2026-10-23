from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import SessionLocal, Product, get_setting
import os

bot = Bot(token=os.getenv("SHOP_BOT_TOKEN"))
dp = Dispatcher()

@dp.message(Command("start"))
async def start(msg: Message):
    s = SessionLocal()
    products = s.query(Product).all()
    s.close()
    if not products:
        await msg.answer("Shop is empty.")
        return
    btns = [[InlineKeyboardButton(text=f"{p.name} — ${p.price}", callback_data=f"view_{p.id}")]
            for p in products]
    await msg.answer("🛍 Products:", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@dp.callback_query(F.data.startswith("view_"))
async def view_product(cb: CallbackQuery):
    pid = int(cb.data.split("_")[1])
    s = SessionLocal()
    p = s.query(Product).filter_by(id=pid).first()
    s.close()
    if not p:
        await cb.answer("Not found."); return
    text = f"*{p.name}*\n\n{p.description or ''}\n\n💰 ${p.price}"
    if p.image_file_id:
        await cb.message.answer_photo(p.image_file_id, caption=text, parse_mode="Markdown")
    else:
        await cb.message.answer(text, parse_mode="Markdown")
