from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import KeyboardButton, BufferedInputFile
from datetime import datetime
 
import database as db
from keyboards import main_menu_kb, test_type_kb, cancel_kb, back_kb
from utils.certificate import generate_certificate
from handlers.registration import check_subscriptions
 
router = Router()
 
 
# ============ STATES ============
 
class CreateTest(StatesGroup):
    choose_type = State()
    title = State()
    answers = State()
    deadline = State()
 
 
class SolveTest(StatesGroup):
    test_code = State()
    answers = State()
 
 
class ViewResults(StatesGroup):
    test_code = State()
 
 
# ============ YORDAMCHI FUNKSIYALAR ============
 
def normalize_answers(text: str) -> list:
    import re
    text = text.upper().strip()
    letters = re.findall(r'[ABCDE]', text)
    return letters
 
 
def parse_deadline(text: str):
    """
    Qabul qilinadigan formatlar:
    - 25.12.2024
    - 25.12.2024 18:00
    - 25/12/2024
    """
    text = text.strip().replace("/", ".")
    formats = ["%d.%m.%Y %H:%M", "%d.%m.%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None
 
 
def is_deadline_passed(deadline_str: str) -> bool:
    if not deadline_str:
        return False
    try:
        deadline = datetime.strptime(deadline_str, "%d.%m.%Y %H:%M")
        return datetime.now() > deadline
    except Exception:
        return False
 
 
def format_answer_details(user_ans: str, correct_ans: str) -> str:
    """Har bir savol uchun to'g'ri/noto'g'ri belgisi"""
    lines = []
    for i, (u, c) in enumerate(zip(user_ans, correct_ans), 1):
        if u == c:
            lines.append(f"  {i:>3}. ✅ {u}")
        else:
            lines.append(f"  {i:>3}. ❌ {u} (to'g'ri: {c})")
    return "\n".join(lines)
 
 
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
    await message.answer("❗ Kerakli bo'limni tanlang.", reply_markup=test_type_kb())
 
 
@router.message(CreateTest.choose_type, F.text.in_([
    "📝 Oddiy test", "📕 Fanli test", "📦 Maxsus test", "📗 Blok test"
]))
async def choose_test_type(message: Message, state: FSMContext):
    await state.update_data(test_type=message.text)
    await state.set_state(CreateTest.title)
    await message.answer(
        "📌 Test nomini (fanini) kiriting:\nMasalan: Matematika, Ingliz tili",
        reply_markup=cancel_kb()
    )
 
 
@router.message(CreateTest.choose_type, F.text == "🔄 Orqaga")
async def back_from_type(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Bosh sahifa.", reply_markup=main_menu_kb())
 
 
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
        "yoki raqamli: <b>1A 2B 3C 4D 5A</b>\n\n"
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
        await message.answer("❌ Kamida 5 ta savol bo'lishi kerak!")
        return
    if len(answers) > 200:
        await message.answer("❌ Ko'pi bilan 200 ta savol bo'lishi mumkin!")
        return
 
    await state.update_data(answers="".join(answers))
    await state.set_state(CreateTest.deadline)
 
    # Deadline so'rash klaviaturasi
    builder = ReplyKeyboardBuilder()
    builder.button(text="⏭ Deadline yo'q")
    builder.button(text="❌ Bekor qilish")
    builder.adjust(2)
 
    await message.answer(
        "⏰ <b>Deadline (muddat) belgilash</b>\n\n"
        "Test qachon tugashini kiriting:\n"
        "📌 Format: <b>25.12.2024</b> yoki <b>25.12.2024 18:00</b>\n\n"
        "Deadline bo'lmasa — <b>⏭ Deadline yo'q</b> tugmasini bosing.",
        reply_markup=builder.as_markup(resize_keyboard=True),
        parse_mode="HTML"
    )
 
 
@router.message(CreateTest.deadline)
async def get_test_deadline(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return
 
    data = await state.get_data()
    user = await db.get_user(message.from_user.id)
    full_name = f"{user['first_name']} {user['last_name']}"
    deadline_str = None
 
    if message.text != "⏭ Deadline yo'q":
        deadline = parse_deadline(message.text)
        if not deadline:
            await message.answer(
                "❌ Noto'g'ri format! Qayta kiriting:\n"
                "📌 Format: <b>25.12.2024</b> yoki <b>25.12.2024 18:00</b>",
                parse_mode="HTML"
            )
            return
        if deadline < datetime.now():
            await message.answer("❌ Deadline o'tib ketgan! Kelajakdagi sana kiriting.")
            return
        deadline_str = deadline.strftime("%d.%m.%Y %H:%M")
 
    code = await db.create_test(
        creator_id=message.from_user.id,
        creator_name=full_name,
        title=data["title"],
        answers=data["answers"],
        deadline=deadline_str
    )
    await state.clear()
 
    deadline_info = f"\n⏰ Deadline: <b>{deadline_str}</b>" if deadline_str else "\n⏰ Deadline: <b>Yo'q</b>"
 
    await message.answer(
        f"✅ <b>Test muvaffaqiyatli yaratildi!</b>\n\n"
        f"📌 Fan: <b>{data['title']}</b>\n"
        f"🔢 Savollar: <b>{len(data['answers'])}</b> ta\n"
        f"🆔 Test ID: <code>{code}</code>"
        f"{deadline_info}\n\n"
        f"📢 Bu ID ni kanalga joylashtiring.",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )
 
 
# ============ MENING TESTLARIM ============
 
@router.message(F.text == "📊 Mening testlarim")
async def my_tests(message: Message, bot: Bot):
    if not await ensure_registered(message, bot):
        return
    tests = await db.get_creator_tests(message.from_user.id)
    if not tests:
        await message.answer("📭 Siz hali test yaratmagansiz.", reply_markup=main_menu_kb())
        return
 
    builder = InlineKeyboardBuilder()
    for t in tests[:20]:
        status = "🔴" if is_deadline_passed(t["deadline"]) else "🟢"
        deadline_txt = t["deadline"] or "∞"
        builder.button(
            text=f"{status} {t['test_code']} | {t['title'][:20]} | ⏰{deadline_txt}",
            callback_data=f"mytest_{t['id']}"
        )
    builder.adjust(1)
    await message.answer(
        f"📋 <b>Mening testlarim</b> ({len(tests)} ta)\n\n"
        "🟢 — faol  |  🔴 — muddat o'tgan\n\n"
        "Natijalarni ko'rish uchun testni tanlang:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
 
 
@router.callback_query(F.data.startswith("mytest_"))
async def show_test_results(callback: CallbackQuery):
    test_id = int(callback.data.split("_")[1])
 
    # Testni topish
    all_tests = await db.get_all_tests()
    test = next((t for t in all_tests if t["id"] == test_id), None)
    if not test:
        await callback.answer("Test topilmadi!", show_alert=True)
        return
 
    # Faqat test egasi ko'ra oladi
    if callback.from_user.id != test["creator_id"]:
        admin_ok = await db.is_admin_db(callback.from_user.id)
        if not admin_ok:
            await callback.answer("❌ Bu test sizniki emas!", show_alert=True)
            return
 
    results = await db.get_test_results(test_id)
 
    status = "🔴 Muddat o'tgan" if is_deadline_passed(test["deadline"]) else "🟢 Faol"
    deadline_txt = test["deadline"] or "Yo'q"
 
    text = (
        f"📋 <b>{test['title']}</b>\n"
        f"🆔 {test['test_code']} | 🔢 {test['question_count']} ta savol\n"
        f"⏰ Deadline: {deadline_txt} | {status}\n"
        f"👥 Ishtirokchilar: {len(results)} ta\n\n"
    )
 
    if not results:
        text += "📭 Hali hech kim test topshirmagan."
        await callback.message.edit_text(text, parse_mode="HTML")
        return
 
    # Umumiy statistika
    avg_pct = sum(r["percentage"] for r in results) / len(results)
    text += f"📊 O'rtacha natija: {avg_pct:.1f}%\n"
    text += f"🏆 Eng yuqori: {results[0]['percentage']:.1f}%\n\n"
    text += "━━━━━━━━━━━━━━━━━━\n"
    text += "<b>Natijalar (yuqoridan pastga):</b>\n\n"
 
    for i, r in enumerate(results[:15], 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += (
            f"{emoji} <b>{r['first_name']} {r['last_name']}</b>\n"
            f"   ✅ {r['correct']}/{r['total']} ({r['percentage']:.1f}%)\n"
            f"   📅 {r['taken_at'][:16]}\n"
        )
 
    if len(results) > 15:
        text += f"\n... va yana {len(results)-15} ta ishtirokchi"
 
    # Har bir natijani batafsil ko'rish uchun tugmalar
    builder = InlineKeyboardBuilder()
    for r in results[:10]:
        builder.button(
            text=f"🔍 {r['first_name']} {r['last_name']} ({r['percentage']:.0f}%)",
            callback_data=f"result_detail_{r['id']}_{test_id}"
        )
    builder.adjust(1)
 
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
 
 
@router.callback_query(F.data.startswith("result_detail_"))
async def show_result_detail(callback: CallbackQuery):
    parts = callback.data.split("_")
    result_id = int(parts[2])
    test_id = int(parts[3])
 
    # Natijani topish
    results = await db.get_test_results(test_id)
    result = next((r for r in results if r["id"] == result_id), None)
    if not result:
        await callback.answer("Natija topilmadi!", show_alert=True)
        return
 
    # Testni topish
    all_tests = await db.get_all_tests()
    test = next((t for t in all_tests if t["id"] == test_id), None)
 
    user_ans = result["user_answers"]
    correct_ans = test["answers"]
 
    # Har bir javobni tahlil qilish
    details = []
    for i, (u, c) in enumerate(zip(user_ans, correct_ans), 1):
        if u == c:
            details.append(f"{i:>3}. ✅ {u}")
        else:
            details.append(f"{i:>3}. ❌ {u} → {c}")
 
    # 50 tadan ko'p bo'lsa ikki qismga bo'lib yuborish
    header = (
        f"🔍 <b>{result['first_name']} {result['last_name']}</b>\n"
        f"📌 Test: {test['title']}\n"
        f"✅ To'g'ri: {result['correct']}/{result['total']} ({result['percentage']:.1f}%)\n"
        f"📅 Topshirilgan: {result['taken_at'][:16]}\n\n"
        f"<b>Javoblar tahlili:</b>\n"
        f"(✅ to'g'ri | ❌ noto'g'ri → to'g'ri javob)\n\n"
    )
 
    chunk_size = 50
    chunks = [details[i:i+chunk_size] for i in range(0, len(details), chunk_size)]
 
    await callback.message.answer(
        header + "<code>" + "\n".join(chunks[0]) + "</code>",
        parse_mode="HTML"
    )
    for chunk in chunks[1:]:
        await callback.message.answer(
            "<code>" + "\n".join(chunk) + "</code>",
            parse_mode="HTML"
        )
 
    await callback.answer()
 
 
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
        await message.answer("❌ Bunday test topilmadi! ID ni tekshirib qayta yuboring.")
        return
 
    # Deadline tekshirish
    if is_deadline_passed(test["deadline"]):
        await message.answer(
            f"⏰ <b>Test muddati tugagan!</b>\n\n"
            f"📌 Test: {test['title']}\n"
            f"🔴 Deadline: {test['deadline']}\n\n"
            f"Bu testga javob topshirib bo'lmaydi.",
            parse_mode="HTML"
        )
        return
 
    deadline_info = f"\n⏰ Deadline: <b>{test['deadline']}</b>" if test["deadline"] else ""
 
    await state.update_data(
        test_code=code,
        test_id=test["id"],
        total=test["question_count"],
        test_title=test["title"],
        test_author=test["creator_name"]
    )
    await state.set_state(SolveTest.answers)
    await message.answer(
        f"✅ Test topildi!\n\n"
        f"📌 Fan: <b>{test['title']}</b>\n"
        f"🔢 Savollar: <b>{test['question_count']}</b> ta\n"
        f"👤 Muallif: {test['creator_name']}"
        f"{deadline_info}\n\n"
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
 
    # Deadline qayta tekshirish
    test = await db.get_test_by_code(data["test_code"])
    if is_deadline_passed(test["deadline"]):
        await state.clear()
        await message.answer(
            "⏰ Kechirasiz, test muddati tugadi!",
            reply_markup=main_menu_kb()
        )
        return
 
    user_answers = normalize_answers(message.text)
    total = data["total"]
 
    if len(user_answers) < total:
        await message.answer(
            f"❌ Siz {len(user_answers)} ta javob yubordingiz, "
            f"lekin {total} ta bo'lishi kerak!\nQayta yuboring."
        )
        return
 
    correct_answers = list(test["answers"])
    user_ans = user_answers[:total]
    correct_count = sum(1 for u, c in zip(user_ans, correct_answers) if u == c)
    pct = (correct_count / total * 100) if total > 0 else 0
    await state.clear()
 
    user = await db.get_user(message.from_user.id)
    full_name = f"{user['first_name']} {user['last_name']}"
    user_ans_str = "".join(user_ans)
 
    await db.save_result(
        user_id=message.from_user.id,
        test_id=data["test_id"],
        correct=correct_count,
        total=total,
        percentage=pct,
        user_answers=user_ans_str
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
 
    emoji = "🏆" if pct >= 80 else "✅" if pct >= 60 else "📊"
 
    # Xato javoblarni ko'rsatish (qisqacha)
    wrong_list = []
    for i, (u, c) in enumerate(zip(user_ans, correct_answers), 1):
        if u != c:
            wrong_list.append(f"{i}-savol: {u}→{c}")
 
    wrong_text = ""
    if wrong_list:
        shown = wrong_list[:10]
        wrong_text = "\n\n❌ <b>Xato javoblar:</b>\n" + " | ".join(shown)
        if len(wrong_list) > 10:
            wrong_text += f"\n... va yana {len(wrong_list)-10} ta xato"
 
    result_text = (
        f"{emoji} <b>Natijangiz</b>\n\n"
        f"👤 {full_name}\n"
        f"📌 Fan: {data['test_title']}\n"
        f"✅ To'g'ri: {correct_count}/{total}\n"
        f"📊 Foiz: {pct:.1f}%\n"
        f"👤 Muallif: {data['test_author']}"
        f"{wrong_text}"
    )
 
    await message.answer_photo(
        photo=BufferedInputFile(cert_buf.read(), filename="sertifikat.png"),
        caption=result_text,
        parse_mode="HTML",
        protect_content=True
    )
