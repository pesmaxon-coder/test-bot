from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardButton, KeyboardButton
from aiogram.types import BufferedInputFile
 
import database as db
from config import ADMIN_IDS
from keyboards import main_menu_kb
 
router = Router()
 
 
# ============ ADMIN TEKSHIRISH ============
 
async def is_admin(user_id: int) -> bool:
    return await db.is_admin_db(user_id)
 
 
# ============ KLAVIATURALAR ============
 
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
        KeyboardButton(text="👨‍💼 Adminlar"),
        KeyboardButton(text="📣 Xabar yuborish"),
    )
    builder.row(
        KeyboardButton(text="🏠 Asosiy menyu"),
    )
    return builder.as_markup(resize_keyboard=True)
 
 
def cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True)
 
 
def admins_list_kb(admins, owner_id):
    builder = InlineKeyboardBuilder()
    for adm in admins:
        # Asosiy admin o'chirilmasin
        if adm["id"] in ADMIN_IDS:
            builder.button(
                text=f"👑 {adm['full_name']} (Asosiy)",
                callback_data=f"admin_noop"
            )
        else:
            builder.button(
                text=f"❌ {adm['full_name']}",
                callback_data=f"del_admin_{adm['id']}"
            )
    builder.button(text="➕ Admin qo'shish", callback_data="add_admin_start")
    builder.adjust(1)
    return builder.as_markup()
 
 
# ============ STATES ============
 
class AddChannel(StatesGroup):
    name = State()
    username = State()
    url = State()
    channel_type = State()
 
 
class AddAdminState(StatesGroup):
    user_id = State()
 
 
class BroadcastState(StatesGroup):
    message = State()
 
 
# ============ ADMIN KIRISH ============
 
@router.message(F.text == "/admin")
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        return
    await message.answer(
        "👨‍💼 <b>Admin Panel</b>\n\nXush kelibsiz!",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )
 
 
@router.message(F.text == "🏠 Asosiy menyu")
async def back_to_main(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu_kb())
 
 
# ============ STATISTIKA ============
 
@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if not await is_admin(message.from_user.id):
        return
    users, tests, results = await db.get_stats()
    req_ch = await db.get_channels("required")
    paid_ch = await db.get_channels("paid")
    admins = await db.get_admins()
    await message.answer(
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{users}</b>\n"
        f"📋 Testlar: <b>{tests}</b>\n"
        f"✅ Tekshirishlar: <b>{results}</b>\n"
        f"📢 Majburiy kanallar: <b>{len(req_ch)}</b>\n"
        f"🔒 Pullik kanallar: <b>{len(paid_ch)}</b>\n"
        f"👨‍💼 Adminlar: <b>{len(admins)}</b>",
        parse_mode="HTML"
    )
 
 
# ============ TESTLAR RO'YXATI ============
 
@router.message(F.text == "📋 Testlar ro'yxati")
async def list_tests(message: Message):
    if not await is_admin(message.from_user.id):
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
    if not await is_admin(message.from_user.id):
        return
    users = await db.get_all_users()
    if not users:
        await message.answer("👥 Foydalanuvchilar yo'q.")
        return
    text = f"👥 <b>Foydalanuvchilar</b> ({len(users)} ta):\n\n"
    for i, u in enumerate(users[:25], 1):
        text += (
            f"{i}. {u['first_name']} {u['last_name']}\n"
            f"   📱 {u['phone']}\n"
            f"   🆔 <code>{u['id']}</code> | 📅 {u['registered_at'][:10]}\n\n"
        )
    if len(users) > 25:
        text += f"... va yana {len(users)-25} ta"
    await message.answer(text, parse_mode="HTML")
 
 
# ============ ADMINLAR BOSHQARUVI ============
 
