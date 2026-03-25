from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from keyboards import main_menu_kb, phone_kb, sub_kb, admin_main_kb

router = Router()


class RegState(StatesGroup):
    first_name = State()
    last_name = State()
    phone = State()


async def check_sub(bot: Bot, user_id: int) -> bool:
    channels = await db.get_channels("required")
    if not channels:
        return True
    for ch in channels:
        try:
            m = await bot.get_chat_member(ch["username"], user_id)
            if m.status in ("left", "kicked", "banned"):
                return False
        except Exception:
            return False
    return True


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    uid = message.from_user.id

    if not await db.is_admin_db(uid):
        if await db.is_bot_paused():
            await message.answer(
                "⏸ <b>Bot hozircha vaqtincha to'xtatilgan.</b>\n\n"
                "🔧 Tez orada qayta ishga tushiriladi.\n"
                "Sabr qiling! 🙏",
                parse_mode="HTML"
            )
            return

    user = await db.get_user(uid)

    if user:
        if await db.is_admin_db(uid):
            await message.answer(
                "👨‍💼 <b>Admin paneliga xush kelibsiz!</b>\n\n"
                "🔧 Boshqaruv panelingizdan foydalaning.",
                reply_markup=admin_main_kb(),
                parse_mode="HTML"
            )
            return

        if not await check_sub(bot, uid):
            channels = await db.get_channels("required")
            await message.answer(
                "❌ <b>Kechirasiz!</b>\n\n"
                "📢 Botdan foydalanish uchun quyidagi kanallarga a'zo bo'lishingiz kerak:",
                reply_markup=sub_kb(channels),
                parse_mode="HTML"
            )
            return

        await message.answer(
            "👋 <b>Xush kelibsiz, " + user["first_name"] + "!</b>\n\n"
            "📚 Bot bilan ishlashni boshlang!",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
        return

    await state.set_state(RegState.first_name)
    await message.answer(
        "🎓 <b>Botga xush kelibsiz!</b>\n\n"
        "📝 Ro'yxatdan o'tish uchun bir necha qadam:\n\n"
        "✍️ <b>Ismingizni kiriting.</b>\n"
        "❗ Ism faqat lotin harflarida bo'lishi shart.",
        parse_mode="HTML"
    )


@router.message(RegState.first_name)
async def get_first_name(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.replace(" ", "").isalpha() or len(text.split()) > 1:
        await message.answer(
            "❌ <b>Kechirasiz!</b> Ism bitta lotin so'zdan iborat bo'lishi kerak.\n"
            "Tekshirib qayta yuboring 👇",
            parse_mode="HTML"
        )
        return
    await state.update_data(first_name=text.capitalize())
    await state.set_state(RegState.last_name)
    await message.answer(
        "✅ Ism qabul qilindi!\n\n"
        "✍️ <b>Familiyangizni kiriting.</b>\n"
        "❗ Familiya faqat lotin harflarida bo'lishi shart.",
        parse_mode="HTML"
    )


@router.message(RegState.last_name)
async def get_last_name(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.replace(" ", "").isalpha() or len(text.split()) > 1:
        await message.answer(
            "❌ Familiya bitta lotin so'z bo'lishi kerak. Qayta kiriting 👇",
            parse_mode="HTML"
        )
        return
    await state.update_data(last_name=text.capitalize())
    await state.set_state(RegState.phone)
    await message.answer(
        "✅ Familiya qabul qilindi!\n\n"
        "📱 <b>Telefon raqamingizni yuboring.</b>\n"
        "Quyidagi tugmani bosing 👇",
        reply_markup=phone_kb(),
        parse_mode="HTML"
    )


@router.message(RegState.phone, F.contact)
async def get_phone(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await db.register_user(
        message.from_user.id,
        data["first_name"],
        data["last_name"],
        message.contact.phone_number
    )
    await state.clear()

    if not await check_sub(bot, message.from_user.id):
        channels = await db.get_channels("required")
        await message.answer(
            "🎉 <b>Ro'yxatdan o'tdingiz!</b>\n\n"
            "📢 Endi botdan foydalanish uchun kanallarga a'zo bo'lishingiz kerak:",
            reply_markup=sub_kb(channels),
            parse_mode="HTML"
        )
        return

    await message.answer(
        "🎉 <b>Tabriklaymiz!</b>\n\n"
        "✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!\n"
        "👋 Xush kelibsiz, <b>" + data["first_name"] + " " + data["last_name"] + "</b>!\n\n"
        "📚 Botdan foydalanishni boshlang 👇",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )


@router.message(RegState.phone)
async def phone_wrong(message: Message):
    await message.answer(
        "❗ Iltimos, <b>tugma orqali</b> telefon raqam yuboring 👇",
        reply_markup=phone_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "check_sub")
async def check_sub_cb(callback: CallbackQuery, bot: Bot):
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("Avval /start bosing!", show_alert=True)
        return
    if await check_sub(bot, callback.from_user.id):
        await callback.message.edit_text(
            "✅ <b>Rahmat!</b> Barcha kanallarga a'zo bo'ldingiz!",
            parse_mode="HTML"
        )
        await callback.message.answer(
            "🎉 <b>Xush kelibsiz, " + user["first_name"] + "!</b>\n\n"
            "📚 Botdan foydalanishni boshlang 👇",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
    else:
        await callback.answer(
            "❌ Hali barcha kanallarga a'zo bo'lmadingiz!",
            show_alert=True
        )