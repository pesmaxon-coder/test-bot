from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import main_menu_kb, phone_kb, subscription_kb
from config import REQUIRED_CHANNELS

router = Router()


class RegState(StatesGroup):
    first_name = State()
    last_name = State()
    phone = State()


async def check_subscriptions(bot: Bot, user_id: int) -> bool:
    for ch in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(ch["username"], user_id)
            if member.status in ("left", "kicked", "banned"):
                return False
        except Exception:
            return False
    return True


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user = await db.get_user(message.from_user.id)

    if user:
        # Obunani tekshirish
        if not await check_subscriptions(bot, message.from_user.id):
            await message.answer(
                "❌ Kechirasiz, botimizdan foydalanishdan oldin "
                "ushbu kanallarga a'zo bo'lishingiz kerak.",
                reply_markup=subscription_kb()
            )
            return
        await message.answer(
            f"👋 Assalomu alaykum {user['first_name']} {user['last_name']}!\n"
            f"Botimizga xush kelibsiz.",
            reply_markup=main_menu_kb()
        )
        return

    # Yangi foydalanuvchi — ro'yxatdan o'tkazish
    await state.set_state(RegState.first_name)
    await message.answer(
        "👋 Botimizga xush kelibsiz!\n\n"
        "✍️ Ismingizni kiriting.\n\n"
        "❗ Ism faqat lotin alifbosida bo'lishi shart."
    )


@router.message(RegState.first_name)
async def get_first_name(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.replace(" ", "").isalpha():
        await message.answer(
            "❌ Kechirasiz ism bitta so'zdan iborat bo'lishi mumkin. "
            "Tekshirib qayta yuboring."
        )
        return
    if len(text.split()) > 1:
        await message.answer(
            "❌ Kechirasiz ism bitta so'zdan iborat bo'lishi mumkin. "
            "Tekshirib qayta yuboring."
        )
        return
    await state.update_data(first_name=text.capitalize())
    await state.set_state(RegState.last_name)
    await message.answer(
        "✍️ Familiyangizni kiriting.\n\n"
        "❗ Familiya faqat lotin alifbosida bo'lishi shart."
    )


@router.message(RegState.last_name)
async def get_last_name(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.replace(" ", "").isalpha():
        await message.answer(
            "❌ Familiya faqat lotin harflaridan iborat bo'lishi kerak. "
            "Qayta kiriting."
        )
        return
    if len(text.split()) > 1:
        await message.answer("❌ Familiya faqat bitta so'z bo'lishi kerak.")
        return
    await state.update_data(last_name=text.capitalize())
    await state.set_state(RegState.phone)
    await message.answer(
        "📱 Telefon raqamingizni yuboring.",
        reply_markup=phone_kb()
    )


@router.message(RegState.phone, F.contact)
async def get_phone(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    phone = message.contact.phone_number
    await db.register_user(
        message.from_user.id,
        data["first_name"],
        data["last_name"],
        phone
    )
    await state.clear()

    # Obunani tekshirish
    if not await check_subscriptions(bot, message.from_user.id):
        await message.answer(
            f"✅ Ro'yxatdan o'tdingiz!\n\n"
            "❌ Endi botimizdan foydalanish uchun quyidagi kanallarga "
            "a'zo bo'lishingiz kerak.",
            reply_markup=subscription_kb()
        )
        return

    await message.answer(
        f"✅ Assalomu alaykum {data['first_name']} {data['last_name']} "
        f"botimizga xush kelibsiz.",
        reply_markup=main_menu_kb()
    )


@router.message(RegState.phone)
async def phone_not_shared(message: Message):
    await message.answer(
        "❗ Iltimos, tugma orqali telefon raqamingizni yuboring.",
        reply_markup=phone_kb()
    )


# ============ OBUNA TEKSHIRISH ============

@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery, bot: Bot):
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("Avval /start bosing!", show_alert=True)
        return

    if await check_subscriptions(bot, callback.from_user.id):
        await callback.message.edit_text(
            f"✅ Rahmat! Barcha kanallarga a'zo bo'ldingiz.\n"
            f"Botdan foydalanishingiz mumkin!"
        )
        await callback.message.answer(
            f"👋 {user['first_name']} {user['last_name']}, xush kelibsiz!",
            reply_markup=main_menu_kb()
        )
    else:
        await callback.answer(
            "❌ Siz hali barcha kanallarga a'zo bo'lmadingiz!",
            show_alert=True
        )
