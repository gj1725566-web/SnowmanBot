from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import SessionLocal, Product, get_setting, set_setting
import os

ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

bot = Bot(token=os.getenv("ADMIN_BOT_TOKEN"))
dp = Dispatcher()

def is_admin(user_id: int):
    return user_id in ADMIN_IDS

# ---- FSM states ----
class AddProduct(StatesGroup):
    name = State()
    price = State()
    image = State()
    desc = State()

class EditProduct(StatesGroup):
    choose_field = State()
    new_value = State()

# ---- Entry point ----
@dp.message(Command("start"))
async def start(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Unauthorized.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Product", callback_data="add")],
        [InlineKeyboardButton(text="✏️ Edit Product", callback_data="edit_list")],
        [InlineKeyboardButton(text="🏦 Bank Account", callback_data="bank")],
    ])
    await msg.answer("Admin Panel", reply_markup=kb)

# ---- Add product ----
@dp.callback_query(F.data == "add")
async def add_start(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): return
    await cb.message.answer("Enter product name:")
    await state.set_state(AddProduct.name)

@dp.message(AddProduct.name)
async def add_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("Enter price (number):")
    await state.set_state(AddProduct.price)

@dp.message(AddProduct.price)
async def add_price(msg: Message, state: FSMContext):
    try:
        price = float(msg.text)
    except:
        await msg.answer("Invalid number, try again:")
        return
    await state.update_data(price=price)
    await msg.answer("Send product image (or /skip):")
    await state.set_state(AddProduct.image)

@dp.message(AddProduct.image, F.photo)
async def add_image(msg: Message, state: FSMContext):
    await state.update_data(image=msg.photo[-1].file_id)
    await msg.answer("Enter description (or /skip):")
    await state.set_state(AddProduct.desc)

@dp.message(AddProduct.image, Command("skip"))
async def add_image_skip(msg: Message, state: FSMContext):
    await state.update_data(image=None)
    await msg.answer("Enter description (or /skip):")
    await state.set_state(AddProduct.desc)

@dp.message(AddProduct.desc)
async def add_desc(msg: Message, state: FSMContext):
    data = await state.get_data()
    desc = "" if msg.text == "/skip" else msg.text
    s = SessionLocal()
    p = Product(name=data["name"], price=data["price"],
                image_file_id=data.get("image"), description=desc)
    s.add(p); s.commit(); s.close()
    await msg.answer(f"✅ Added: {data['name']} — {data['price']}")
    await state.clear()

# ---- Edit product ----
@dp.callback_query(F.data == "edit_list")
async def edit_list(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    s = SessionLocal()
    products = s.query(Product).all()
    s.close()
    if not products:
        await cb.message.answer("No products yet.")
        return
    btns = [[InlineKeyboardButton(text=f"{p.name} — {p.price}", callback_data=f"edit_{p.id}")]
            for p in products]
    await cb.message.answer("Choose product to edit:", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@dp.callback_query(F.data.startswith("edit_"))
async def edit_field(cb: CallbackQuery):
    pid = int(cb.data.split("_")[1])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Name", callback_data=f"f_name_{pid}"),
         InlineKeyboardButton(text="Price", callback_data=f"f_price_{pid}")],
        [InlineKeyboardButton(text="Image", callback_data=f"f_image_{pid}"),
         InlineKeyboardButton(text="Description", callback_data=f"f_desc_{pid}")],
    ])
    await cb.message.answer("Which field to edit?", reply_markup=kb)

@dp.callback_query(F.data.startswith("f_"))
async def edit_new_value(cb: CallbackQuery, state: FSMContext):
    _, field, pid = cb.data.split("_")
    await state.update_data(field=field, pid=int(pid))
    if field == "image":
        await cb.message.answer("Send new image:")
    else:
        await cb.message.answer(f"Enter new {field}:")
    await state.set_state(EditProduct.new_value)

@dp.message(EditProduct.new_value)
async def edit_save(msg: Message, state: FSMContext):
    data = await state.get_data()
    field, pid = data["field"], data["pid"]
    s = SessionLocal()
    p = s.query(Product).filter_by(id=pid).first()
    if not p:
        await msg.answer("Product not found.")
        s.close(); await state.clear(); return
    if field == "name":
        p.name = msg.text
    elif field == "price":
        try: p.price = float(msg.text)
        except: await msg.answer("Invalid number."); s.close(); return
    elif field == "desc":
        p.description = msg.text
    elif field == "image" and msg.photo:
        p.image_file_id = msg.photo[-1].file_id
    s.commit(); s.close()
    await msg.answer("✅ Updated.")
    await state.clear()

# ---- Bank ----
@dp.callback_query(F.data == "bank")
async def bank_view(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    current = get_setting("bank_info", "Not set")
    await cb.message.answer(f"Current bank info:\n{current}\n\nSend new bank info, or /cancel:")

@dp.message(Command("cancel"))
async def cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Cancelled.")

# To handle bank info input, you can add a separate state, omitted here
# In practice, use a dedicated State to receive bank input and call set_setting("bank_info", text)
