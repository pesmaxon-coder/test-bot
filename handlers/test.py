from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import main_menu_kb, test_type_kb, cancel_kb, back_kb
from utils.certificate import generate_certificate
from handlers.registration import check_subscriptions
from aiogram.types import BufferedInputFile

router = Router()


class CreateTest(StatesGroup):
    choose_type = State()
    title = State()
    answers = State()


class SolveTest(StatesGroup):
    test_code = State()
    answers = State()


def normalize_answers(text: str) -> list:
    """
    Javoblarni normallashtiradi.
    Qabul qilish formatlari:
    - "ABCDDCBA"
    - "A B C D D C B A"
    - "1A 2B 3C ..." yoki "1.A 2.B ..."
    """
    text = text.upper().strip()
    # Raqam-harf formatini filtrlash (1A, 2B...)
    import re
    # Faqat harflarni olish
    letters = re.findall(r'[ABCDE]', text)
    return letters


async def ensure_registered(message: Message, bot: Bot) -> bool:
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❗ Avval /start bosing va ro'yxatdan o'ting!")
        return False
    if not await check_subscriptions(bot, message.from_user.id):
        from keyboards import subscription_kb
        await message.answer(
            "❌ Botdan foydalanish uchun kanallarga a'zo bo'ling!",
            reply_markup=subscription_kb()
        )
        return False
    return True


# ============ TEST YARATISH ============

@router.message(F.text == "✍️ Test yaratish")
async def start_create_test(message: Message, state: FSMContext, bot: Bot):
    if not await ensure_registered(message, bot):
        return
    await state.set_state(CreateTest.choose_type)
    await message.answer(
        "❗ Kerakli bo'limni tanlang.",
        reply_markup=test_type_kb()
    )


@router.message(CreateTest.choose_type, F.text.in_([
    "📝 Oddiy test", "📕 Fanli test", "📦 Maxsus test", "📗 Blok test"
]))
async def choose_test_type(message: Message, state: FSMContext):
    await state.update_data(test_type=message.text)
    await state.set_state(CreateTest.title)
    await message.answer(
        "📌 Test nomini (fanini) kiriting:\n"
        "Masalan: Matematika, Ingliz tili, Kimyo",
        reply_markup=cancel_kb()
    )


