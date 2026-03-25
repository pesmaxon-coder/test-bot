from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def main_menu_kb():
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="✍️ Test yaratish"), KeyboardButton(text="✅ Javobni tekshirish"))
    b.row(KeyboardButton(text="📊 Mening testlarim"), KeyboardButton(text="🎉 Sertifikatlar"))
    b.row(KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="🔒 Pullik kanallar"))
    return b.as_markup(resize_keyboard=True)


def phone_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="📱 Telefon raqamni yuborish", request_contact=True)
    return b.as_markup(resize_keyboard=True, one_time_keyboard=True)


def sub_kb(channels):
    b = InlineKeyboardBuilder()
    for ch in channels:
        b.button(text="📢 " + ch["name"], url=ch["url"])
    b.button(text="✅ Tasdiqlash", callback_data="check_sub")
    b.adjust(1)
    return b.as_markup()


def test_type_kb():
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="📝 Oddiy test"), KeyboardButton(text="📕 Fanli test"))
    b.row(KeyboardButton(text="📦 Maxsus test"), KeyboardButton(text="📗 Blok test"))
    b.row(KeyboardButton(text="🔄 Orqaga"))
    return b.as_markup(resize_keyboard=True)


def deadline_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="♾️ Deadline kerak emas")
    b.button(text="❌ Bekor qilish")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)


def cancel_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="❌ Bekor qilish")
    return b.as_markup(resize_keyboard=True)


def back_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="🔄 Orqaga")
    return b.as_markup(resize_keyboard=True)


def confirm_answers_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="✅ Ha, tasdiqlash")
    b.button(text="✏️ Qayta kiritish")
    b.button(text="❌ Bekor qilish")
    b.adjust(2, 1)
    return b.as_markup(resize_keyboard=True)


def settings_kb():
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="🎨 Sertifikat dizayni"), KeyboardButton(text="✏️ Ism-familiyani o'zgartirish"))
    b.row(KeyboardButton(text="🔄 Orqaga"))
    return b.as_markup(resize_keyboard=True)


def design_kb(current=1):
    b = InlineKeyboardBuilder()
    designs = [
        ("1️⃣ Ko'k Chevron", 1), ("2️⃣ Oltin Chegara", 2),
        ("3️⃣ Qora-Oltin", 3), ("4️⃣ To'q Ko'k", 4),
        ("5️⃣ Yashil", 5), ("6️⃣ Vintage", 6),
        ("7️⃣ Rang-Barang", 7), ("8️⃣ Geometrik", 8),
    ]
    for name, num in designs:
        mark = " ✅" if num == current else ""
        b.button(text=name + mark, callback_data="design_" + str(num))
    b.adjust(2)
    return b.as_markup()


def admin_main_kb():
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📋 Testlar ro'yxati"))
    b.row(KeyboardButton(text="📢 Kanallar"), KeyboardButton(text="🔒 Pullik kanallar"))
    b.row(KeyboardButton(text="📩 Kutayotgan so'rovlar"), KeyboardButton(text="🎨 Sertifikat dizaynlari"))
    b.row(KeyboardButton(text="👥 Foydalanuvchilar"), KeyboardButton(text="👨‍💼 Adminlar"))
    b.row(KeyboardButton(text="📣 Xabar yuborish"), KeyboardButton(text="⏸ Botni to'xtatish"))
    b.row(KeyboardButton(text="🏠 Asosiy menyu"))
    return b.as_markup(resize_keyboard=True)