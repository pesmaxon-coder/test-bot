from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from keyboards import main_menu_kb

router = Router()


# ===== FOYDALANUVCHI: Pullik kanallar ro'yxati =====

@router.message(F.text == "🔒 Pullik kanallar")
async def show_paid_channels(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting!")
        return

    channels = await db.get_channels("paid")
    if not channels:
        await message.answer(
            "📭 <b>Hozircha pullik kanallar yo'q.</b>\n\n"
            "Tez orada qo'shiladi! 🔜",
            parse_mode="HTML"
        )
        return

    text = "🔒 <b>Pullik kanallar</b>\n\n"
    text += "Quyidagi kanallardan biriga kirish uchun so'rov yuboring.\n"
    text += "Admin tasdiqlasa, <b>bir martalik kirish havolasi</b> yuboriladi. 🔑\n\n"

    b = InlineKeyboardBuilder()
    for ch in channels:
        # Foydalanuvchining so'rovini tekshirish
        req = await db.get_user_paid_request(message.from_user.id, ch["id"])
        if req:
            if req["status"] == "pending":
                status_text = "⏳ Kutilmoqda"
                b.button(
                    text=f"⏳ {ch['name']} — Kutilmoqda",
                    callback_data=f"paid_status_{ch['id']}"
                )
            elif req["status"] == "approved":
                status_text = "✅ Tasdiqlangan"
                b.button(
                    text=f"✅ {ch['name']} — Link olindi",
                    callback_data=f"paid_status_{ch['id']}"
                )
            elif req["status"] == "rejected":
                b.button(
                    text=f"❌ {ch['name']} — Rad etilgan (qayta so'rov)",
                    callback_data=f"paid_request_{ch['id']}"
                )
        else:
            b.button(
                text=f"📩 {ch['name']} — So'rov yuborish",
                callback_data=f"paid_request_{ch['id']}"
            )

    b.adjust(1)
    await message.answer(text, reply_markup=b.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("paid_request_"))
async def send_paid_request(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    channel_id = int(callback.data.split("_")[2])

    user = await db.get_user(user_id)
    if not user:
        await callback.answer("❌ Avval ro'yxatdan o'ting!", show_alert=True)
        return

    channel_list = await db.get_channels("paid")
    channel = next((c for c in channel_list if c["id"] == channel_id), None)
    if not channel:
        await callback.answer("❌ Kanal topilmadi!", show_alert=True)
        return

    # So'rov yaratish
    req_id = await db.create_paid_request(user_id, channel_id)
    if req_id is None:
        await callback.answer("⚠️ Siz allaqachon so'rov yuborgansiz! Admin ko'rib chiqmoqda.", show_alert=True)
        return

    # Foydalanuvchiga xabar
    await callback.message.edit_text(
        f"✅ <b>So'rovingiz yuborildi!</b>\n\n"
        f"📢 Kanal: <b>{channel['name']}</b>\n"
        f"🆔 So'rov raqami: <code>#{req_id}</code>\n\n"
        f"⏳ Admin ko'rib chiqishi bilan sizga <b>bir martalik kirish havolasi</b> yuboriladi.\n"
        f"Sabr qiling! 🙏",
        parse_mode="HTML"
    )

    # Adminlarga xabarnoma yuborish
    full_name = f"{user['first_name']} {user['last_name']}"
    admins = await db.get_admins()
    from config import ADMIN_IDS
    admin_ids = list(ADMIN_IDS) + [a["id"] for a in admins]

    b = InlineKeyboardBuilder()
    b.button(text="✅ Tasdiqlash", callback_data=f"adm_approve_{req_id}")
    b.button(text="❌ Rad etish", callback_data=f"adm_reject_{req_id}")
    b.adjust(2)

    notif_text = (
        f"🔔 <b>Yangi pullik kanal so'rovi!</b>\n\n"
        f"👤 Foydalanuvchi: <b>{full_name}</b>\n"
        f"📱 Telefon: {user['phone']}\n"
        f"🆔 TG ID: <code>{user_id}</code>\n\n"
        f"📢 Kanal: <b>{channel['name']}</b> ({channel['username']})\n"
        f"🔢 So'rov №: <b>#{req_id}</b>"
    )

    for admin_id in set(admin_ids):
        try:
            await bot.send_message(admin_id, notif_text, reply_markup=b.as_markup(), parse_mode="HTML")
        except Exception:
            pass

    await callback.answer("✅ So'rov yuborildi!")


@router.callback_query(F.data.startswith("paid_status_"))
async def check_paid_status(callback: CallbackQuery):
    channel_id = int(callback.data.split("_")[2])
    req = await db.get_user_paid_request(callback.from_user.id, channel_id)
    if not req:
        await callback.answer("❌ So'rov topilmadi!", show_alert=True)
        return

    if req["status"] == "pending":
        await callback.answer("⏳ So'rovingiz hali ko'rib chiqilmagan. Kuting!", show_alert=True)
    elif req["status"] == "approved":
        link = req["invite_link"] or "—"
        await callback.answer(f"✅ Tasdiqlangan!\n\nHavola: {link}", show_alert=True)
    elif req["status"] == "rejected":
        await callback.answer("❌ So'rovingiz rad etilgan. Qayta so'rov yuborishingiz mumkin.", show_alert=True)


# ===== ADMIN: So'rovlarni ko'rib chiqish =====

async def notify_user_approved(bot: Bot, user_id: int, ch_name: str, invite_link: str):
    try:
        await bot.send_message(
            user_id,
            f"🎉 <b>So'rovingiz tasdiqlandi!</b>\n\n"
            f"📢 Kanal: <b>{ch_name}</b>\n\n"
            f"🔑 <b>Bir martalik kirish havolangiz:</b>\n{invite_link}\n\n"
            f"⚠️ Bu havola <b>faqat bir marta</b> ishlatilishi mumkin!\n"
            f"Tezroq bosing va kanalga qo'shiling 👆",
            parse_mode="HTML"
        )
    except Exception:
        pass


async def notify_user_rejected(bot: Bot, user_id: int, ch_name: str):
    try:
        await bot.send_message(
            user_id,
            f"❌ <b>Afsuski, so'rovingiz rad etildi.</b>\n\n"
            f"📢 Kanal: <b>{ch_name}</b>\n\n"
            f"💬 Batafsil ma'lumot uchun admin bilan bog'laning.",
            parse_mode="HTML"
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_approve_"))
async def admin_approve_request(callback: CallbackQuery, bot: Bot):
    from database import is_admin_db
    if not await is_admin_db(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    req_id = int(callback.data.split("_")[2])
    req = await db.get_paid_request(req_id)
    if not req:
        await callback.answer("❌ So'rov topilmadi!", show_alert=True)
        return
    if req["status"] != "pending":
        await callback.answer("⚠️ Bu so'rov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    # Bir martalik invite link yaratish
    try:
        chat_member_count = await bot.get_chat(req["ch_username"])
        invite = await bot.create_chat_invite_link(
            chat_id=req["ch_username"],
            member_limit=1,
            name=f"Req#{req_id}"
        )
        invite_link = invite.invite_link
    except Exception as e:
        await callback.answer(
            f"❌ Invite link yaratib bo'lmadi!\n{str(e)[:100]}\n\nBot kanalda admin bo'lishi kerak!",
            show_alert=True
        )
        return

    # DB yangilash
    await db.approve_paid_request(req_id, invite_link)

    # Foydalanuvchiga yuborish
    await notify_user_approved(bot, req["user_id"], req["ch_name"], invite_link)

    full_name = f"{req['first_name']} {req['last_name']}"
    await callback.message.edit_text(
        f"✅ <b>So'rov tasdiqlandi!</b>\n\n"
        f"👤 Foydalanuvchi: <b>{full_name}</b>\n"
        f"📢 Kanal: <b>{req['ch_name']}</b>\n"
        f"🔢 So'rov №: <b>#{req_id}</b>\n\n"
        f"🔑 Invite link foydalanuvchiga yuborildi:\n<code>{invite_link}</code>",
        parse_mode="HTML"
    )
    await callback.answer("✅ Tasdiqlandi va link yuborildi!")


@router.callback_query(F.data.startswith("adm_reject_"))
async def admin_reject_request(callback: CallbackQuery, bot: Bot):
    from database import is_admin_db
    if not await is_admin_db(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    req_id = int(callback.data.split("_")[2])
    req = await db.get_paid_request(req_id)
    if not req:
        await callback.answer("❌ So'rov topilmadi!", show_alert=True)
        return
    if req["status"] != "pending":
        await callback.answer("⚠️ Bu so'rov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await db.reject_paid_request(req_id)
    await notify_user_rejected(bot, req["user_id"], req["ch_name"])

    full_name = f"{req['first_name']} {req['last_name']}"
    await callback.message.edit_text(
        f"❌ <b>So'rov rad etildi.</b>\n\n"
        f"👤 Foydalanuvchi: <b>{full_name}</b>\n"
        f"📢 Kanal: <b>{req['ch_name']}</b>\n"
        f"🔢 So'rov №: <b>#{req_id}</b>\n\n"
        f"ℹ️ Foydalanuvchiga xabar yuborildi.",
        parse_mode="HTML"
    )
    await callback.answer("❌ Rad etildi!")


# ===== ADMIN: Kutayotgan so'rovlar ro'yxati =====

@router.message(F.text == "📩 Kutayotgan so'rovlar")
async def pending_requests_list(message: Message, bot: Bot):
    from database import is_admin_db
    if not await is_admin_db(message.from_user.id):
        return

    requests = await db.get_pending_paid_requests()
    if not requests:
        await message.answer("📭 <b>Hozircha kutayotgan so'rovlar yo'q.</b>", parse_mode="HTML")
        return

    text = f"📩 <b>Kutayotgan so'rovlar</b> ({len(requests)} ta):\n\n"
    b = InlineKeyboardBuilder()
    for r in requests:
        full_name = f"{r['first_name']} {r['last_name']}"
        text += f"#{r['id']} — {full_name} → {r['ch_name']}\n"
        b.button(
            text=f"#{r['id']} {full_name[:15]} → {r['ch_name'][:12]}",
            callback_data=f"adm_reqdetail_{r['id']}"
        )
    b.adjust(1)
    await message.answer(text, reply_markup=b.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("adm_reqdetail_"))
async def admin_request_detail(callback: CallbackQuery):
    from database import is_admin_db
    if not await is_admin_db(callback.from_user.id):
        return

    req_id = int(callback.data.split("_")[2])
    req = await db.get_paid_request(req_id)
    if not req:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return

    full_name = f"{req['first_name']} {req['last_name']}"
    b = InlineKeyboardBuilder()
    if req["status"] == "pending":
        b.button(text="✅ Tasdiqlash", callback_data=f"adm_approve_{req_id}")
        b.button(text="❌ Rad etish", callback_data=f"adm_reject_{req_id}")
        b.adjust(2)

    status_map = {"pending": "⏳ Kutilmoqda", "approved": "✅ Tasdiqlangan", "rejected": "❌ Rad etilgan"}
    await callback.message.edit_text(
        f"🔍 <b>So'rov #{req_id}</b>\n\n"
        f"👤 Foydalanuvchi: <b>{full_name}</b>\n"
        f"📱 Telefon: {req['phone']}\n"
        f"🆔 TG ID: <code>{req['user_id']}</code>\n\n"
        f"📢 Kanal: <b>{req['ch_name']}</b> ({req['ch_username']})\n"
        f"📅 So'rov vaqti: {req['requested_at'][:16]}\n"
        f"📌 Holat: {status_map.get(req['status'], req['status'])}",
        reply_markup=b.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()