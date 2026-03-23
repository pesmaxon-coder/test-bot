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
    title       = State()
    answers     = State()
    deadline    = State()


class SolveTest(StatesGroup):
    test_code = State()
    answers   = State()


def normalize_answers(text):
    return re.findall(r'[ABCDE]', text.upper())


def parse_deadline(text):
    text = text.strip().replace("/", ".").replace("-", ".")
    for fmt in ["%d.%m.%Y %H:%M", "%d.%m.%Y"]:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def is_deadline_passed(deadline_str):
    if not deadline_str:
        return False
    try:
        return datetime.now() > datetime.strptime(deadline_str, "%d.%m.%Y %H:%M")
    except Exception:
        return False


async def ensure_registered(message, bot):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Avval /start bosing!")
        return False
    if not await check_subscriptions(bot, message.from_user.id):
        from keyboards import subscription_kb
        await message.answer("Kanallarga a'zo bo'ling!", reply_markup=subscription_kb())
        return False
    return True


def deadline_kb():
    b = ReplyKeyboardBuilder()
    b.button(text="Deadline yoq saqlash")
    b.button(text="Bekor qilish")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)


# ============ TEST YARATISH ============

@router.message(F.text == "✍️ Test yaratish")
async def start_create_test(message: Message, state: FSMContext, bot: Bot):
    if not await ensure_registered(message, bot):
        return
    await state.clear()
    await state.set_state(CreateTest.choose_type)
    await message.answer("Kerakli bolimni tanlang.", reply_markup=test_type_kb())


@router.message(
    StateFilter(CreateTest.choose_type),
    F.text.in_(["📝 Oddiy test", "📕 Fanli test", "📦 Maxsus test", "📗 Blok test"])
)
async def choose_test_type(message: Message, state: FSMContext):
    await state.update_data(test_type=message.text)
    await state.set_state(CreateTest.title)
    await message.answer("Test nomini kiriting:\nMasalan: Matematika, Ingliz tili", reply_markup=cancel_kb())