@router.message(CreateTest.title)
async def get_test_title(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(CreateTest.answers)
    await message.answer(
        "✏️ Test kalitlarini yuboring.\n\n"
        "📌 Format: <b>ABCDDCBAABCD</b>\n"
        "(Har bir harf bir savolning to'g'ri javobi)\n\n"
        "Yoki raqamli: <b>1A 2B 3C 4D 5A</b>\n\n"
        "⚠️ Faqat A, B, C, D, E harflari qabul qilinadi.",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )


@router.message(CreateTest.answers)
async def get_test_answers(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return

    answers = normalize_answers(message.text)
    if len(answers) < 5:
        await message.answer(
            "❌ Kamida 5 ta savol bo'lishi kerak!\n"
            "Qayta yuboring. Format: ABCDDCBA..."
        )
        return
    if len(answers) > 200:
        await message.answer("❌ Ko'pi bilan 200 ta savol bo'lishi mumkin!")
        return

    data = await state.get_data()
    user = await db.get_user(message.from_user.id)
    full_name = f"{user['first_name']} {user['last_name']}"
    answers_str = "".join(answers)

    code = await db.create_test(
        creator_id=message.from_user.id,
        creator_name=full_name,
        title=data["title"],
        answers=answers_str
    )
    await state.clear()

    await message.answer(
        f"✅ Test muvaffaqiyatli yaratildi!\n\n"
        f"📌 Fan: <b>{data['title']}</b>\n"
        f"🔢 Savollar soni: <b>{len(answers)}</b>\n"
        f"🆔 Test ID: <code>{code}</code>\n\n"
        f"⬆️ Bu ID ni kanalga joylashtiring.\n"
        f"Test ishtirokchilari ushbu ID orqali javoblarini topshiradilar.",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )


@router.message(CreateTest.choose_type, F.text == "🔄 Orqaga")
async def back_from_create(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Bosh sahifa.", reply_markup=main_menu_kb())


# ============ JAVOBNI TEKSHIRISH ============

@router.message(F.text == "✅ Javobni tekshirish")
async def start_solve_test(message: Message, state: FSMContext, bot: Bot):
    if not await ensure_registered(message, bot):
        return
    await state.set_state(SolveTest.test_code)
    await message.answer(
        "✍️ Test kodini yuboring.\n\nMasalan: <code>ABC1234</code>",
        reply_markup=back_kb(),
        parse_mode="HTML"
    )


@router.message(SolveTest.test_code)
async def get_test_code(message: Message, state: FSMContext):
    if message.text == "🔄 Orqaga":
        await state.clear()
        await message.answer("🏠 Bosh sahifa.", reply_markup=main_menu_kb())
        return

    code = message.text.strip().upper()
    test = await db.get_test_by_code(code)

    if not test:
        await message.answer(
            "❌ Bunday test topilmadi!\n"
            "ID ni tekshirib qayta yuboring."
        )
        return

    await state.update_data(test_code=code, test_id=test["id"],
                            total=test["question_count"],
                            test_title=test["title"],
                            test_author=test["creator_name"])
    await state.set_state(SolveTest.answers)
    await message.answer(
        f"✅ Test topildi!\n\n"
        f"📌 Fan: <b>{test['title']}</b>\n"
        f"🔢 Savollar soni: <b>{test['question_count']}</b>\n"
        f"👤 Muallif: {test['creator_name']}\n\n"
        f"✏️ Javoblaringizni yuboring.\n"
        f"Format: <b>ABCDDCBA...</b> ({test['question_count']} ta harf)",
        reply_markup=back_kb(),
        parse_mode="HTML"
    )


@router.message(SolveTest.answers)
async def check_answers(message: Message, state: FSMContext, bot: Bot):
    if message.text == "🔄 Orqaga":
        await state.clear()
        await message.answer("🏠 Bosh sahifa.", reply_markup=main_menu_kb())
        return

    data = await state.get_data()
    user_answers = normalize_answers(message.text)
    total = data["total"]

    if len(user_answers) < total:
        await message.answer(
            f"❌ Siz {len(user_answers)} ta javob yubordingiz, "
            f"lekin {total} ta bo'lishi kerak!\n"
            f"Qayta yuboring."
        )
        return

    # Testning to'g'ri javoblarini olish
    test = await db.get_test_by_code(data["test_code"])
    correct_answers = list(test["answers"])

    # Tekshirish
    user_ans = user_answers[:total]
    correct_count = sum(1 for u, c in zip(user_ans, correct_answers) if u == c)
    pct = (correct_count / total * 100) if total > 0 else 0

    await state.clear()

    # Foydalanuvchi ma'lumotlari
    user = await db.get_user(message.from_user.id)
    full_name = f"{user['first_name']} {user['last_name']}"

    # Natijani saqlash
    await db.save_result(
        user_id=message.from_user.id,
        test_id=data["test_id"],
        correct=correct_count,
        total=total,
        percentage=pct,
        cert_path=""
    )

    # Sertifikat yaratish
    await message.answer("🎨 Sertifikat tayyorlanmoqda...")

    cert_buf = generate_certificate(
        design_num=user["cert_design"],
        full_name=full_name,
        test_title=data["test_title"],
        correct=correct_count,
        total=total,
        author=data["test_author"]
    )

    # Natijani ko'rsatish
    emoji = "🏆" if pct >= 80 else "✅" if pct >= 60 else "📊"
    result_text = (
        f"{emoji} <b>Natijangiz</b>\n\n"
        f"👤 {full_name}\n"
        f"📌 Fan: {data['test_title']}\n"
        f"✅ To'g'ri: {correct_count}/{total}\n"
        f"📊 Foiz: {pct:.1f}%\n"
        f"👤 Muallif: {data['test_author']}"
    )

    await message.answer_photo(
        photo=BufferedInputFile(cert_buf.read(), filename="sertifikat.png"),
        caption=result_text,
        parse_mode="HTML",
        protect_content=True
    )
