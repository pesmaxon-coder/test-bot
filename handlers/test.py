from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
from collections import Counter
import re

import database as db
from keyboards import (
    main_menu_kb, test_type_kb, cancel_kb, back_kb,
    deadline_kb, confirm_answers_kb
)
from utils.certificate import generate_certificate
from handlers.registration import check_sub

router = Router()


class CreateTest(StatesGroup):
    choose_type = State()
    title = State()
    answers = State()
    deadline = State()


class SolveTest(StatesGroup):
    test_code = State()
    answers = State()
    confirm = State()


def get_answers(text):
    return re.findall(r'[ABCDE]', text.upper())


def parse_date(text):
    text = text.strip().replace("/", ".").replace("-", ".")
    for fmt in ["%d.%m.%Y %H:%M", "%d.%m.%Y"]:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def deadline_over(dl):
    if not dl:
        return False
    try:
        return datetime.now() > datetime.strptime(dl, "%d.%m.%Y %H:%M")
    except Exception:
        return False


async def check_registered(message: Message, bot: Bot):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❗ Avval /start bosing!")
        return False
    if await db.is_bot_paused() and not await db.is_admin_db(message.from_user.id):
        await message.answer("⏸ Bot hozircha to'xtatilgan.")
        return False
    if not await check_sub(bot, message.from_user.id):
        from keyboards import sub_kb
        channels = await db.get_channels("required")
        await message.answer("📢 Kanallarga a'zo bo'ling!", reply_markup=sub_kb(channels))
        return False
    return True


# ===== TEST YARATISH =====

@router.message(F.text == "✍️ Test yaratish")
async def start_create(message: Message, state: FSMContext, bot: Bot):
    if not await check_registered(message, bot):
        return
    await state.clear()
    await state.set_state(CreateTest.choose_type)
    await message.answer(
        "✍️ <b>Test yaratish</b>\n\n❗ Kerakli bo'limni tanlang:",
        reply_markup=test_type_kb(),
        parse_mode="HTML"
    )


@router.message(
    StateFilter(CreateTest.choose_type),
    F.text.in_(["📝 Oddiy test", "📕 Fanli test", "📦 Maxsus test", "📗 Blok test"])
)
async def choose_type(message: Message, state: FSMContext):
    await state.update_data(test_type=message.text)
    await state.set_state(CreateTest.title)
    await message.answer(
        "📌 <b>Test nomini kiriting</b>\n\nMasalan: Matematika, Ingliz tili, Kimyo",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )


