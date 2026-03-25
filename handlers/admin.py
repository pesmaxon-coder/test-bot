from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import KeyboardButton
from datetime import datetime

import database as db
from config import ADMIN_IDS
from keyboards import main_menu_kb, admin_main_kb, cancel_kb

router = Router()


async def is_admin(uid):
    return await db.is_admin_db(uid)


def dl_over(dl):
    if not dl:
        return False
    try:
        return datetime.now() > datetime.strptime(dl, "%d.%m.%Y %H:%M")
    except Exception:
        return False


class AddChannel(StatesGroup):
    name = State()
    username = State()
    url = State()
    ch_type = State()


class AddAdmin(StatesGroup):
    user_id = State()


class Broadcast(StatesGroup):
    msg = State()


# ===== ADMIN KIRISH =====

@router.message(F.text == "/admin")
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        return
    paused = await db.is_bot_paused()
    status = "⏸ TO'XTATILGAN" if paused else "▶️ ISHLAYAPTI"
    await message.answer(
        "👨‍💼 <b>Admin Panel</b>\n\n"
        "🤖 Bot holati: " + status + "\n\n"
        "Xush kelibsiz! Quyidagi bo'limlardan birini tanlang 👇",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )


@router.message(F.text == "🏠 Asosiy menyu")
async def to_main(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("🏠 Bosh sahifa.", reply_markup=main_menu_kb())


# ===== STATISTIKA =====

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if not await is_admin(message.from_user.id):
        return
    users, tests, results = await db.get_stats()
    req = await db.get_channels("required")
    paid = await db.get_channels("paid")
    admins = await db.get_admins()
    paused = await db.is_bot_paused()
    await message.answer(
        "📊 <b>Bot statistikasi</b>\n\n"
        "👥 Foydalanuvchilar: <b>" + str(users) + "</b>\n"
        "📋 Testlar: <b>" + str(tests) + "</b>\n"
        "✅ Tekshirishlar: <b>" + str(results) + "</b>\n"
        "📢 Majburiy kanallar: <b>" + str(len(req)) + "</b>\n"
        "🔒 Pullik kanallar: <b>" + str(len(paid)) + "</b>\n"
        "👨‍💼 Adminlar: <b>" + str(len(admins)) + "</b>\n\n"
        "🤖 Bot holati: " + ("⏸ <b>TO'XTATILGAN</b>" if paused else "▶️ <b>ISHLAYAPTI</b>"),
        parse_mode="HTML"
    )


# ===== TESTLAR =====

@router.message(F.text == "📋 Testlar ro'yxati")
async def list_tests(message: Message):
    if not await is_admin(message.from_user.id):
        return
    tests = await db.get_all_tests()
    if not tests:
        await message.answer("📭 Hech qanday test yo'q.")
        return
    b = InlineKeyboardBuilder()
    for t in tests[:20]:
        status = "🔴" if dl_over(t["deadline"]) else "🟢"
        b.button(
            text=status + " " + t["test_code"] + " | " + t["title"][:18],
            callback_data="atd_" + str(t["id"])
        )
    b.adjust(1)
    await message.answer(
        "📋 <b>Barcha testlar</b> (" + str(len(tests)) + " ta)\n\n"
        "🟢 Faol  |  🔴 Yopiq\n\n"
        "Ko'rish uchun tanlang 👇",
        reply_markup=b.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("atd_"))
async def admin_test_detail(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    test_id = int(callback.data.split("_")[1])
    tests = await db.get_all_tests()
    test = next((t for t in tests if t["id"] == test_id), None)
    if not test:
        await callback.answer("❌ Test topilmadi!", show_alert=True)
        return

    results = await db.get_test_results(test_id)
    dl = test["deadline"] or "Yo'q"
    status = "🔴 Yopiq" if dl_over(test["deadline"]) else "🟢 Faol"

    ans = test["answers"]
    ans_lines = []
    for i in range(0, len(ans), 10):
        chunk = list(ans[i:i+10])
        ans_lines.append(str(i+1) + "-" + str(i+len(chunk)) + ": " + " ".join(chunk))

    b = InlineKeyboardBuilder()
    b.button(text="👥 Ishtirokchilar", callback_data="atu_" + str(test_id))
    b.button(text="📊 Tahlil", callback_data="t_analysis_" + str(test_id))
    b.button(text="⏰ Deadlineni tugatish", callback_data="atdl_" + str(test_id))
    b.button(text="🗑 Testni o'chirish", callback_data="atdel_" + str(test_id))
    b.button(text="◀️ Orqaga", callback_data="atback")
    b.adjust(2, 1, 1, 1)

    await callback.message.edit_text(
        "📋 <b>" + test["title"] + "</b>\n\n"
        "🆔 ID: <code>" + test["test_code"] + "</code>\n"
        "🔢 Savollar: <b>" + str(test["question_count"]) + "</b> ta\n"
        "👤 Muallif: " + test["creator_name"] + "\n"
        "⏰ Deadline: " + dl + "\n"
        "📌 Holat: " + status + "\n"
        "👥 Ishtirokchilar: <b>" + str(len(results)) + "</b> ta\n\n"
        "📝 <b>Kalitlar:</b>\n" + "\n".join(ans_lines),
        reply_markup=b.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "atback")
async def admin_tests_back(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    tests = await db.get_all_tests()
    b = InlineKeyboardBuilder()
    for t in tests[:20]:
        status = "🔴" if dl_over(t["deadline"]) else "🟢"
        b.button(
            text=status + " " + t["test_code"] + " | " + t["title"][:18],
            callback_data="atd_" + str(t["id"])
        )
    b.adjust(1)
    await callback.message.edit_text(
        "📋 <b>Barcha testlar</b> (" + str(len(tests)) + " ta):",
        reply_markup=b.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("atu_"))
async def admin_test_users(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    test_id = int(callback.data.split("_")[1])
    tests = await db.get_all_tests()
    test = next((t for t in tests if t["id"] == test_id), None)
    results = await db.get_test_results(test_id)
    if not results:
        await callback.answer("📭 Hali hech kim topshirmagan!", show_alert=True)
        return
    avg = sum(r["percentage"] for r in results) / len(results)
    medals = ["🥇", "🥈", "🥉"]
    text = ("👥 <b>" + test["title"] + " — Ishtirokchilar</b>\n"
            "Jami: <b>" + str(len(results)) + "</b> | O'rtacha: <b>" + str(round(avg, 1)) + "%</b>\n\n")
    for i, r in enumerate(results[:20], 1):
        m = medals[i-1] if i <= 3 else str(i) + "."
        emoji = "🏆" if r["percentage"] >= 80 else "✅" if r["percentage"] >= 60 else "📊"
        text += (m + " " + emoji + " <b>" + r["first_name"] + " " + r["last_name"] + "</b>\n"
                 "   ✅ " + str(r["correct"]) + "/" + str(r["total"])
                 + " (" + str(round(r["percentage"], 1)) + "%) | 📅 " + r["taken_at"][:10] + "\n\n")
    if len(results) > 20:
        text += "... va yana " + str(len(results) - 20) + " ta"

    b = InlineKeyboardBuilder()
    for r in results[:10]:
        emoji = "🏆" if r["percentage"] >= 80 else "✅" if r["percentage"] >= 60 else "📊"
        b.button(
            text=emoji + " " + r["first_name"] + " " + r["last_name"] + " (" + str(round(r["percentage"])) + "%)",
            callback_data="rdetail_" + str(r["id"]) + "_" + str(test_id)
        )
    b.button(text="◀️ Orqaga", callback_data="atd_" + str(test_id))
    b.adjust(1)
    await callback.message.edit_text(text, reply_markup=b.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("atdl_"))
async def admin_end_dl_confirm(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    test_id = int(callback.data.split("_")[1])
    b = InlineKeyboardBuilder()
    b.button(text="✅ Ha, tugatish", callback_data="atdlyes_" + str(test_id))
    b.button(text="❌ Bekor", callback_data="atd_" + str(test_id))
    b.adjust(2)
    await callback.message.edit_text(
        "⏰ <b>Deadlineni tugatish</b>\n\n"
        "Bu testning deadlineni hoziroq tugatmoqchimisiz?\n"
        "⚠️ Shundan keyin hech kim topshira olmaydi!",
        reply_markup=b.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("atdlyes_"))
async def admin_end_dl_yes(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    test_id = int(callback.data.split("_")[1])
    await db.end_test_deadline(test_id)
    await callback.message.edit_text("✅ <b>Deadline tugatiildi!</b>\n\n🔴 Test yopiq.", parse_mode="HTML")
    await callback.answer("✅ OK!")


@router.callback_query(F.data.startswith("atdel_"))
async def admin_del_test_confirm(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    test_id = int(callback.data.split("_")[1])
    b = InlineKeyboardBuilder()
    b.button(text="✅ Ha, o'chirish", callback_data="atdelyes_" + str(test_id))
    b.button(text="❌ Bekor", callback_data="atd_" + str(test_id))
    b.adjust(2)
    await callback.message.edit_text(
        "🗑 <b>Testni o'chirish</b>\n\n"
        "⚠️ Test va uning <b>barcha natijalari</b> o'chiriladi!\n\n"
        "Davom etasizmi?",
        reply_markup=b.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("atdelyes_"))
async def admin_del_test_yes(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    test_id = int(callback.data.split("_")[1])
    await db.delete_test(test_id)
    await callback.message.edit_text("✅ <b>Test va natijalari o'chirildi!</b>", parse_mode="HTML")


# ===== FOYDALANUVCHILAR =====

@router.message(F.text == "👥 Foydalanuvchilar")
async def list_users(message: Message):
    if not await is_admin(message.from_user.id):
        return
    users = await db.get_all_users()
    if not users:
        await message.answer("📭 Foydalanuvchilar yo'q.")
        return
    text = "👥 <b>Foydalanuvchilar</b> (" + str(len(users)) + " ta):\n\n"
    for i, u in enumerate(users[:25], 1):
        text += (str(i) + ". 👤 <b>" + u["first_name"] + " " + u["last_name"] + "</b>\n"
                 "   📱 " + u["phone"] + "\n"
                 "   🆔 <code>" + str(u["id"]) + "</code>\n\n")
    if len(users) > 25:
        text += "... va yana " + str(len(users) - 25) + " ta"
    await message.answer(text, parse_mode="HTML")


# ===== KANALLAR =====

@router.message(F.text == "📢 Kanallar")
async def manage_req_channels(message: Message):
    if not await is_admin(message.from_user.id):
        return
    channels = await db.get_channels("required")
    text = "📢 <b>Majburiy obuna kanallari:</b>\n\n"
    for i, ch in enumerate(channels, 1):
        text += str(i) + ". " + ch["name"] + " — " + ch["username"] + "\n"
    if not channels:
        text += "📭 Kanallar yo'q.\n"
    text += "\n🗑 O'chirish uchun tugmani bosing."
    b = InlineKeyboardBuilder()
    for ch in channels:
        b.button(text="🗑 " + ch["name"], callback_data="delch_" + str(ch["id"]))
    b.button(text="➕ Yangi kanal qo'shish", callback_data="addch_required")
    b.adjust(1)
    await message.answer(text, reply_markup=b.as_markup(), parse_mode="HTML")


@router.message(F.text == "🔒 Pullik kanallar")
async def manage_paid_channels(message: Message):
    if not await is_admin(message.from_user.id):
        return
    channels = await db.get_channels("paid")
    text = "🔒 <b>Pullik kanallar:</b>\n\n"
    for i, ch in enumerate(channels, 1):
        text += str(i) + ". " + ch["name"] + " — " + ch["username"] + "\n"
    if not channels:
        text += "📭 Kanallar yo'q.\n"
    b = InlineKeyboardBuilder()
    for ch in channels:
        b.button(text="🗑 " + ch["name"], callback_data="delch_" + str(ch["id"]))
    b.button(text="➕ Yangi kanal qo'shish", callback_data="addch_paid")
    b.adjust(1)
    await message.answer(text, reply_markup=b.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("delch_"))
async def delete_channel(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    ch_id = int(callback.data.split("_")[1])
    await db.delete_channel(ch_id)
    await callback.message.edit_text("✅ Kanal o'chirildi!")
    await callback.answer("✅ OK!")


@router.callback_query(F.data.startswith("addch_"))
async def start_add_channel(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    ch_type = callback.data.split("_")[1]
    await state.update_data(ch_type=ch_type)
    await state.set_state(AddChannel.name)
    type_name = "majburiy obuna" if ch_type == "required" else "pullik"
    await callback.message.answer(
        "➕ <b>Yangi " + type_name + " kanal qo'shish</b>\n\n"
        "📌 Kanal nomini kiriting\n(masalan: Asosiy kanal):",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddChannel.name)
async def add_ch_name(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AddChannel.username)
    await message.answer("🔗 Kanal username kiriting\n(masalan: @mening_kanal):")


@router.message(AddChannel.username)
async def add_ch_username(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
        return
    username = message.text.strip()
    if not username.startswith("@"):
        username = "@" + username
    await state.update_data(username=username)
    await state.set_state(AddChannel.url)
    await message.answer("🌐 Kanal linkini kiriting\n(masalan: https://t.me/mening_kanal):")


@router.message(AddChannel.url)
async def add_ch_url(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
        return
    data = await state.get_data()
    await db.add_channel(data["name"], data["username"], message.text.strip(), data["ch_type"])
    await state.clear()
    await message.answer(
        "✅ <b>Kanal qo'shildi!</b>\n\n"
        "📌 Nom: " + data["name"] + "\n"
        "🔗 Username: " + data["username"],
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )


# ===== SERTIFIKAT DIZAYNLARI =====

@router.message(F.text == "🎨 Sertifikat dizaynlari")
async def show_designs(message: Message):
    if not await is_admin(message.from_user.id):
        return
    b = InlineKeyboardBuilder()
    for i in range(1, 9):
        b.button(text="🎨 Dizayn " + str(i), callback_data="prevd_" + str(i))
    b.adjust(4)
    await message.answer(
        "🎨 <b>Sertifikat dizaynlari</b>\n\n"
        "Ko'rish uchun tugmani bosing 👇",
        reply_markup=b.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("prevd_"))
async def preview_design(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    num = int(callback.data.split("_")[1])
    from utils.certificate import generate_certificate
    await callback.message.answer("🎨 Namuna tayyorlanmoqda...")
    buf = generate_certificate(
        design_num=num,
        full_name="Alijon Alijonov",
        test_title="Ingliz tili",
        correct=18,
        total=20,
        author="Abbos Mekhmonaliev"
    )
    await callback.message.answer_photo(
        photo=BufferedInputFile(buf.read(), filename="namuna.png"),
        caption="🎨 <b>Dizayn " + str(num) + "</b>",
        parse_mode="HTML",
        protect_content=True
    )
    await callback.answer()


# ===== ADMINLAR =====

@router.message(F.text == "👨‍💼 Adminlar")
async def manage_admins(message: Message):
    if not await is_admin(message.from_user.id):
        return
    admins = await db.get_admins()
    text = "👨‍💼 <b>Adminlar ro'yxati:</b>\n\n"
    for aid in ADMIN_IDS:
        user = await db.get_user(aid)
        name = user["first_name"] + " " + user["last_name"] if user else "ID:" + str(aid)
        text += "👑 <b>" + name + "</b> (asosiy)\n🆔 <code>" + str(aid) + "</code>\n\n"
    for adm in admins:
        if adm["id"] not in ADMIN_IDS:
            text += "👤 <b>" + adm["full_name"] + "</b>\n🆔 <code>" + str(adm["id"]) + "</code>\n\n"

    b = InlineKeyboardBuilder()
    for adm in admins:
        if adm["id"] not in ADMIN_IDS:
            b.button(text="🗑 " + adm["full_name"], callback_data="deladm_" + str(adm["id"]))
    b.button(text="➕ Yangi admin qo'shish", callback_data="addadm")
    b.adjust(1)
    await message.answer(text, reply_markup=b.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "addadm")
async def start_add_admin(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.set_state(AddAdmin.user_id)
    await callback.message.answer(
        "➕ <b>Yangi admin qo'shish</b>\n\n"
        "🆔 Foydalanuvchining Telegram ID sini kiriting.\n\n"
        "💡 ID ni <b>👥 Foydalanuvchilar</b> bo'limidan toping.",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddAdmin.user_id)
async def do_add_admin(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
        return
    try:
        new_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Noto'g'ri ID! Faqat raqam kiriting.")
        return
    user = await db.get_user(new_id)
    if not user:
        await message.answer(
            "❌ Bu ID da foydalanuvchi topilmadi!\n"
            "💡 Avval botga /start bosishi kerak."
        )
        return
    if await db.is_admin_db(new_id):
        await message.answer("⚠️ Bu foydalanuvchi allaqachon admin!")
        await state.clear()
        return
    full_name = user["first_name"] + " " + user["last_name"]
    await db.add_admin(new_id, full_name)
    await state.clear()
    await message.answer(
        "✅ <b>" + full_name + "</b> admin qilindi!\n\n"
        "🆔 ID: <code>" + str(new_id) + "</code>\n"
        "💡 Endi /admin buyrug'i orqali kira oladi.",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )
    try:
        await message.bot.send_message(
            new_id,
            "🎉 <b>Siz admin qildingiz!</b>\n\n"
            "👨‍💼 Admin paneliga kirish uchun /admin yozing.",
            parse_mode="HTML"
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("deladm_"))
async def delete_admin(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Faqat asosiy admin boshqa adminlarni o'chira oladi!", show_alert=True)
        return
    adm_id = int(callback.data.split("_")[1])
    await db.remove_admin(adm_id)
    await callback.message.edit_text("✅ Admin ro'yxatidan o'chirildi!", parse_mode="HTML")
    await callback.answer("✅ OK!")
    try:
        await callback.bot.send_message(adm_id, "ℹ️ Sizning admin huquqingiz bekor qilindi.")
    except Exception:
        pass


# ===== XABAR YUBORISH =====

@router.message(F.text == "📣 Xabar yuborish")
async def start_broadcast(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.set_state(Broadcast.msg)
    await message.answer(
        "📣 <b>Xabar yuborish</b>\n\n"
        "Barcha foydalanuvchilarga yuboriladigan xabarni yozing:\n"
        "(Matn, rasm yoki video bo'lishi mumkin)",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )


@router.message(Broadcast.msg)
async def do_broadcast(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
        return
    await state.clear()
    users = await db.get_all_users()
    sent, failed = 0, 0
    await message.answer("📤 Yuborilmoqda... (" + str(len(users)) + " ta foydalanuvchi)")
    for user in users:
        try:
            await message.copy_to(user["id"], protect_content=True)
            sent += 1
        except Exception:
            failed += 1
    await message.answer(
        "✅ <b>Xabar yuborildi!</b>\n\n"
        "✅ Muvaffaqiyatli: <b>" + str(sent) + "</b>\n"
        "❌ Xatolik: <b>" + str(failed) + "</b>",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )


# ===== BOT TO'XTATISH =====

@router.message(F.text == "⏸ Botni to'xtatish")
async def pause_bot(message: Message):
    if not await is_admin(message.from_user.id):
        return
    await db.set_bot_status(paused=True)
    b = ReplyKeyboardBuilder()
    b.button(text="▶️ Botni yoqish")
    await message.answer(
        "⏸ <b>Bot vaqtincha to'xtatildi!</b>\n\n"
        "🚫 Foydalanuvchilar botdan foydalana olmaydi.\n"
        "▶️ Qayta yoqish uchun tugmani bosing 👇",
        reply_markup=b.as_markup(resize_keyboard=True),
        parse_mode="HTML"
    )


@router.message(F.text == "▶️ Botni yoqish")
async def resume_bot(message: Message):
    if not await is_admin(message.from_user.id):
        return
    await db.set_bot_status(paused=False)
    await message.answer(
        "▶️ <b>Bot qayta yoqildi!</b>\n\n"
        "✅ Foydalanuvchilar botdan foydalana oladi.",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )


# ===== SHARED CALLBACKS =====

@router.callback_query(F.data.startswith("rdetail_"))
async def result_detail_admin(callback: CallbackQuery):
    parts = callback.data.split("_")
    result_id = int(parts[1])
    test_id = int(parts[2])
    results = await db.get_test_results(test_id)
    result = next((r for r in results if r["id"] == result_id), None)
    if not result:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return
    tests = await db.get_all_tests()
    test = next((t for t in tests if t["id"] == test_id), None)
    ua = result["user_answers"]
    ca = test["answers"]
    lines = []
    for i in range(test["question_count"]):
        u = ua[i] if i < len(ua) else "-"
        c = ca[i]
        if u == c:
            lines.append(str(i+1) + ". ✅ " + u)
        else:
            lines.append(str(i+1) + ". ❌ " + u + " → " + c)
    header = (
        "🔍 <b>" + result["first_name"] + " " + result["last_name"] + "</b>\n"
        "📌 " + test["title"] + " | 🆔 " + test["test_code"] + "\n"
        "✅ To'g'ri: <b>" + str(result["correct"]) + "/" + str(result["total"]) + "</b>"
        " (" + str(round(result["percentage"], 1)) + "%)\n"
        "📅 " + result["taken_at"][:16] + "\n\n"
        "📋 Tahlil (✅ to'g'ri | ❌ xato → to'g'ri):\n\n"
    )
    chunks = [lines[i:i+50] for i in range(0, len(lines), 50)]
    await callback.message.answer(header + "\n".join(chunks[0]), parse_mode="HTML")
    for ch in chunks[1:]:
        await callback.message.answer("\n".join(ch))
    await callback.answer()