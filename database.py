import aiosqlite
import random
import string
from datetime import datetime
from config import DB_PATH, REQUIRED_CHANNELS
 
 
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                cert_design INTEGER DEFAULT 1,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER NOT NULL,
                creator_name TEXT NOT NULL,
                test_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                answers TEXT NOT NULL,
                question_count INTEGER NOT NULL,
                deadline TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                test_id INTEGER NOT NULL,
                correct INTEGER NOT NULL,
                total INTEGER NOT NULL,
                percentage REAL NOT NULL,
                user_answers TEXT NOT NULL DEFAULT '',
                cert_path TEXT,
                taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT NOT NULL,
                url TEXT NOT NULL,
                ch_type TEXT NOT NULL DEFAULT 'required',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY,
                full_name TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
 
        # ===== MIGRATION: eski DB ga yangi ustunlar qo'shish =====
        try:
            await db.execute("ALTER TABLE tests ADD COLUMN deadline TEXT DEFAULT NULL")
            await db.commit()
        except Exception:
            pass  # Ustun allaqachon mavjud
 
        try:
            await db.execute("ALTER TABLE results ADD COLUMN user_answers TEXT DEFAULT ''")
            await db.commit()
        except Exception:
            pass  # Ustun allaqachon mavjud
        # ===== MIGRATION END =====
 
        # Config kanallarini import
        async with db.execute("SELECT COUNT(*) FROM channels WHERE ch_type='required'") as cur:
            count = (await cur.fetchone())[0]
        if count == 0 and REQUIRED_CHANNELS:
            for ch in REQUIRED_CHANNELS:
                await db.execute(
                    "INSERT INTO channels (name, username, url, ch_type) VALUES (?, ?, ?, ?)",
                    (ch["name"], ch["username"], ch["url"], "required")
                )
            await db.commit()
 
 
# ============ FOYDALANUVCHILAR ============
 
async def register_user(tg_id, first_name, last_name, phone):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users (id, first_name, last_name, phone)
            VALUES (?, ?, ?, ?)
        """, (tg_id, first_name, last_name, phone))
        await db.commit()
 
 
async def get_user(tg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id = ?", (tg_id,)) as cur:
            return await cur.fetchone()
 
 
async def update_user_name(tg_id, first_name, last_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET first_name=?, last_name=? WHERE id=?",
            (first_name, last_name, tg_id)
        )
        await db.commit()
 
 
async def update_cert_design(tg_id, design):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET cert_design=? WHERE id=?",
            (design, tg_id)
        )
        await db.commit()
 
 
async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY registered_at DESC") as cur:
            return await cur.fetchall()
 
 
# ============ TESTLAR ============
 
def generate_test_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
 
 
async def create_test(creator_id, creator_name, title, answers, deadline=None):
    code = generate_test_code()
    async with aiosqlite.connect(DB_PATH) as db:
        while True:
            try:
                await db.execute("""
                    INSERT INTO tests
                    (creator_id, creator_name, test_code, title, answers, question_count, deadline)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (creator_id, creator_name, code, title,
                      answers.upper(), len(answers), deadline))
                await db.commit()
                return code
            except Exception:
                code = generate_test_code()
 
 
async def get_test_by_code(code):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tests WHERE test_code = ?", (code.upper(),)
        ) as cur:
            return await cur.fetchone()
 
 
async def get_all_tests():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tests ORDER BY created_at DESC") as cur:
            return await cur.fetchall()
 
 
async def get_creator_tests(creator_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tests WHERE creator_id = ? ORDER BY created_at DESC",
            (creator_id,)
        ) as cur:
            return await cur.fetchall()
 
 
# ============ NATIJALAR ============
 
async def save_result(user_id, test_id, correct, total, percentage, user_answers, cert_path=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO results (user_id, test_id, correct, total, percentage, user_answers, cert_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, test_id, correct, total, percentage, user_answers, cert_path))
        await db.commit()
 
 
async def get_user_results(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT r.*, t.title, t.test_code, t.creator_name
            FROM results r
            JOIN tests t ON r.test_id = t.id
            WHERE r.user_id = ?
            ORDER BY r.taken_at DESC LIMIT 20
        """, (user_id,)) as cur:
            return await cur.fetchall()
 
 
async def get_test_results(test_id):
    """Test bo'yicha barcha ishtirokchilar natijalari"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT r.*, u.first_name, u.last_name, u.phone
            FROM results r
            JOIN users u ON r.user_id = u.id
            WHERE r.test_id = ?
            ORDER BY r.percentage DESC, r.taken_at ASC
        """, (test_id,)) as cur:
            return await cur.fetchall()
 
 
async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            users = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM tests") as c:
            tests = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM results") as c:
            results = (await c.fetchone())[0]
    return users, tests, results
 
 
# ============ KANALLAR ============
 
async def get_channels(ch_type="required"):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM channels WHERE ch_type = ? ORDER BY id", (ch_type,)
        ) as cur:
            return await cur.fetchall()
 
 
async def add_channel(name, username, url, ch_type="required"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO channels (name, username, url, ch_type) VALUES (?, ?, ?, ?)",
            (name, username, url, ch_type)
        )
        await db.commit()
 
 
async def delete_channel(ch_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE id = ?", (ch_id,))
        await db.commit()
 
 
# ============ ADMINLAR ============
 
async def get_admins():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM admins ORDER BY added_at") as cur:
            return await cur.fetchall()
 
 
async def add_admin(user_id, full_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO admins (id, full_name) VALUES (?, ?)",
            (user_id, full_name)
        )
        await db.commit()
 
 
async def remove_admin(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admins WHERE id = ?", (user_id,))
        await db.commit()
 
 
async def is_admin_db(user_id):
    from config import ADMIN_IDS
    if user_id in ADMIN_IDS:
        return True
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM admins WHERE id = ?", (user_id,)
        ) as cur:
            return await cur.fetchone() is not None
 