@router.message(StateFilter(CreateTest.choose_type))
async def choose_type_other(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Bosh sahifa.", reply_markup=main_menu_kb())


@router.message(StateFilter(CreateTest.title))
async def get_title(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(CreateTest.answers)
    await message.answer(
        "✏️ <b>Test kalitlarini yuboring</b>\n\n"
        "📌 Format: <code>ABCDDCBAABCD</code>\n"
        "📌 yoki: <code>1A 2B 3C 4D 5A</code>\n\n"
        "⚠️ Faqat A B C D E harflari qabul qilinadi.",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )


@router.message(StateFilter(CreateTest.answers))
async def get_answers_for_test(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return
    answers = get_answers(message.text)
    if len(answers) < 5:
        await message.answer("❌ Kamida <b>5 ta</b> javob kiriting!", parse_mode="HTML")
        return
    if len(answers) > 200:
        await message.answer("❌ Ko'pi bilan <b>200 ta</b> savol bo'lishi mumkin!", parse_mode="HTML")
        return
    await state.update_data(answers="".join(answers))
    await state.set_state(CreateTest.deadline)
    await message.answer(
        "✅ <b>" + str(len(answers)) + " ta javob</b> qabul qilindi!\n\n"
        "⏰ <b>Deadline belgilash</b>\n\n"
        "📅 Kun: <code>25.12.2024</code>\n"
        "🕐 Vaqt bilan: <code>25.12.2024 18:00</code>\n\n"
        "Deadline kerak bo'lmasa quyidagi tugmani bosing 👇",
        reply_markup=deadline_kb(),
        parse_mode="HTML"
    )


@router.message(StateFilter(CreateTest.deadline))
async def get_deadline(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return

    data = await state.get_data()
    deadline_str = None

    if message.text == "♾️ Deadline kerak emas":
        deadline_str = None
    else:
        dl = parse_date(message.text)
        if dl is None:
            await message.answer(
                "❌ <b>Format noto'g'ri!</b>\n\n"
                "✅ To'g'ri formatlar:\n"
                "📅 <code>25.12.2024</code>\n"
                "🕐 <code>25.12.2024 18:00</code>\n\n"
                "Yoki deadline kerak bo'lmasa tugmani bosing 👇",
                reply_markup=deadline_kb(),
                parse_mode="HTML"
            )
            return
        if dl < datetime.now():
            await message.answer(
                "❌ Bu sana allaqachon o'tib ketgan!\n"
                "📅 Kelajakdagi sana kiriting:",
                reply_markup=deadline_kb()
            )
            return
        deadline_str = dl.strftime("%d.%m.%Y %H:%M")

    user = await db.get_user(message.from_user.id)
    full_name = user["first_name"] + " " + user["last_name"]
    code = await db.create_test(
        creator_id=message.from_user.id,
        creator_name=full_name,
        title=data["title"],
        answers=data["answers"],
        deadline=deadline_str
    )
    await state.clear()

    dl_text = "⏰ Deadline: <b>" + deadline_str + "</b>" if deadline_str else "♾️ Deadline: <b>Yo'q (cheksiz)</b>"
    await message.answer(
        "🎉 <b>Test muvaffaqiyatli yaratildi!</b>\n\n"
        "📌 Fan: <b>" + data["title"] + "</b>\n"
        "🔢 Savollar: <b>" + str(len(data["answers"])) + "</b> ta\n"
        "🆔 Test ID: <code>" + code + "</code>\n"
        + dl_text + "\n\n"
        "📢 Bu ID ni kanalga joylashtiring!\n"
        "Ishtirokchilar shu ID orqali test topshiradilar.",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )


# ===== MENING TESTLARIM =====

@router.message(F.text == "📊 Mening testlarim")
async def my_tests(message: Message, bot: Bot):
    if not await check_registered(message, bot):
        return
    tests = await db.get_creator_tests(message.from_user.id)
    if not tests:
        await message.answer(
            "📭 Siz hali test yaratmagansiz.\n\n"
            "✍️ Test yaratish tugmasini bosing!",
            reply_markup=main_menu_kb()
        )
        return
    b = InlineKeyboardBuilder()
    for t in tests[:20]:
        status = "🔴" if deadline_over(t["deadline"]) else "🟢"
        dl = t["deadline"] if t["deadline"] else "∞"
        b.button(
            text=status + " " + t["test_code"] + " | " + t["title"][:15] + " | " + dl,
            callback_data="mytest_" + str(t["id"])
        )
    b.adjust(1)
    await message.answer(
        "📋 <b>Mening testlarim</b> (" + str(len(tests)) + " ta)\n\n"
        "🟢 Faol  |  🔴 Yopiq\n\n"
        "Ko'rish uchun tanlang 👇",
        reply_markup=b.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("mytest_"))
async def my_test_menu(callback: CallbackQuery):
    test_id = int(callback.data.split("_")[1])
    tests = await db.get_all_tests()
    test = next((t for t in tests if t["id"] == test_id), None)
    if not test:
        await callback.answer("❌ Test topilmadi!", show_alert=True)
        return
    if callback.from_user.id != test["creator_id"]:
        if not await db.is_admin_db(callback.from_user.id):
            await callback.answer("❌ Bu test sizniki emas!", show_alert=True)
            return

    results = await db.get_test_results(test_id)
    status = "🔴 Yopiq" if deadline_over(test["deadline"]) else "🟢 Faol"
    dl = test["deadline"] or "Yo'q"

    b = InlineKeyboardBuilder()
    b.button(text="🏆 Reyting", callback_data="t_rating_" + str(test_id) + "_0")
    b.button(text="📊 Tahlil", callback_data="t_analysis_" + str(test_id))
    b.button(text="🔍 Batafsil natijalar", callback_data="t_results_" + str(test_id) + "_0")
    b.adjust(2, 1)

    await callback.message.edit_text(
        "📋 <b>" + test["title"] + "</b>\n\n"
        "🆔 ID: <code>" + test["test_code"] + "</code>\n"
        "🔢 Savollar: <b>" + str(test["question_count"]) + "</b> ta\n"
        "⏰ Deadline: " + dl + "\n"
        "📌 Holat: " + status + "\n"
        "👥 Ishtirokchilar: <b>" + str(len(results)) + "</b> ta\n\n"
        "Qaysi bo'limni ko'rmoqchisiz? 👇",
        reply_markup=b.as_markup(),
        parse_mode="HTML"
    )


# ===== REYTING (sahifalash bilan) =====

@router.callback_query(F.data.startswith("t_rating_"))
async def show_rating(callback: CallbackQuery):
    parts = callback.data.split("_")
    test_id = int(parts[2])
    page = int(parts[3]) if len(parts) > 3 else 0
    per_page = 20

    tests = await db.get_all_tests()
    test = next((t for t in tests if t["id"] == test_id), None)
    results = await db.get_test_results(test_id)

    if not results:
        await callback.answer("📭 Hali natijalar yo'q!", show_alert=True)
        return

    total = len(results)
    avg = sum(r["percentage"] for r in results) / total
    start = page * per_page
    end = start + per_page
    page_results = results[start:end]

    text = "🏆 <b>" + test["title"] + " — Reyting</b>\n"
    text += "👥 Jami: <b>" + str(total) + "</b> | 📊 O'rtacha: <b>" + str(round(avg, 1)) + "%</b>\n"
    text += "📄 " + str(start+1) + "-" + str(min(end, total)) + " / " + str(total) + "\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"

    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(page_results, start+1):
        m = medals[i-1] if i <= 3 else str(i) + "."
        filled = int(r["percentage"] / 10)
        bar = "█" * filled + "░" * (10 - filled)
        text += (m + " <b>" + r["first_name"] + " " + r["last_name"] + "</b>\n"
                 "   [" + bar + "] " + str(round(r["percentage"], 1)) + "%\n"
                 "   ✅ " + str(r["correct"]) + "/" + str(r["total"]) + "\n\n")

    b = InlineKeyboardBuilder()
    nav = []
    if page > 0:
        nav.append(("⬅️ Oldingi", "t_rating_" + str(test_id) + "_" + str(page - 1)))
    if end < total:
        nav.append(("Keyingi ➡️", "t_rating_" + str(test_id) + "_" + str(page + 1)))
    for label, cb in nav:
        b.button(text=label, callback_data=cb)
    b.button(text="◀️ Orqaga", callback_data="mytest_" + str(test_id))
    if nav:
        b.adjust(len(nav), 1)
    else:
        b.adjust(1)

    await callback.message.edit_text(text, reply_markup=b.as_markup(), parse_mode="HTML")


# ===== TAHLIL =====

@router.callback_query(F.data.startswith("t_analysis_"))
async def show_analysis(callback: CallbackQuery):
    test_id = int(callback.data.split("_")[2])
    tests = await db.get_all_tests()
    test = next((t for t in tests if t["id"] == test_id), None)
    results = await db.get_test_results(test_id)
    if not results:
        await callback.answer("📭 Hali natijalar yo'q!", show_alert=True)
        return

    total_p = len(results)
    correct_ans = test["answers"]
    q_stats = []
    for qi in range(test["question_count"]):
        dist = Counter()
        ok = 0
        for r in results:
            ua = r["user_answers"]
            given = ua[qi] if qi < len(ua) else "-"
            dist[given] += 1
            if given == correct_ans[qi]:
                ok += 1
        pct = ok / total_p * 100
        q_stats.append({"q": qi+1, "pct": pct, "correct_ans": correct_ans[qi], "dist": dist})

    hardest = sorted(q_stats, key=lambda x: x["pct"])[:5]
    easiest = sorted(q_stats, key=lambda x: x["pct"], reverse=True)[:5]
    avg = sum(r["percentage"] for r in results) / total_p
    above = sum(1 for r in results if r["percentage"] >= 60)

    text = ("📊 <b>" + test["title"] + " — Tahlil</b>\n\n"
            "👥 Ishtirokchilar: <b>" + str(total_p) + "</b>\n"
            "📈 O'rtacha: <b>" + str(round(avg, 1)) + "%</b>\n"
            "✅ 60%+ olganlar: <b>" + str(above) + "</b> ta\n"
            "❌ 60% dan past: <b>" + str(total_p - above) + "</b> ta\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🔴 <b>Eng qiyin savollar:</b>\n\n")
    for s in hardest:
        dist_str = " | ".join(k + ":" + str(v) for k, v in sorted(s["dist"].items()) if k != "-")
        text += ("❓ <b>" + str(s["q"]) + "-savol</b> (to'g'ri: " + s["correct_ans"] + ")\n"
                 "   📊 " + str(round(s["pct"])) + "% to'g'ri | " + dist_str + "\n\n")
    text += "━━━━━━━━━━━━━━━━━━\n🟢 <b>Eng oson savollar:</b>\n\n"
    for s in easiest:
        text += "✅ <b>" + str(s["q"]) + "-savol</b> — " + str(round(s["pct"])) + "% to'g'ri\n"

    b = InlineKeyboardBuilder()
    b.button(text="📈 Barcha savollar tahlili", callback_data="t_allq_" + str(test_id))
    b.button(text="◀️ Orqaga", callback_data="mytest_" + str(test_id))
    b.adjust(1)
    await callback.message.edit_text(text, reply_markup=b.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("t_allq_"))
async def all_questions(callback: CallbackQuery):
    test_id = int(callback.data.split("_")[2])
    tests = await db.get_all_tests()
    test = next((t for t in tests if t["id"] == test_id), None)
    results = await db.get_test_results(test_id)
    if not results:
        await callback.answer("📭 Natijalar yo'q!", show_alert=True)
        return
    total = len(results)
    correct_ans = test["answers"]
    lines = ["<b>Savol | To'g'ri% | Taqsimot</b>\n"]
    for qi in range(test["question_count"]):
        dist = Counter()
        ok = 0
        for r in results:
            ua = r["user_answers"]
            given = ua[qi] if qi < len(ua) else "-"
            dist[given] += 1
            if given == correct_ans[qi]:
                ok += 1
        pct = ok / total * 100
        icon = "🟢" if pct >= 70 else "🟡" if pct >= 40 else "🔴"
        dist_str = " ".join(k + ":" + str(v) for k, v in sorted(dist.items()) if k != "-")
        lines.append(icon + " <b>" + str(qi+1) + ".</b> " + str(round(pct, 1)) + "% | " + dist_str)
    chunks = [lines[i:i+30] for i in range(0, len(lines), 30)]
    await callback.message.answer("\n".join(chunks[0]), parse_mode="HTML")
    for ch in chunks[1:]:
        await callback.message.answer("\n".join(ch), parse_mode="HTML")
    await callback.answer()


# ===== BATAFSIL NATIJALAR (sahifalash bilan) =====

@router.callback_query(F.data.startswith("t_results_"))
async def test_results_list(callback: CallbackQuery):
    parts = callback.data.split("_")
    test_id = int(parts[2])
    page = int(parts[3]) if len(parts) > 3 else 0
    per_page = 15

    results = await db.get_test_results(test_id)
    if not results:
        await callback.answer("📭 Natijalar yo'q!", show_alert=True)
        return

    total = len(results)
    start = page * per_page
    end = start + per_page
    page_results = results[start:end]

    text = ("🔍 <b>Batafsil natijalar</b> (" + str(total) + " ta)\n"
            "📄 " + str(start+1) + "-" + str(min(end, total)) + " / " + str(total) + "\n\n")

    for i, r in enumerate(page_results, start+1):
        emoji = "🏆" if r["percentage"] >= 80 else "✅" if r["percentage"] >= 60 else "📊"
        text += str(i) + ". " + emoji + " " + r["first_name"] + " " + r["last_name"] + " — " + str(round(r["percentage"], 1)) + "%\n"

    b = InlineKeyboardBuilder()
    for r in page_results:
        emoji = "🏆" if r["percentage"] >= 80 else "✅" if r["percentage"] >= 60 else "📊"
        b.button(
            text=emoji + " " + r["first_name"] + " " + r["last_name"] + " (" + str(round(r["percentage"])) + "%)",
            callback_data="rdetail_" + str(r["id"]) + "_" + str(test_id)
        )

    nav = []
    if page > 0:
        nav.append(("⬅️ Oldingi", "t_results_" + str(test_id) + "_" + str(page - 1)))
    if end < total:
        nav.append(("Keyingi ➡️", "t_results_" + str(test_id) + "_" + str(page + 1)))
    for label, cb in nav:
        b.button(text=label, callback_data=cb)
    b.button(text="◀️ Orqaga", callback_data="mytest_" + str(test_id))

    if nav:
        b.adjust(1, len(nav), 1)
    else:
        b.adjust(1)

    await callback.message.edit_text(text, reply_markup=b.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("rdetail_"))
async def result_detail(callback: CallbackQuery):
    parts = callback.data.split("_")
    result_id = int(parts[1])
    test_id = int(parts[2])
    results = await db.get_test_results(test_id)
    result = next((r for r in results if r["id"] == result_id), None)
    if not result:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return
    tests = await db.get_all_tests()
    test = next((t for t in tests if t["id"] == test_id), None)
    ua = result["user_answers"]
    ca = test["answers"]
    lines = []
    for i in range(test["question_count"]):
        u = ua[i] if i < len(ua) else "-"
        c = ca[i]
        if u == c:
            lines.append(str(i+1) + ". ✅ " + u)
        else:
            lines.append(str(i+1) + ". ❌ " + u + " → " + c)
    header = (
        "🔍 <b>" + result["first_name"] + " " + result["last_name"] + "</b>\n"
        "📌 " + test["title"] + " | 🆔 " + test["test_code"] + "\n"
        "✅ To'g'ri: <b>" + str(result["correct"]) + "/" + str(result["total"]) + "</b>"
        " (" + str(round(result["percentage"], 1)) + "%)\n"
        "📅 " + result["taken_at"][:16] + "\n\n"
        "📋 Tahlil (✅ to'g'ri | ❌ xato → to'g'ri):\n\n"
    )
    chunks = [lines[i:i+50] for i in range(0, len(lines), 50)]
    await callback.message.answer(header + "\n".join(chunks[0]), parse_mode="HTML")
    for ch in chunks[1:]:
        await callback.message.answer("\n".join(ch))
    await callback.answer()


# ===== JAVOBNI TEKSHIRISH =====

@router.message(F.text == "✅ Javobni tekshirish")
async def start_solve(message: Message, state: FSMContext, bot: Bot):
    if not await check_registered(message, bot):
        return
    await state.clear()
    await state.set_state(SolveTest.test_code)
    await message.answer(
        "✅ <b>Javobni tekshirish</b>\n\n"
        "🆔 Test kodini yuboring.\n"
        "Masalan: <code>ABC1234</code>",
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
        await message.answer(
            "❌ <b>Bunday test topilmadi!</b>\n"
            "🆔 Kodni tekshirib qayta yuboring.",
            parse_mode="HTML"
        )
        return
    if deadline_over(test["deadline"]):
        await message.answer(
            "⏰ <b>Test muddati tugagan!</b>\n\n"
            "📌 " + test["title"] + "\n"
            "🔴 Deadline: " + str(test["deadline"]),
            parse_mode="HTML"
        )
        return
    dl = "\n⏰ Deadline: <b>" + test["deadline"] + "</b>" if test["deadline"] else ""
    await state.update_data(
        test_code=code,
        test_id=test["id"],
        total=test["question_count"],
        test_title=test["title"],
        test_author=test["creator_name"]
    )
    await state.set_state(SolveTest.answers)
    await message.answer(
        "✅ <b>Test topildi!</b>\n\n"
        "📌 Fan: <b>" + test["title"] + "</b>\n"
        "🔢 Savollar: <b>" + str(test["question_count"]) + "</b> ta\n"
        "👤 Muallif: " + test["creator_name"]
        + dl + "\n\n"
        "✏️ Javoblarni yuboring.\n"
        "📌 Format: <code>ABCDDCBA...</code>\n\n"
        "💡 Kam javob yuborsangiz, qolganlar <b>xato</b> hisoblanadi.",
        reply_markup=back_kb(),
        parse_mode="HTML"
    )


@router.message(StateFilter(SolveTest.answers))
async def get_answers_to_confirm(message: Message, state: FSMContext):
    if message.text in ["🔄 Orqaga", "❌ Bekor qilish"]:
        await state.clear()
        await message.answer("🏠 Bosh sahifa.", reply_markup=main_menu_kb())
        return
    data = await state.get_data()
    user_answers = get_answers(message.text)
    total = data["total"]
    if len(user_answers) == 0:
        await message.answer(
            "❌ <b>Hech qanday javob topilmadi!</b>\n"
            "A, B, C, D, E harflaridan foydalaning.",
            parse_mode="HTML"
        )
        return

    user_ans = list(user_answers[:total])
    while len(user_ans) < total:
        user_ans.append("-")

    missing = total - len(user_answers)
    lines = []
    for i in range(0, len(user_ans), 10):
        chunk = user_ans[i:i+10]
        part = str(i+1) + "-" + str(i+len(chunk)) + ": " + " ".join(chunk)
        lines.append(part)

    warn = ""
    if missing > 0:
        warn = "\n\n⚠️ <b>Diqqat:</b> " + str(missing) + " ta savol javobsiz — xato hisoblanadi!"

    confirm_msg = (
        "📋 <b>Javoblaringiz:</b>\n\n"
        + "\n".join(lines)
        + warn
        + "\n\n❓ <b>Tasdiqlaysizmi?</b>"
    )

    await state.update_data(pending_answers="".join(user_ans))
    await state.set_state(SolveTest.confirm)
    await message.answer(confirm_msg, reply_markup=confirm_answers_kb(), parse_mode="HTML")


@router.message(StateFilter(SolveTest.confirm))
async def do_check_answers(message: Message, state: FSMContext, bot: Bot):
    if message.text == "✏️ Qayta kiritish":
        await state.set_state(SolveTest.answers)
        await message.answer("✏️ Javoblarni qayta yuboring:", reply_markup=back_kb())
        return
    if message.text in ["❌ Bekor qilish", "🔄 Orqaga"]:
        await state.clear()
        await message.answer("🏠 Bosh sahifa.", reply_markup=main_menu_kb())
        return
    if message.text != "✅ Ha, tasdiqlash":
        await message.answer("❗ Tugmalardan birini bosing.")
        return

    data = await state.get_data()
    test = await db.get_test_by_code(data["test_code"])

    if deadline_over(test["deadline"]):
        await state.clear()
        await message.answer("⏰ Test muddati tugadi!", reply_markup=main_menu_kb())
        return

    user_ans = list(data["pending_answers"])
    total = data["total"]
    correct_answers = list(test["answers"])

    correct_count = sum(1 for u, c in zip(user_ans, correct_answers) if u == c)
    pct = (correct_count / total * 100) if total > 0 else 0
    await state.clear()

    user = await db.get_user(message.from_user.id)
    full_name = user["first_name"] + " " + user["last_name"]

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

    wrong = []
    for i, (u, c) in enumerate(zip(user_ans, correct_answers)):
        if u != c:
            shown_u = u if u != "-" else "bo'sh"
            wrong.append(str(i+1) + ": " + shown_u + "→" + c)

    wrong_text = ""
    if wrong:
        wrong_text = "\n\n❌ <b>Xato javoblar:</b>\n" + "  |  ".join(wrong[:10])
        if len(wrong) > 10:
            wrong_text += "\n... va yana " + str(len(wrong) - 10) + " ta xato"

    if pct >= 80:
        emoji = "🏆"
        baho = "A'LO"
    elif pct >= 60:
        emoji = "✅"
        baho = "YAXSHI"
    else:
        emoji = "📊"
        baho = "QONIQARLI"

    caption = (
        emoji + " <b>Natijangiz — " + baho + "</b>\n\n"
        "👤 " + full_name + "\n"
        "📌 Fan: " + data["test_title"] + "\n"
        "✅ To'g'ri: <b>" + str(correct_count) + "/" + str(total) + "</b>\n"
        "📊 Foiz: <b>" + str(round(pct, 1)) + "%</b>\n"
        "👨‍🏫 Muallif: " + data["test_author"]
        + wrong_text
    )

    await message.answer_photo(
        photo=BufferedInputFile(cert_buf.read(), filename="sertifikat.png"),
        caption=caption,
        parse_mode="HTML",
        protect_content=True
    )