@router.message(F.text == "👨‍💼 Adminlar")
async def manage_admins(message: Message):
    if not await is_admin(message.from_user.id):
        return
 
    admins = await db.get_admins()
 
    # Config dagi asosiy adminlarni ham ko'rsatish
    all_admins = []
    config_ids = set(ADMIN_IDS)
    db_ids = {a["id"] for a in admins}
 
    # Config adminlarini oldin qo'shish
    for aid in ADMIN_IDS:
        user = await db.get_user(aid)
        name = f"{user['first_name']} {user['last_name']}" if user else f"ID: {aid}"
        all_admins.append({"id": aid, "full_name": name})
 
    # DB adminlarini qo'shish (config da yo'qlarini)
    for adm in admins:
        if adm["id"] not in config_ids:
            all_admins.append(dict(adm))
 
    text = f"👨‍💼 <b>Adminlar ro'yxati</b> ({len(all_admins)} ta):\n\n"
    for i, adm in enumerate(all_admins, 1):
        crown = "👑" if adm["id"] in ADMIN_IDS else "👤"
        text += f"{i}. {crown} {adm['full_name']}\n   🆔 <code>{adm['id']}</code>\n\n"
 
    text += "\n❌ O'chirish uchun tugmani bosing.\n👑 — asosiy admin (o'chirib bo'lmaydi)"
 
    builder = InlineKeyboardBuilder()
    for adm in all_admins:
        if adm["id"] in ADMIN_IDS:
            builder.button(
                text=f"👑 {adm['full_name']}",
                callback_data="admin_noop"
            )
        else:
            builder.button(
                text=f"❌ {adm['full_name']}",
                callback_data=f"del_admin_{adm['id']}"
            )
    builder.button(text="➕ Yangi admin qo'shish", callback_data="add_admin_start")
    builder.adjust(1)
 
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
 
 
@router.callback_query(F.data == "admin_noop")
async def admin_noop(callback: CallbackQuery):
    await callback.answer("👑 Asosiy adminni o'chirib bo'lmaydi!", show_alert=True)
 
 