@router.message(StateFilter(CreateTest.choose_type))
async def choose_type_fallback(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bosh sahifa.", reply_markup=main_menu_kb())


@router.message(StateFilter(CreateTest.title))
async def get_test_title(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga", "Bekor qilish"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(CreateTest.answers)
    await message.answer(
        "Test kalitlarini yuboring.\n\n"
        "Format: ABCDDCBAABCD\n"
        "yoki: 1A 2B 3C 4D 5A\n\n"
        "Faqat A B C D E harflari qabul qilinadi.",
        reply_markup=cancel_kb()
    )


@router.message(StateFilter(CreateTest.answers))
async def get_test_answers(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga", "Bekor qilish"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
        return
    answers = normalize_answers(message.text)
    if len(answers) < 5:
        await message.answer("Kamida 5 ta javob kiriting!")
        return
    if len(answers) > 200:
        await message.answer("Kopida 200 ta savol bolishi mumkin!")
        return
    await state.update_data(answers="".join(answers))
    await state.set_state(CreateTest.deadline)
    await message.answer(
        str(len(answers)) + " ta javob qabul qilindi!\n\n"
        "Deadline belgilash\n\n"
        "Kun: 25.12.2024\n"
        "Vaqt bilan: 25.12.2024 18:00\n\n"
        "Deadline kerak bolmasa quyidagi tugmani bosing:",
        reply_markup=deadline_kb()
    )


@router.message(StateFilter(CreateTest.deadline))
async def get_test_deadline(message: Message, state: FSMContext):
    if message.text in ["Bekor qilish", "❌ Bekor qilish", "🔄 Orqaga"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
        return

    data = await state.get_data()
    deadline_str = None

    if message.text == "Deadline yoq saqlash":
        deadline_str = None
    else:
        deadline = parse_deadline(message.text)
        if deadline is None:
            await message.answer(
                "Format notogri!\n\n"
                "25.12.2024\n"
                "yoki\n"
                "25.12.2024 18:00\n\n"
                "Deadline kerak bolmasa tugmani bosing:",
                reply_markup=deadline_kb()
            )
            return
        if deadline < datetime.now():
            await message.answer("Bu sana otib ketgan! Kelajakdagi sana kiriting.", reply_markup=deadline_kb())
            return
        deadline_str = deadline.strftime("%d.%m.%Y %H:%M")

    user = await db.get_user(message.from_user.id)
    full_name = user['first_name'] + " " + user['last_name']
    code = await db.create_test(
        creator_id=message.from_user.id,
        creator_name=full_name,
        title=data["title"],
        answers=data["answers"],
        deadline=deadline_str
    )
    await state.clear()

    if deadline_str:
        dl_text = "Deadline: " + deadline_str
    else:
        dl_text = "Deadline: Yoq (cheksiz)"

    await message.answer(
        "Test yaratildi!\n\n"
        "Fan: " + data['title'] + "\n"
        "Savollar: " + str(len(data['answers'])) + " ta\n"
        "Test ID: " + code + "\n"
        + dl_text + "\n\n"
        "Bu ID ni kanalga joylashtiring!",
        reply_markup=main_menu_kb()
    )


# ============ MENING TESTLARIM ============

@router.message(F.text == "📊 Mening testlarim")
async def my_tests(message: Message, bot: Bot):
    if not await ensure_registered(message, bot):
        return
    tests = await db.get_creator_tests(message.from_user.id)
    if not tests:
        await message.answer("Siz hali test yaratmagansiz.", reply_markup=main_menu_kb())
        return

    builder = InlineKeyboardBuilder()
    for t in tests[:20]:
        passed = is_deadline_passed(t["deadline"])
        status = "🔴" if passed else "🟢"
        dl = t["deadline"] if t["deadline"] else "cheksiz"
        label = t['title'][:15]
        builder.button(
            text=status + " " + t['test_code'] + " | " + label + " | " + dl,
            callback_data="mytest_" + str(t['id'])
        )
    builder.adjust(1)
    await message.answer(
        "Mening testlarim (" + str(len(tests)) + " ta)\n\n"
        "🟢 Faol  |  🔴 Muddat otgan\n\n"
        "Batafsil korish uchun tanlang:",
        reply_markup=builder.as_markup()
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
            await callback.answer("Bu test sizniki emas!", show_alert=True)
            return

    results = await db.get_test_results(test_id)
    passed = is_deadline_passed(test["deadline"])
    status = "🔴 Muddat otgan" if passed else "🟢 Faol"
    dl = test["deadline"] or "Yoq"

    builder = InlineKeyboardBuilder()
    builder.button(text="🏆 Reyting", callback_data="t_rating_" + str(test_id))
    builder.button(text="📊 Tahlil", callback_data="t_analysis_" + str(test_id))
    builder.button(text="🔍 Batafsil", callback_data="t_results_" + str(test_id))
    builder.adjust(2, 1)

    await callback.message.edit_text(
        "📋 " + test['title'] + "\n"
        "ID: " + test['test_code'] + " | " + str(test['question_count']) + " ta savol\n"
        "Deadline: " + dl + " | " + status + "\n"
        "Ishtirokchilar: " + str(len(results)) + " ta\n\n"
        "Qaysi bolimni kormoqchisiz?",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("t_rating_"))
async def show_rating(callback: CallbackQuery):
    test_id = int(callback.data.split("_")[2])
    all_tests = await db.get_all_tests()
    test = next((t for t in all_tests if t["id"] == test_id), None)
    results = await db.get_test_results(test_id)

    if not results:
        await callback.answer("Hali natijalar yoq!", show_alert=True)
        return

    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 " + test['title'] + " — Reyting\n"
    text += "Jami: " + str(len(results)) + " ta ishtirokchi\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"

    avg = sum(r["percentage"] for r in results) / len(results)

    for i, r in enumerate(results[:20], 1):
        medal = medals[i-1] if i <= 3 else str(i) + "."
        filled = int(r["percentage"] / 10)
        bar = "█" * filled + "░" * (10 - filled)
        text += (
            medal + " " + r['first_name'] + " " + r['last_name'] + "\n"
            "   " + bar + " " + str(round(r['percentage'], 1)) + "%\n"
            "   ✅ " + str(r['correct']) + "/" + str(r['total']) + "\n\n"
        )

    if len(results) > 20:
        text += "... va yana " + str(len(results) - 20) + " ta\n"

    text += "\nOrtacha: " + str(round(avg, 1)) + "%"

    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Orqaga", callback_data="mytest_" + str(test_id))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("t_analysis_"))
async def show_analysis(callback: CallbackQuery):
    test_id = int(callback.data.split("_")[2])
    all_tests = await db.get_all_tests()
    test = next((t for t in all_tests if t["id"] == test_id), None)
    results = await db.get_test_results(test_id)

    if not results:
        await callback.answer("Hali natijalar yoq!", show_alert=True)
        return

    total_p = len(results)
    correct_ans = test["answers"]
    q_count = test["question_count"]

    question_stats = []
    for q_idx in range(q_count):
        correct = 0
        dist = Counter()
        for r in results:
            ua = r["user_answers"]
            given = ua[q_idx] if q_idx < len(ua) else "-"
            dist[given] += 1
            if given == correct_ans[q_idx]:
                correct += 1
        pct = (correct / total_p * 100) if total_p > 0 else 0
        question_stats.append({
            "q": q_idx + 1,
            "correct": correct,
            "pct": pct,
            "correct_ans": correct_ans[q_idx],
            "dist": dist
        })

    hardest = sorted(question_stats, key=lambda x: x["pct"])[:5]
    easiest = sorted(question_stats, key=lambda x: x["pct"], reverse=True)[:5]

    avg_pct = sum(r["percentage"] for r in results) / total_p
    above = sum(1 for r in results if r["percentage"] >= 60)
    below = total_p - above

    text = (
        "📊 " + test['title'] + " — Tahlil\n"
        "Ishtirokchilar: " + str(total_p) + " ta\n"
        "Ortacha natija: " + str(round(avg_pct, 1)) + "%\n"
        "60%+ olganlar: " + str(above) + " ta\n"
        "60% dan past: " + str(below) + " ta\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔴 Eng qiyin savollar:\n\n"
    )

    for s in hardest:
        filled = int(s["pct"] / 10)
        bar = "█" * filled + "░" * (10 - filled)
        dist_items = sorted(s["dist"].items())
        dist_str = " | ".join(k + ":" + str(v) for k, v in dist_items if k != "-")
        text += (
            str(s['q']) + "-savol (togri: " + s['correct_ans'] + ")\n"
            "   " + bar + " " + str(round(s['pct'], 0)) + "% togri\n"
            "   [" + dist_str + "]\n\n"
        )

    text += "━━━━━━━━━━━━━━━━━━\n🟢 Eng oson savollar:\n\n"
    for s in easiest:
        text += str(s['q']) + "-savol — " + str(round(s['pct'], 0)) + "% togri javob berdi\n"

    builder = InlineKeyboardBuilder()
    builder.button(text="📈 Barcha savollar", callback_data="t_allq_" + str(test_id))
    builder.button(text="◀️ Orqaga", callback_data="mytest_" + str(test_id))
    builder.adjust(1)
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("t_allq_"))
async def show_all_questions(callback: CallbackQuery):
    test_id = int(callback.data.split("_")[2])
    all_tests = await db.get_all_tests()
    test = next((t for t in all_tests if t["id"] == test_id), None)
    results = await db.get_test_results(test_id)

    if not results:
        await callback.answer("Natijalar yoq!", show_alert=True)
        return

    total = len(results)
    correct_ans = test["answers"]
    lines = ["Savol | Togri% | Javob taqsimoti\n"]

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
        if pct >= 70:
            icon = "🟢"
        elif pct >= 40:
            icon = "🟡"
        else:
            icon = "🔴"
        dist_str = " ".join(k + ":" + str(v) for k, v in sorted(dist.items()) if k != "-")
        num = str(q_idx + 1)
        lines.append(icon + num + ". " + str(round(pct, 1)) + "% | " + dist_str)

    chunks = [lines[i:i+30] for i in range(0, len(lines), 30)]
    await callback.message.answer("\n".join(chunks[0]))
    for chunk in chunks[1:]:
        await callback.message.answer("\n".join(chunk))
    await callback.answer()


@router.callback_query(F.data.startswith("t_results_"))
async def show_test_results(callback: CallbackQuery):
    test_id = int(callback.data.split("_")[2])
    all_tests = await db.get_all_tests()
    test = next((t for t in all_tests if t["id"] == test_id), None)
    results = await db.get_test_results(test_id)

    if not results:
        await callback.answer("Hali natijalar yoq!", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for r in results[:15]:
        name = r['first_name'] + " " + r['last_name']
        pct = str(round(r['percentage'], 0))
        builder.button(
            text="🔍 " + name + " (" + pct + "%)",
            callback_data="rdetail_" + str(r['id']) + "_" + str(test_id)
        )
    builder.button(text="◀️ Orqaga", callback_data="mytest_" + str(test_id))
    builder.adjust(1)

    text = "Batafsil natijalar (" + str(len(results)) + " ta)\n\n"
    for i, r in enumerate(results[:15], 1):
        text += str(i) + ". " + r['first_name'] + " " + r['last_name'] + " — " + str(round(r['percentage'], 1)) + "%\n"

    await callback.message.edit_text(text, reply_markup=builder.as_markup())


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
        if u == c:
            lines.append(str(i+1) + ". OK " + u)
        else:
            lines.append(str(i+1) + ". XX " + u + " -> " + c)

    header = (
        result['first_name'] + " " + result['last_name'] + "\n"
        + test['title'] + " | " + test['test_code'] + "\n"
        "Togri: " + str(result['correct']) + "/" + str(result['total'])
        + " (" + str(round(result['percentage'], 1)) + "%)\n"
        + result['taken_at'][:16] + "\n\n"
        "Tahlil (OK togri | XX xato -> togri):\n\n"
    )

    chunks = [lines[i:i+50] for i in range(0, len(lines), 50)]
    await callback.message.answer(header + "\n".join(chunks[0]))
    for chunk in chunks[1:]:
        await callback.message.answer("\n".join(chunk))
    await callback.answer()


# ============ JAVOBNI TEKSHIRISH ============

@router.message(F.text == "✅ Javobni tekshirish")
async def start_solve_test(message: Message, state: FSMContext, bot: Bot):
    if not await ensure_registered(message, bot):
        return
    await state.clear()
    await state.set_state(SolveTest.test_code)
    await message.answer("Test kodini yuboring.\n\nMasalan: ABC1234", reply_markup=back_kb())


@router.message(StateFilter(SolveTest.test_code))
async def get_test_code(message: Message, state: FSMContext):
    if message.text in ["🔄 Orqaga", "❌ Bekor qilish"]:
        await state.clear()
        await message.answer("Bosh sahifa.", reply_markup=main_menu_kb())
        return

    code = message.text.strip().upper()
    test = await db.get_test_by_code(code)
    if not test:
        await message.answer("Bunday test topilmadi!")
        return

    if is_deadline_passed(test["deadline"]):
        await message.answer(
            "Test muddati tugagan!\n\n"
            + test['title'] + "\n"
            "Deadline: " + str(test['deadline'])
        )
        return

    if test["deadline"]:
        dl_info = "\nDeadline: " + test["deadline"]
    else:
        dl_info = ""

    await state.update_data(
        test_code=code,
        test_id=test["id"],
        total=test["question_count"],
        test_title=test["title"],
        test_author=test["creator_name"]
    )
    await state.set_state(SolveTest.answers)
    await message.answer(
        "Test topildi!\n\n"
        "Fan: " + test['title'] + "\n"
        "Savollar: " + str(test['question_count']) + " ta\n"
        "Muallif: " + test['creator_name']
        + dl_info + "\n\n"
        "Javoblarni yuboring. Format: ABCDDCBA...\n\n"
        "Agar kam javob yuborsangiz, qolganlar xato hisoblanadi.",
        reply_markup=back_kb()
    )


@router.message(StateFilter(SolveTest.answers))
async def check_answers(message: Message, state: FSMContext, bot: Bot):
    if message.text in ["🔄 Orqaga", "❌ Bekor qilish"]:
        await state.clear()
        await message.answer("Bosh sahifa.", reply_markup=main_menu_kb())
        return

    data = await state.get_data()
    test = await db.get_test_by_code(data["test_code"])

    if is_deadline_passed(test["deadline"]):
        await state.clear()
        await message.answer("Test muddati tugadi!", reply_markup=main_menu_kb())
        return

    user_answers = normalize_answers(message.text)
    total = data["total"]

    if len(user_answers) == 0:
        await message.answer("Hech qanday javob topilmadi! A B C D harflaridan foydalaning.")
        return

    if len(user_answers) < total:
        missing = total - len(user_answers)
        await message.answer(
            str(len(user_answers)) + " ta javob yuborildi, "
            + str(total) + " ta savol bor.\n"
            "Qolgan " + str(missing) + " ta savol xato hisoblanadi.\n\n"
            "Natija hisoblanmoqda..."
        )

    correct_answers = list(test["answers"])
    user_ans = list(user_answers[:total])
    while len(user_ans) < total:
        user_ans.append("-")

    correct_count = sum(1 for u, c in zip(user_ans, correct_answers) if u == c)
    pct = (correct_count / total * 100) if total > 0 else 0
    await state.clear()

    user = await db.get_user(message.from_user.id)
    full_name = user['first_name'] + " " + user['last_name']

    await db.save_result(
        user_id=message.from_user.id,
        test_id=data["test_id"],
        correct=correct_count,
        total=total,
        percentage=pct,
        user_answers="".join(user_ans)
    )

    await message.answer("Sertifikat tayyorlanmoqda...")
    cert_buf = generate_certificate(
        design_num=user["cert_design"],
        full_name=full_name,
        test_title=data["test_title"],
        correct=correct_count,
        total=total,
        author=data["test_author"]
    )

    wrong_lines = []
    for i, (u, c) in enumerate(zip(user_ans, correct_answers)):
        if u != c:
            if u == "-":
                wrong_lines.append(str(i+1) + ": bosh -> " + c)
            else:
                wrong_lines.append(str(i+1) + ": " + u + " -> " + c)

    wrong_text = ""
    if wrong_lines:
        shown = wrong_lines[:10]
        wrong_text = "\n\nXato javoblar:\n" + "  |  ".join(shown)
        if len(wrong_lines) > 10:
            wrong_text += "\n... va yana " + str(len(wrong_lines) - 10) + " ta xato"

    if pct >= 80:
        emoji = "🏆"
    elif pct >= 60:
        emoji = "✅"
    else:
        emoji = "📊"

    caption = (
        emoji + " Natijangiz\n\n"
        "Foydalanuvchi: " + full_name + "\n"
        "Fan: " + data['test_title'] + "\n"
        "Togri: " + str(correct_count) + "/" + str(total) + "\n"
        "Foiz: " + str(round(pct, 1)) + "%\n"
        "Muallif: " + data['test_author']
        + wrong_text
    )

    await message.answer_photo(
        photo=BufferedInputFile(cert_buf.read(), filename="sertifikat.png"),
        caption=caption,
        protect_content=True
    )
