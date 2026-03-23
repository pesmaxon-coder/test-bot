from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import KeyboardButton, BufferedInputFile
from aiogram.filters import StateFilter
from datetime import datetime
from collections import Counter
import re
 
import database as db
from keyboards import main_menu_kb, test_type_kb, cancel_kb, back_kb
from utils.certificate import generate_certificate
from handlers.registration import check_subscriptions
 
router = Router()
 
 
class CreateTest(StatesGroup):
    choose_type = State()
    title      = State()
    answers    = State()
    deadline   = State()
 
 
class SolveTest(StatesGroup):
    test_code = State()
    answers   = State()
 
 
# ============ YORDAMCHI ============
 
def normalize_answers(text: str) -> list:
    return re.findall(r'[ABCDE]', text.upper())
 
 
def parse_deadline(text: str):
    text = text.strip().replace("/", ".").replace("-", ".")
    for fmt in ["%d.%m.%Y %H:%M", "%d.%m.%Y"]:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None
 
 
def is_deadline_passed(deadline_str) -> bool:
    if not deadline_str:
        return False
    try:
        return datetime.now() > datetime.strptime(deadline_str, "%d.%m.%Y %H:%M")
    except Exception:
        return False
 
 
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
 
 
def deadline_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="✅ Deadline yo'q, saqlash")
    b.button(text="🚫 Testni bekor qilish")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)
 
 
# ============ TEST YARATISH ============
 
@router.message(F.text == "✍️ Test yaratish")
async def start_create_test(message: Message, state: FSMContext, bot: Bot):
    if not await ensure_registered(message, bot):
        return
    await state.clear()
    await state.set_state(CreateTest.choose_type)
    await message.answer("❗ Kerakli bo'limni tanlang.", reply_markup=test_type_kb())
 
 
@router.message(
    StateFilter(CreateTest.choose_type),
    F.text.in_(["📝 Oddiy test", "📕 Fanli test", "📦 Maxsus test", "📗 Blok test"])
)
async def choose_test_type(message: Message, state: FSMContext):
    await state.update_data(test_type=message.text)
    await state.set_state(CreateTest.title)
    await message.answer(
        "📌 Test nomini kiriting:\nMasalan: Matematika, Ingliz tili",
        reply_markup=cancel_kb()
    )
 
 
