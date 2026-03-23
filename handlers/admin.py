from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
 
import database as db
from config import ADMIN_IDS
from keyboards import main_menu_kb
 
router = Router()
 
 
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
 
 
# ============ ADMIN MENYU ============
 
def admin_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📊 Statistika"),
        KeyboardButton(text="📋 Testlar ro'yxati"),
    )
    builder.row(
        KeyboardButton(text="📢 Kanallar boshqaruvi"),
        KeyboardButton(text="🔒 Pullik kanallar"),
    )
    builder.row(
        KeyboardButton(text="🎨 Sertifikat dizaynlari"),
        KeyboardButton(text="👥 Foydalanuvchilar"),
    )
    builder.row(
        KeyboardButton(text="📣 Xabar yuborish"),
        KeyboardButton(text="🏠 Asosiy menyu"),
    )
    return builder.as_markup(resize_keyboard=True)
 
 
def cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True)
 
 
# ============ STATES ============
 
class AddChannel(StatesGroup):
    name = State()
    username = State()
    url = State()
    channel_type = State()  # 'required' or 'paid'
 
 
class BroadcastState(StatesGroup):
    message = State()
 
 
# ============ ADMIN KIRISH ============
 
@router.message(F.text == "/admin")
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        return
    await message.answer(
        "👨‍💼 <b>Admin Panel</b>\n\nXush kelibsiz!",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )
 
 
@router.message(F.text == "🏠 Asosiy menyu")
async def back_to_main(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu_kb())
 
 
# ============ STATISTIKA ============
 
@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    users, tests, results = await db.get_stats()
    channels = await db.get_channels("required")
    paid = await db.get_channels("paid")
    await message.answer(
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{users}</b>\n"
        f"📋 Testlar: <b>{tests}</b>\n"
        f"✅ Tekshirishlar: <b>{results}</b>\n"
        f"📢 Majburiy kanallar: <b>{len(channels)}</b>\n"
        f"🔒 Pullik kanallar: <b>{len(paid)}</b>",
        parse_mode="HTML"
    )
 
 
# ============ TESTLAR RO'YXATI ============
 
@router.message(F.text == "📋 Testlar ro'yxati")
async def list_tests(message: Message):
    if not is_admin(message.from_user.id):
        return
    tests = await db.get_all_tests()
    if not tests:
        await message.answer("📭 Hech qanday test yo'q.")
        return
 
    text = f"📋 <b>Barcha testlar</b> ({len(tests)} ta):\n\n"
    for i, t in enumerate(tests[:30], 1):
        text += (
            f"{i}. 🆔 <code>{t['test_code']}</code>\n"
            f"   📌 {t['title']}\n"
            f"   👤 {t['creator_name']} | 🔢 {t['question_count']} ta\n"
            f"   📅 {t['created_at'][:10]}\n\n"
        )
    if len(tests) > 30:
        text += f"... va yana {len(tests)-30} ta test"
    await message.answer(text, parse_mode="HTML")
 
 
# ============ FOYDALANUVCHILAR ============
 
@router.message(F.text == "👥 Foydalanuvchilar")
async def list_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    users = await db.get_all_users()
    if not users:
        await message.answer("👥 Foydalanuvchilar yo'q.")
        return
 
    text = f"👥 <b>Foydalanuvchilar</b> ({len(users)} ta):\n\n"
    for i, u in enumerate(users[:25], 1):
        text += (
            f"{i}. {u['first_name']} {u['last_name']}\n"
            f"   📱 {u['phone']} | 🎨 #{u['cert_design']}\n"
            f"   📅 {u['registered_at'][:10]}\n\n"
        )
    if len(users) > 25:
        text += f"... va yana {len(users)-25} ta"
    await message.answer(text, parse_mode="HTML")
 
 
# ============ MAJBURIY KANALLAR ============
 
def channels_manage_kb(channels, ch_type):
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.button(
            text=f"🗑 {ch['name']}",
            callback_data=f"del_ch_{ch['id']}"
        )
    builder.button(
        text="➕ Kanal qo'shish",
        callback_data=f"add_ch_{ch_type}"
    )
    builder.adjust(1)
    return builder.as_markup()
 
 
@router.message(F.text == "📢 Kanallar boshqaruvi")
async def manage_required_channels(message: Message):
    if not is_admin(message.from_user.id):
        return
    channels = await db.get_channels("required")
    text = "📢 <b>Majburiy obuna kanallari</b>\n\n"
    if channels:
        for i, ch in enumerate(channels, 1):
            text += f"{i}. {ch['name']} — {ch['username']}\n"
    else:
        text += "Hozircha kanallar yo'q.\n"
    text += "\n🗑 O'chirish uchun kanal tugmasini bosing."
    await message.answer(
        text,
        reply_markup=channels_manage_kb(channels, "required"),
        parse_mode="HTML"
    )
 
 
@router.message(F.text == "🔒 Pullik kanallar")
async def manage_paid_channels(message: Message):
    if not is_admin(message.from_user.id):
        return
    channels = await db.get_channels("paid")
    text = "🔒 <b>Pullik kanallar</b>\n\n"
    if channels:
        for i, ch in enumerate(channels, 1):
            text += f"{i}. {ch['name']} — {ch['username']}\n"
    else:
        text += "Hozircha pullik kanallar yo'q.\n"
    text += "\n🗑 O'chirish uchun kanal tugmasini bosing."
    await message.answer(
        text,
        reply_markup=channels_manage_kb(channels, "paid"),
        parse_mode="HTML"
    )
 
 
