from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile

import database as db
from keyboards import main_menu_kb, settings_kb, design_kb, cancel_kb
from utils.certificate import generate_certificate
from handlers.registration import check_subscriptions

router = Router()


class ChangeNameState(StatesGroup):
    first_name = State()
    last_name = State()


async def ensure_registered(message: Message, bot: Bot) -> bool:
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❗ Avval /start bosing!")
        return False
    if not await check_subscriptions(bot, message.from_user.id):
        from keyboards import subscription_kb
        await message.answer("❌ Kanallarga a'zo bo'ling!", reply_markup=subscription_kb())
        return False
    return True


# ============ SOZLAMALAR MENYUSI ============

@router.message(F.text == "⚙️ Sozlamalar")
async def settings_menu(message: Message, bot: Bot):
    if not await ensure_registered(message, bot):
        return
    user = await db.get_user(message.from_user.id)
    await message.answer(
        f"⚙️ <b>Sozlamalar</b>\n\n"
        f"👤 Ism-familiya: {user['first_name']} {user['last_name']}\n"
        f"🎨 Sertifikat dizayni: #{user['cert_design']}",
        reply_markup=settings_kb(),
        parse_mode="HTML"
    )


@router.message(F.text == "🔄 Orqaga")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Bosh sahifa.", reply_markup=main_menu_kb())


# ============ SERTIFIKAT DIZAYNI ============

@router.message(F.text == "🎨 Sertifikat dizayni")
async def choose_design(message: Message, bot: Bot):
    if not await ensure_registered(message, bot):
        return
    user = await db.get_user(message.from_user.id)
    await message.answer(
        "🎨 <b>Sertifikat dizaynini tanlang:</b>\n\n"
        "✅ — hozirgi tanlangan dizayn",
        reply_markup=design_kb(user["cert_design"]),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("design_"))
async def set_design(callback: CallbackQuery, bot: Bot):
    design_num = int(callback.data.split("_")[1])
    user = await db.get_user(callback.from_user.id)

    await db.update_cert_design(callback.from_user.id, design_num)

    # Namuna sertifikat ko'rsatish
    await callback.message.answer("🎨 Namuna sertifikat tayyorlanmoqda...")

    cert_buf = generate_certificate(
        design_num=design_num,
        full_name=f"{user['first_name']} {user['last_name']}",
        test_title="Matematika",
        correct=18,
        total=20,
        author="Test Muallifi"
    )

    await callback.message.answer_photo(
        photo=BufferedInputFile(cert_buf.read(), filename="namuna.png"),
        caption=f"✅ {design_num}-dizayn tanlandi!\n\nBu sizning keyingi sertifikatingiz ko'rinishi.",
        protect_content=True
    )
    await callback.answer(f"✅ {design_num}-dizayn tanlandi!")
    # Keyboard yangilash
    await callback.message.edit_reply_markup(reply_markup=design_kb(design_num))


# ============ ISM-FAMILIYANI O'ZGARTIRISH ============

@router.message(F.text == "✏️ Ism-familiyani o'zgartirish")
async def change_name_start(message: Message, state: FSMContext, bot: Bot):
    if not await ensure_registered(message, bot):
        return
    await state.set_state(ChangeNameState.first_name)
    await message.answer(
        "✏️ Yangi ismingizni kiriting (faqat lotin harflari):",
        reply_markup=cancel_kb()
    )


@router.message(ChangeNameState.first_name)
async def change_first_name(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=settings_kb())
        return
    text = message.text.strip()
    if not text.isalpha() or len(text.split()) > 1:
        await message.answer("❌ Faqat bitta lotin so'z kiriting!")
        return
    await state.update_data(first_name=text.capitalize())
    await state.set_state(ChangeNameState.last_name)
    await message.answer("✏️ Yangi familiyangizni kiriting:")


@router.message(ChangeNameState.last_name)
async def change_last_name(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=settings_kb())
        return
    text = message.text.strip()
    if not text.isalpha() or len(text.split()) > 1:
        await message.answer("❌ Faqat bitta lotin so'z kiriting!")
        return
    data = await state.get_data()
    await db.update_user_name(message.from_user.id, data["first_name"], text.capitalize())
    await state.clear()
    await message.answer(
        f"✅ Ism-familiya o'zgartirildi!\n"
        f"👤 {data['first_name']} {text.capitalize()}",
        reply_markup=settings_kb()
    )


# ============ SERTIFIKATLAR ============

@router.message(F.text == "🎉 Sertifikatlar")
async def show_certificates(message: Message, bot: Bot):
    if not await ensure_registered(message, bot):
        return

    results = await db.get_user_results(message.from_user.id)
    if not results:
        await message.answer(
            "📭 Siz hali hech qanday testda qatnashmadingiz.\n\n"
            "✅ Javobni tekshirish bo'limiga o'ting!",
            reply_markup=main_menu_kb()
        )
        return

    text = "🎉 <b>Sizning natijalaringiz:</b>\n\n"
    for i, r in enumerate(results, 1):
        emoji = "🏆" if r["percentage"] >= 80 else "✅" if r["percentage"] >= 60 else "📊"
        text += (
            f"{i}. {emoji} <b>{r['title']}</b>\n"
            f"   ✅ {r['correct']}/{r['total']} ({r['percentage']:.1f}%)\n"
            f"   🆔 {r['test_code']} | 📅 {r['taken_at'][:10]}\n\n"
        )

    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")


# ============ PULLIK KANALLAR ============

@router.message(F.text == "🔒 Pullik kanallar")
async def pullik_kanallar(message: Message):
    await message.answer(
        "🔒 <b>Pullik kanallar</b>\n\n"
        "Bu bo'lim tez orada ochiladi!",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )
