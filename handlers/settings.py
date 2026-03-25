from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import main_menu_kb, settings_kb, design_kb, cancel_kb
from utils.certificate import generate_certificate

router = Router()


class ChangeName(StatesGroup):
    first_name = State()
    last_name = State()


@router.message(F.text == "⚙️ Sozlamalar")
async def settings_menu(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❗ Avval /start bosing!")
        return
    await message.answer(
        "⚙️ <b>Sozlamalar</b>\n\n"
        "👤 Ism-familiya: <b>" + user["first_name"] + " " + user["last_name"] + "</b>\n"
        "🎨 Sertifikat dizayni: <b>#" + str(user["cert_design"]) + "</b>",
        reply_markup=settings_kb(),
        parse_mode="HTML"
    )


@router.message(F.text == "🔄 Orqaga")
async def go_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Bosh sahifa.", reply_markup=main_menu_kb())


@router.message(F.text == "🎨 Sertifikat dizayni")
async def choose_design(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        return
    await message.answer(
        "🎨 <b>Sertifikat dizaynini tanlang</b>\n\n"
        "✅ — hozirgi tanlangan dizayn\n\n"
        "Ko'rish uchun tugmani bosing 👇",
        reply_markup=design_kb(user["cert_design"]),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("design_"))
async def set_design(callback: CallbackQuery):
    num = int(callback.data.split("_")[1])
    user = await db.get_user(callback.from_user.id)
    await db.update_cert_design(callback.from_user.id, num)

    await callback.message.answer("🎨 Namuna sertifikat tayyorlanmoqda...")
    buf = generate_certificate(
        design_num=num,
        full_name=user["first_name"] + " " + user["last_name"],
        test_title="Ingliz tili",
        correct=18,
        total=20,
        author="Test Muallifi"
    )
    await callback.message.answer_photo(
        photo=BufferedInputFile(buf.read(), filename="namuna.png"),
        caption="✅ <b>" + str(num) + "-dizayn tanlandi!</b>\n\nSertifikatingiz shu ko'rinishda bo'ladi.",
        parse_mode="HTML",
        protect_content=True
    )
    await callback.answer("✅ Tanlandi!")
    await callback.message.edit_reply_markup(reply_markup=design_kb(num))


@router.message(F.text == "✏️ Ism-familiyani o'zgartirish")
async def change_name_start(message: Message, state: FSMContext):
    await state.set_state(ChangeName.first_name)
    await message.answer(
        "✏️ <b>Yangi ismingizni kiriting:</b>\n"
        "❗ Faqat lotin harflari",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )


@router.message(ChangeName.first_name)
async def change_first(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=settings_kb())
        return
    text = message.text.strip()
    if not text.isalpha() or len(text.split()) > 1:
        await message.answer("❌ Faqat bitta lotin so'z kiriting!")
        return
    await state.update_data(first_name=text.capitalize())
    await state.set_state(ChangeName.last_name)
    await message.answer("✏️ <b>Yangi familiyangizni kiriting:</b>", parse_mode="HTML")


@router.message(ChangeName.last_name)
async def change_last(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga"]:
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
        "✅ <b>Ism-familiya o'zgartirildi!</b>\n\n"
        "👤 " + data["first_name"] + " " + text.capitalize(),
        reply_markup=settings_kb(),
        parse_mode="HTML"
    )


@router.message(F.text == "🎉 Sertifikatlar")
async def show_certs(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        return
    results = await db.get_user_results(message.from_user.id)
    if not results:
        await message.answer(
            "📭 <b>Siz hali hech qanday testda qatnashmadingiz.</b>\n\n"
            "✅ Javobni tekshirish bo'limiga o'ting!",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
        return
    text = "🎉 <b>Sizning natijalaringiz:</b>\n\n"
    for i, r in enumerate(results, 1):
        if r["percentage"] >= 80:
            emoji = "🏆"
        elif r["percentage"] >= 60:
            emoji = "✅"
        else:
            emoji = "📊"
        text += (str(i) + ". " + emoji + " <b>" + r["title"] + "</b>\n"
                 "   ✅ " + str(r["correct"]) + "/" + str(r["total"])
                 + " (" + str(round(r["percentage"], 1)) + "%)\n"
                 "   🆔 " + r["test_code"] + " | 📅 " + r["taken_at"][:10] + "\n\n")
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")