@router.message(StateFilter(CreateTest.choose_type))
async def choose_type_fallback(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Bosh sahifa.", reply_markup=main_menu_kb())
 
 
@router.message(StateFilter(CreateTest.title))
async def get_test_title(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga", "🚫 Testni bekor qilish"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(CreateTest.answers)
    await message.answer(
        "✏️ Test kalitlarini yuboring.\n\n"
        "📌 Format: <b>ABCDDCBAABCD</b>\n"
        "yoki: <b>1A 2B 3C 4D 5A</b>\n\n"
        "⚠️ Faqat A B C D E harflari qabul qilinadi.",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )
 
 
@router.message(StateFilter(CreateTest.answers))
async def get_test_answers(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga", "🚫 Testni bekor qilish"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return
    answers = normalize_answers(message.text)
    if len(answers) < 5:
        await message.answer("❌ Kamida 5 ta javob kiriting!\nFormat: <b>ABCDE...</b>", parse_mode="HTML")
        return
    if len(answers) > 200:
        await message.answer("❌ Ko'pi bilan 200 ta savol bo'lishi mumkin!")
        return
    await state.update_data(answers="".join(answers))
    await state.set_state(CreateTest.deadline)
    await message.answer(
        f"✅ <b>{len(answers)} ta javob</b> qabul qilindi!\n\n"
        "⏰ <b>Deadline belgilash</b>\n\n"
        "📅 Kun: <code>25.12.2024</code>\n"
        "🕐 Vaqt bilan: <code>25.12.2024 18:00</code>\n\n"
        "Deadline kerak bo'lmasa — quyidagi tugmani bosing:",
        reply_markup=deadline_kb(),
        parse_mode="HTML"
    )
 
 
@router.message(StateFilter(CreateTest.deadline))
async def get_test_deadline(message: Message, state: FSMContext):
    if message.text in ["🚫 Testni bekor qilish", "❌ Bekor qilish", "🔄 Orqaga"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return
 
    data = await state.get_data()
    deadline_str = None
 
    if message.text == "✅ Deadline yo'q, saqlash":
        deadline_str = None
    else:
        deadline = parse_deadline(message.text)
        if deadline is None:
            await message.answer(
                "❌ <b>Format noto'g'ri!</b>\n\n"
                "📅 <code>25.12.2024</code>\n"
                "🕐 <code>25.12.2024 18:00</code>\n\n"
                "Yoki deadline kerak bo'lmasa tugmani bosing:",
                reply_markup=deadline_kb(),
                parse_mode="HTML"
            )
            return
        if deadline < datetime.now():
            await message.answer("❌ Bu sana o'tib ketgan! Kelajakdagi sana kiriting.", reply_markup=deadline_kb())
            return
        deadline_str = deadline.strftime("%d.%m.%Y %H:%M")
 
    user = await db.get_user(message.from_user.id)
    full_name = f"{user['first_name']} {user['last_name']}"
    code = await db.create_test(
        creator_id=message.from_user.id,
        creator_name=full_name,
        title=data["title"],
        answers=data["answers"],
        deadline=deadline_str
    )
    await state.clear()
    dl_text = f"⏰ Deadline: <b>{deadline_str}</b>" if deadline_str else "♾ Deadline: <b>Yo'q</b>"
    await message.answer(
        f"🎉 <b>Test yaratildi!</b>\n\n"
        f"📌 Fan: <b>{data['title']}</b>\n"
        f"🔢 Savollar: <b>{len(data['answers'])}</b> ta\n"
        f"🆔 Test ID: <code>{code}</code>\n"
        f"{dl_text}\n\n"
        f"📢 Bu ID ni kanalga joylashtiring!",
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
        dl = t["deadline"] if t["deadline"] else "∞"
        builder.button(
            text=f"{status} {t['test_code']} | {t['title'][:15]} | ⏰{dl}",
            callback_data=f"mytest_{t['id']}"
        )
    builder.adjust(1)
    await message.answer(
        f"📋 <b>Mening testlarim</b> ({len(tests)} ta)\n\n"
        "🟢 Faol  |  🔴 Muddat o'tgan\n\n"
        "Batafsil ko'rish uchun tanlang:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
 
 
@router.callback_query(F.data.startswith("mytest_"))
async def show_test_menu(callback: CallbackQuery):
    test_id = int(callback.data.split("_")[1])
    all_tests = await db.get_all_tests()
    test = next((t for t in all_tests if t["id"] == test_id), None)
    if not test:
        await callback.answer("Test topilmadi!", show_alert=True)
        return
 
    if callback.from_user.id != test["creator_id"]:
        if not await db.is_admin_db(callback.from_user.id):
            await callback.answer("❌ Bu test sizniki emas!", show_alert=True)
            return
 
    results = await db.get_test_results(test_id)
    status = "🔴 Muddat o'tgan" if is_deadline_passed(test["deadline"]) else "🟢 Faol"
    dl = test["deadline"] or "Yo'q"
 
    builder = InlineKeyboardBuilder()
    builder.button(text="🏆 Reyting", callback_data=f"t_rating_{test_id}")
    builder.button(text="📊 Tahlil", callback_data=f"t_analysis_{test_id}")
    builder.button(text="🔍 Batafsil natijalar", callback_data=f"t_results_{test_id}")
    builder.adjust(2, 1)
 
    await callback.message.edit_text(
        f"📋 <b>{test['title']}</b>\n"
        f"🆔 {test['test_code']} | 🔢 {test['question_count']} ta\n"
        f"⏰ Deadline: {dl} | {status}\n"
        f"👥 Ishtirokchilar: <b>{len(results)}</b> ta\n\n"
        f"Qaysi bo'limni ko'rmoqchisiz?",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
 
 
# ===== REYTING =====
@router.callback_query(F.data.startswith("t_rating_"))
async def show_rating(callback: CallbackQuery):
    test_id = int(callback.data.split("_")[2])
    all_tests = await db.get_all_tests()
    test = next((t for t in all_tests if t["id"] == test_id), None)
    results = await db.get_test_results(test_id)
 
    if not results:
        await callback.answer("Hali natijalar yo'q!", show_alert=True)
        return
 
    medals = ["🥇", "🥈", "🥉"]
    text = f"🏆 <b>{test['title']} — Reyting</b>\n"
    text += f"👥 Jami: {len(results)} ta ishtirokchi\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"
 
    for i, r in enumerate(results[:20], 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        bar_filled = int(r["percentage"] / 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        text += (
            f"{medal} <b>{r['first_name']} {r['last_name']}</b>\n"
            f"   {bar} {r['percentage']:.1f}%\n"
            f"   ✅ {r['correct']}/{r['total']} | 📅 {r['taken_at'][:10]}\n\n"
        )
 
    if len(results) > 20:
        text += f"... va yana {len(results)-20} ta"
 
    avg = sum(r["percentage"] for r in results) / len(results)
    text += f"\n📊 O'rtacha: <b>{avg:.1f}%</b>"
 
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Orqaga", callback_data=f"mytest_{test_id}")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
 
 
# ===== TAHLIL (ANALYTICS) =====
@router.callback_query(F.data.startswith("t_analysis_"))
async def show_analysis(callback: CallbackQuery):
    test_id = int(callback.data.split("_")[2])
    all_tests = await db.get_all_tests()
    test = next((t for t in all_tests if t["id"] == test_id), None)
    results = await db.get_test_results(test_id)
 
    if not results:
        await callback.answer("Hali natijalar yo'q!", show_alert=True)
        return
 
    total_participants = len(results)
    correct_ans = test["answers"]
    question_count = test["question_count"]
 
    # Har bir savol uchun to'g'ri javob berganlar soni
    question_stats = []
    for q_idx in range(question_count):
        correct = 0
        answer_dist = Counter()
        for r in results:
            user_ans = r["user_answers"]
            if q_idx < len(user_ans):
                given = user_ans[q_idx]
            else:
                given = "-"
            answer_dist[given] += 1
            if given == correct_ans[q_idx]:
                correct += 1
        pct = (correct / total_participants * 100) if total_participants > 0 else 0
        question_stats.append({
            "q": q_idx + 1,
            "correct": correct,
            "pct": pct,
            "correct_ans": correct_ans[q_idx],
            "dist": answer_dist
        })
 
    # Eng ko'p xato qilingan savollar
    hardest = sorted(question_stats, key=lambda x: x["pct"])[:5]
    # Eng oson savollar
    easiest = sorted(question_stats, key=lambda x: x["pct"], reverse=True)[:5]
 
    avg_pct = sum(r["percentage"] for r in results) / total_participants
    above_avg = sum(1 for r in results if r["percentage"] >= 60)
    below_avg = total_participants - above_avg
 
    text = (
        f"📊 <b>{test['title']} — Tahlil</b>\n"
        f"👥 Ishtirokchilar: {total_participants} ta\n"
        f"📈 O'rtacha natija: <b>{avg_pct:.1f}%</b>\n"
        f"✅ 60%+ olganlar: <b>{above_avg}</b> ta\n"
        f"❌ 60% dan past: <b>{below_avg}</b> ta\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔴 <b>Eng qiyin savollar</b> (ko'p xato):\n\n"
    )
    for s in hardest:
        bar = "█" * int(s["pct"] / 10) + "░" * (10 - int(s["pct"] / 10))
        dist_str = " | ".join(f"{k}:{v}" for k, v in sorted(s["dist"].items()) if k != "-")
        text += (
            f"❓ <b>{s['q']}-savol</b> (to'g'ri: {s['correct_ans']})\n"
            f"   {bar} {s['pct']:.0f}% to'g'ri\n"
            f"   [{dist_str}]\n\n"
        )
 
    text += f"━━━━━━━━━━━━━━━━━━\n🟢 <b>Eng oson savollar</b>:\n\n"
    for s in easiest:
        text += f"✅ <b>{s['q']}-savol</b> — {s['pct']:.0f}% to'g'ri javob berdi\n"
 
    builder = InlineKeyboardBuilder()
    builder.button(text="📈 Barcha savollar tahlili", callback_data=f"t_allq_{test_id}")
    builder.button(text="◀️ Orqaga", callback_data=f"mytest_{test_id}")
    builder.adjust(1)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
 
 
# ===== BARCHA SAVOLLAR TAHLILI =====
@router.callback_query(F.data.startswith("t_allq_"))
async def show_all_questions(callback: CallbackQuery):
    test_id = int(callback.data.split("_")[2])
    all_tests = await db.get_all_tests()
    test = next((t for t in all_tests if t["id"] == test_id), None)
    results = await db.get_test_results(test_id)
 
    if not results:
        await callback.answer("Natijalar yo'q!", show_alert=True)
        return
 
    total = len(results)
    correct_ans = test["answers"]
 
    lines = ["<b>Savol | To'g'ri% | Javob taqsimoti</b>\n"]
    for q_idx in range(test["question_count"]):
        dist = Counter()
        correct_count = 0
        for r in results:
            ua = r["user_answers"]
            given = ua[q_idx] if q_idx < len(ua) else "-"
            dist[given] += 1
            if given == correct_ans[q_idx]:
                correct_count += 1
        pct = correct_count / total * 100
        icon = "🟢" if pct >= 70 else "🟡" if pct >= 40 else "🔴"
        dist_str = " ".join(f"{k}:{v}" for k, v in sorted(dist.items()) if k != "-")
        lines.append(f"{icon}<b>{q_idx+1:>3}</b>. {pct:>5.1f}% | {dist_str}")
 
    # Chunklarga bo'lib yuborish
    chunk_size = 30
    chunks = [lines[i:i+chunk_size] for i in range(0, len(lines), chunk_size)]
 
    await callback.message.answer(
        "\n".join(chunks[0]),
        parse_mode="HTML"
    )
    for chunk in chunks[1:]:
        await callback.message.answer("\n".join(chunk), parse_mode="HTML")
 
    await callback.answer()
 
 
# ===== BATAFSIL NATIJALAR =====
@router.callback_query(F.data.startswith("t_results_"))
async def show_test_results(callback: CallbackQuery):
    test_id = int(callback.data.split("_")[2])
    all_tests = await db.get_all_tests()
    test = next((t for t in all_tests if t["id"] == test_id), None)
    results = await db.get_test_results(test_id)
 
    if not results:
        await callback.answer("Hali natijalar yo'q!", show_alert=True)
        return
 
    builder = InlineKeyboardBuilder()
    for r in results[:15]:
        builder.button(
            text=f"🔍 {r['first_name']} {r['last_name']} ({r['percentage']:.0f}%)",
            callback_data=f"rdetail_{r['id']}_{test_id}"
        )
    builder.button(text="◀️ Orqaga", callback_data=f"mytest_{test_id}")
    builder.adjust(1)
 
    text = f"🔍 <b>Batafsil natijalar</b> ({len(results)} ta)\n\n"
    for i, r in enumerate(results[:15], 1):
        text += f"{i}. {r['first_name']} {r['last_name']} — {r['percentage']:.1f}%\n"
 
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
 
 
@router.callback_query(F.data.startswith("rdetail_"))
async def show_result_detail(callback: CallbackQuery):
    parts = callback.data.split("_")
    result_id = int(parts[1])
    test_id = int(parts[2])
 
    results = await db.get_test_results(test_id)
    result = next((r for r in results if r["id"] == result_id), None)
    if not result:
        await callback.answer("Natija topilmadi!", show_alert=True)
        return
 
    all_tests = await db.get_all_tests()
    test = next((t for t in all_tests if t["id"] == test_id), None)
 
    user_ans = result["user_answers"]
    correct_ans = test["answers"]
 
    lines = []
    for i in range(test["question_count"]):
        u = user_ans[i] if i < len(user_ans) else "-"
        c = correct_ans[i]
        icon = "✅" if u == c else "❌"
        detail = f" → {c}" if u != c else ""
        lines.append(f"{i+1:>3}. {icon} {u}{detail}")
 
    header = (
        f"🔍 <b>{result['first_name']} {result['last_name']}</b>\n"
        f"📌 {test['title']} | 🆔 {test['test_code']}\n"
        f"✅ To'g'ri: {result['correct']}/{result['total']} ({result['percentage']:.1f}%)\n"
        f"📅 {result['taken_at'][:16]}\n\n"
        f"<b>Tahlil</b> ✅ to'g'ri | ❌ xato → to'g'ri:\n\n"
    )
 
    chunks = [lines[i:i+50] for i in range(0, len(lines), 50)]
    await callback.message.answer(
        header + "<code>" + "\n".join(chunks[0]) + "</code>",
        parse_mode="HTML"
    )
    for chunk in chunks[1:]:
        await callback.message.answer("<code>" + "\n".join(chunk) + "</code>", parse_mode="HTML")
    await callback.answer()
 
 
# ============ JAVOBNI TEKSHIRISH ============
 
@router.message(F.text == "✅ Javobni tekshirish")
async def start_solve_test(message: Message, state: FSMContext, bot: Bot):
    if not await ensure_registered(message, bot):
        return
    await state.clear()
    await state.set_state(SolveTest.test_code)
    await message.answer(
        "✍️ Test kodini yuboring.\n\nMasalan: <code>ABC1234</code>",
        reply_markup=back_kb(),
        parse_mode="HTML"
    )
 
 
@router.message(StateFilter(SolveTest.test_code))
async def get_test_code(message: Message, state: FSMContext):
    if message.text in ["🔄 Orqaga", "❌ Bekor qilish"]:
        await state.clear()
        await message.answer("🏠 Bosh sahifa.", reply_markup=main_menu_kb())
        return
 
    code = message.text.strip().upper()
    test = await db.get_test_by_code(code)
    if not test:
        await message.answer("❌ Bunday test topilmadi!")
        return
 
    if is_deadline_passed(test["deadline"]):
        await message.answer(
            f"⏰ <b>Test muddati tugagan!</b>\n\n"
            f"📌 {test['title']}\n"
            f"🔴 Deadline: {test['deadline']}",
            parse_mode="HTML"
        )
        return
 
    dl_info = f"\n⏰ Deadline: <b>{test['deadline']}</b>" if test["deadline"] else ""
    await state.update_data(
        test_code=code, test_id=test["id"],
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
        f"{dl_info}\n\n"
        f"✏️ Javoblarni yuboring.\n"
        f"Format: <b>ABCDDCBA...</b>\n\n"
        f"💡 Agar kam javob yuborsangiz, qolganlar <b>xato</b> hisoblanadi.",
        reply_markup=back_kb(),
        parse_mode="HTML"
    )
 
 
@router.message(StateFilter(SolveTest.answers))
async def check_answers(message: Message, state: FSMContext, bot: Bot):
    if message.text in ["🔄 Orqaga", "❌ Bekor qilish"]:
        await state.clear()
        await message.answer("🏠 Bosh sahifa.", reply_markup=main_menu_kb())
        return
 
    data = await state.get_data()
    test = await db.get_test_by_code(data["test_code"])
 
    if is_deadline_passed(test["deadline"]):
        await state.clear()
        await message.answer("⏰ Test muddati tugadi!", reply_markup=main_menu_kb())
        return
 
    user_answers = normalize_answers(message.text)
    total = data["total"]
 
    # ✅ Kam javob bo'lsa — qolganlar xato hisoblanadi (to'ldirish kerak emas)
    if len(user_answers) == 0:
        await message.answer(
            "❌ Hech qanday javob topilmadi!\n"
            "A, B, C, D harflaridan foydalaning."
        )
        return
 
    # Kam bo'lsa ogohlantirish, lekin qabul qilish
    if len(user_answers) < total:
        # To'ldirish — qolganlar "-" (xato)
        missing = total - len(user_answers)
        # Xabar berish lekin davom etish
        await message.answer(
            f"⚠️ Siz <b>{len(user_answers)}</b> ta javob yubordingiz, "
            f"test <b>{total}</b> ta savoldan iborat.\n"
            f"Qolgan <b>{missing}</b> ta savol <b>xato</b> hisoblanadi.\n\n"
            f"🔄 Natija hisoblanmoqda...",
            parse_mode="HTML"
        )
 
    correct_answers = list(test["answers"])
    # Kam javoblarni to'ldirish (xato sifatida)
    user_ans = user_answers[:total]
    while len(user_ans) < total:
        user_ans.append("-")  # Bo'sh = xato
 
    correct_count = sum(1 for u, c in zip(user_ans, correct_answers) if u == c)
    pct = (correct_count / total * 100) if total > 0 else 0
    await state.clear()
 
    user = await db.get_user(message.from_user.id)
    full_name = f"{user['first_name']} {user['last_name']}"
 
    await db.save_result(
        user_id=message.from_user.id,
        test_id=data["test_id"],
        correct=correct_count,
        total=total,
        percentage=pct,
        user_answers="".join(user_ans)
    )
 
    await message.answer("🎨 Sertifikat tayyorlanmoqda...")
    cert_buf = generate_certificate(
        design_num=user["cert_design"],
        full_name=full_name,
        test_title=data["test_title"],
        correct=correct_count,
        total=total,
        author=data["test_author"]
    )
 
    wrong = [(i+1, u, c) for i, (u, c) in enumerate(zip(user_ans, correct_answers)) if u != c]
    wrong_text = ""
    if wrong:
        empty = "(bosh)"
        shown = [f"{i}: {u if u != '-' else '(bo\\'sh)'}→{c}" for i, u, c in wrong[:10]]
        wrong_text = "\n\n❌ <b>Xato javoblar:</b>\n" + "  |  ".join(shown)
        if len(wrong) > 10:
            wrong_text += f"\n... va yana {len(wrong)-10} ta xato"
 
    emoji = "🏆" if pct >= 80 else "✅" if pct >= 60 else "📊"
    await message.answer_photo(
        photo=BufferedInputFile(cert_buf.read(), filename="sertifikat.png"),
        caption=(
            f"{emoji} <b>Natijangiz</b>\n\n"
            f"👤 {full_name}\n"
            f"📌 Fan: {data['test_title']}\n"
            f"✅ To'g'ri: {correct_count}/{total}\n"
            f"📊 Foiz: {pct:.1f}%\n"
            f"👤 Muallif: {data['test_author']}"
            f"{wrong_text}"
        ),
        parse_mode="HTML",
        protect_content=True
    )
 
