from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import REQUIRED_CHANNELS


# ============ ASOSIY MENYU ============

def main_menu_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="✍️ Test yaratish"),
        KeyboardButton(text="✅ Javobni tekshirish"),
    )
    builder.row(
        KeyboardButton(text="🎉 Sertifikatlar"),
        KeyboardButton(text="⚙️ Sozlamalar"),
    )
    builder.row(
        KeyboardButton(text="🔒 Pullik kanallar"),
    )
    return builder.as_markup(resize_keyboard=True)


# ============ RO'YXATDAN O'TISH ============

def phone_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(
        text="📱 Telefon raqamni yuborish",
        request_contact=True
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


# ============ MAJBURIY OBUNA ============

def subscription_kb():
    builder = InlineKeyboardBuilder()
    for ch in REQUIRED_CHANNELS:
        builder.button(text=ch["name"], url=ch["url"])
    builder.button(text="✅ Tasdiqlash", callback_data="check_sub")
    builder.adjust(1)
    return builder.as_markup()


# ============ TEST TUZISH ============

def test_type_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📝 Oddiy test"),
        KeyboardButton(text="📕 Fanli test"),
    )
    builder.row(
        KeyboardButton(text="📦 Maxsus test"),
        KeyboardButton(text="📗 Blok test"),
    )
    builder.row(KeyboardButton(text="🔄 Orqaga"))
    return builder.as_markup(resize_keyboard=True)


def cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True)


def back_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔄 Orqaga")
    return builder.as_markup(resize_keyboard=True)


# ============ SOZLAMALAR ============

def settings_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🎨 Sertifikat dizayni"),
        KeyboardButton(text="✏️ Ism-familiyani o'zgartirish"),
    )
    builder.row(KeyboardButton(text="🔄 Orqaga"))
    return builder.as_markup(resize_keyboard=True)


def design_kb(current=1):
    builder = InlineKeyboardBuilder()
    designs = [
        ("1️⃣ Klassik to'q", 1),
        ("2️⃣ Yashil to'lqin", 2),
        ("3️⃣ Ko'k to'lqin", 3),
        ("4️⃣ Yashil zamonaviy", 4),
        ("5️⃣ Qizil burchak", 5),
        ("6️⃣ Vintage", 6),
        ("7️⃣ Rang-barang", 7),
        ("8️⃣ Geometrik", 8),
    ]
    for name, num in designs:
        check = " ✅" if num == current else ""
        builder.button(text=f"{name}{check}", callback_data=f"design_{num}")
    builder.adjust(2)
    return builder.as_markup()