# Admin qo'shish
@router.callback_query(F.data == "add_admin_start")
async def add_admin_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.set_state(AddAdminState.user_id)
    await callback.message.answer(
        "➕ <b>Yangi admin qo'shish</b>\n\n"
        "Yangi admin bo'ladigan foydalanuvchining <b>Telegram ID</b> sini yuboring.\n\n"
        "💡 ID ni bilish uchun foydalanuvchi botga /start bosishi kerak,\n"
        "keyin <b>👥 Foydalanuvchilar</b> bo'limidan ID ni toping.",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()
 
 
@router.message(AddAdminState.user_id)
async def add_admin_get_id(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
        return
 
    try:
        new_admin_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Noto'g'ri ID! Faqat raqam kiriting.")
        return
 
    # Foydalanuvchi botda ro'yxatdan o'tganmi?
    user = await db.get_user(new_admin_id)
    if not user:
        await message.answer(
            "❌ Bu ID da foydalanuvchi topilmadi!\n\n"
            "Foydalanuvchi avval botga /start bosishi kerak."
        )
        return
 
    # Allaqachon adminmi?
    if await db.is_admin_db(new_admin_id):
        await message.answer("⚠️ Bu foydalanuvchi allaqachon admin!")
        await state.clear()
        return
 
    full_name = f"{user['first_name']} {user['last_name']}"
    await db.add_admin(new_admin_id, full_name)
    await state.clear()
 
    await message.answer(
        f"✅ <b>{full_name}</b> admin qilindi!\n\n"
        f"🆔 ID: <code>{new_admin_id}</code>\n\n"
        f"Endi u /admin buyrug'i orqali admin paneliga kira oladi.",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )
 
    # Yangi adminga xabar yuborish
    try:
        await message.bot.send_message(
            new_admin_id,
            "🎉 Siz admin qildingiz!\n\n"
            "Admin paneliga kirish uchun /admin yozing."
        )
    except Exception:
        pass
 
 
# Admin o'chirish
@router.callback_query(F.data.startswith("del_admin_"))
async def delete_admin(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
 
    # Faqat asosiy admin o'chira oladi
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Faqat asosiy admin boshqa adminlarni o'chira oladi!", show_alert=True)
        return
 
    admin_id = int(callback.data.split("_")[2])
 
    if admin_id in ADMIN_IDS:
        await callback.answer("👑 Asosiy adminni o'chirib bo'lmaydi!", show_alert=True)
        return
 
    user = await db.get_user(admin_id)
    name = f"{user['first_name']} {user['last_name']}" if user else str(admin_id)
 
    await db.remove_admin(admin_id)
    await callback.message.edit_text(
        f"✅ <b>{name}</b> admin ro'yxatidan o'chirildi.",
        parse_mode="HTML"
    )
    await callback.answer("✅ O'chirildi!")
 
    # O'chirilgan adminga xabar
    try:
        await callback.bot.send_message(
            admin_id,
            "ℹ️ Sizning admin huquqingiz bekor qilindi."
        )
    except Exception:
        pass
 
 
# ============ KANALLAR BOSHQARUVI ============
 
def channels_manage_kb(channels, ch_type):
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.button(
            text=f"❌ {ch['name']}",
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
    if not await is_admin(message.from_user.id):
        return
    channels = await db.get_channels("required")
    text = "📢 <b>Majburiy obuna kanallari</b>\n\n"
    if channels:
        for i, ch in enumerate(channels, 1):
            text += f"{i}. {ch['name']} — {ch['username']}\n"
    else:
        text += "Hozircha kanallar yo'q.\n"
    text += "\n❌ O'chirish uchun kanal tugmasini bosing."
    await message.answer(text, reply_markup=channels_manage_kb(channels, "required"), parse_mode="HTML")
 
 
@router.message(F.text == "🔒 Pullik kanallar")
async def manage_paid_channels(message: Message):
    if not await is_admin(message.from_user.id):
        return
    channels = await db.get_channels("paid")
    text = "🔒 <b>Pullik kanallar</b>\n\n"
    if channels:
        for i, ch in enumerate(channels, 1):
            text += f"{i}. {ch['name']} — {ch['username']}\n"
    else:
        text += "Hozircha pullik kanallar yo'q.\n"
    text += "\n❌ O'chirish uchun kanal tugmasini bosing."
    await message.answer(text, reply_markup=channels_manage_kb(channels, "paid"), parse_mode="HTML")
 
 
@router.callback_query(F.data.startswith("add_ch_"))
async def start_add_channel(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    ch_type = callback.data.split("_")[2]
    await state.update_data(channel_type=ch_type)
    await state.set_state(AddChannel.name)
    type_name = "majburiy obuna" if ch_type == "required" else "pullik"
    await callback.message.answer(
        f"➕ Yangi <b>{type_name}</b> kanal qo'shish\n\nKanal nomini kiriting:",
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
    await message.answer("Kanal username ni kiriting:\n(Masalan: @mening_kanal)")
 
 
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
    await message.answer("Kanal linkini kiriting:\n(Masalan: https://t.me/mening_kanal)")
 
 
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
 
 
@router.callback_query(F.data.startswith("del_ch_"))
async def delete_channel(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
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
    if not await is_admin(message.from_user.id):
        return
    builder = InlineKeyboardBuilder()
    for num, name in DESIGN_NAMES.items():
        builder.button(text=f"👁 {name}", callback_data=f"preview_design_{num}")
    builder.adjust(2)
    await message.answer(
        "🎨 <b>Sertifikat dizaynlari</b>\n\n"
        "Ko'rish uchun tugmani bosing:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
 
 
@router.callback_query(F.data.startswith("preview_design_"))
async def preview_design(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    num = int(callback.data.split("_")[2])
    from utils.certificate import generate_certificate
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
        caption=f"🎨 <b>{DESIGN_NAMES[num]}</b>",
        parse_mode="HTML",
        protect_content=True
    )
    await callback.answer()
 
 
# ============ XABAR YUBORISH ============
 
@router.message(F.text == "📣 Xabar yuborish")
async def start_broadcast(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.set_state(BroadcastState.message)
    await message.answer(
        "📣 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:",
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