# Kanal qo'shish
@router.callback_query(F.data.startswith("add_ch_"))
async def start_add_channel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    ch_type = callback.data.split("_")[2]
    await state.update_data(channel_type=ch_type)
    await state.set_state(AddChannel.name)
    type_name = "majburiy obuna" if ch_type == "required" else "pullik"
    await callback.message.answer(
        f"➕ Yangi <b>{type_name}</b> kanal qo'shish\n\n"
        f"Kanal nomini kiriting:\n(Masalan: Asosiy kanal)",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()
 
 
@router.message(AddChannel.name)
async def add_channel_name(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AddChannel.username)
    await message.answer(
        "Kanal username ni kiriting:\n(Masalan: @mening_kanal)"
    )
 
 
@router.message(AddChannel.username)
async def add_channel_username(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
        return
    username = message.text.strip()
    if not username.startswith("@"):
        username = "@" + username
    await state.update_data(username=username)
    await state.set_state(AddChannel.url)
    await message.answer(
        "Kanal linkini kiriting:\n(Masalan: https://t.me/mening_kanal)"
    )
 
 
@router.message(AddChannel.url)
async def add_channel_url(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
        return
    data = await state.get_data()
    await db.add_channel(
        name=data["name"],
        username=data["username"],
        url=message.text.strip(),
        ch_type=data["channel_type"]
    )
    await state.clear()
    type_name = "Majburiy obuna" if data["channel_type"] == "required" else "Pullik"
    await message.answer(
        f"✅ <b>{type_name} kanal qo'shildi!</b>\n\n"
        f"📌 Nom: {data['name']}\n"
        f"🔗 Username: {data['username']}",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )
 
 
# Kanal o'chirish
@router.callback_query(F.data.startswith("del_ch_"))
async def delete_channel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    ch_id = int(callback.data.split("_")[2])
    await db.delete_channel(ch_id)
    await callback.message.edit_text("✅ Kanal o'chirildi!")
    await callback.answer("✅ O'chirildi!")
 
 
# ============ SERTIFIKAT DIZAYNLARI ============
 
DESIGN_NAMES = {
    1: "1️⃣ Klassik to'q ko'k",
    2: "2️⃣ Yashil-oltin to'lqin",
    3: "3️⃣ Ko'k band",
    4: "4️⃣ Yashil zamonaviy",
    5: "5️⃣ Qizil burchak",
    6: "6️⃣ Vintage/Krem",
    7: "7️⃣ Rang-barang",
    8: "8️⃣ To'q geometrik",
}
 
 
@router.message(F.text == "🎨 Sertifikat dizaynlari")
async def show_designs(message: Message):
    if not is_admin(message.from_user.id):
        return
 
    builder = InlineKeyboardBuilder()
    for num, name in DESIGN_NAMES.items():
        builder.button(text=f"👁 {name}", callback_data=f"preview_design_{num}")
    builder.adjust(1)
 
    await message.answer(
        "🎨 <b>Sertifikat dizaynlari</b>\n\n"
        "Ko'rish uchun dizayn tugmasini bosing:\n\n"
        "Foydalanuvchilar o'z sozlamalarida istalgan dizaynni tanlashlari mumkin.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
 
 
@router.callback_query(F.data.startswith("preview_design_"))
async def preview_design(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    num = int(callback.data.split("_")[2])
    from utils.certificate import generate_certificate
    from aiogram.types import BufferedInputFile
 
    await callback.message.answer("🎨 Namuna tayyorlanmoqda...")
    buf = generate_certificate(
        design_num=num,
        full_name="Alijon Alijonov",
        test_title="Matematika",
        correct=18,
        total=20,
        author="Test Muallifi"
    )
    await callback.message.answer_photo(
        photo=BufferedInputFile(buf.read(), filename="namuna.png"),
        caption=f"🎨 <b>{DESIGN_NAMES[num]}</b>\n\n"
                f"Bu dizayn foydalanuvchilar tomonidan tanlanishi mumkin.",
        parse_mode="HTML",
        protect_content=True
    )
    await callback.answer()
 
 
# ============ XABAR YUBORISH ============
 
@router.message(F.text == "📣 Xabar yuborish")
async def start_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(BroadcastState.message)
    await message.answer(
        "📣 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:\n"
        "(Matn, rasm yoki video bo'lishi mumkin)",
        reply_markup=cancel_kb()
    )
 
 
@router.message(BroadcastState.message)
async def do_broadcast(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
        return
 
    await state.clear()
    users = await db.get_all_users()
    sent, failed = 0, 0
 
    await message.answer(f"📤 Yuborilmoqda... ({len(users)} ta foydalanuvchi)")
 
    for user in users:
        try:
            await message.copy_to(user["id"], protect_content=True)
            sent += 1
        except Exception:
            failed += 1
 
    await message.answer(
        f"✅ <b>Xabar yuborildi!</b>\n\n"
        f"✅ Muvaffaqiyatli: {sent}\n"
        f"❌ Xatolik: {failed}",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )
