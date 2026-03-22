import aiosqlite
import random
import string
from datetime import datetime
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Foydalanuvchilar
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
        # Testlar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER NOT NULL,
                creator_name TEXT NOT NULL,
                test_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                answers TEXT NOT NULL,
                question_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Test natijalari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                test_id INTEGER NOT NULL,
                correct INTEGER NOT NULL,
                total INTEGER NOT NULL,
                percentage REAL NOT NULL,
                cert_path TEXT,
                taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (test_id) REFERENCES tests(id)
            )
        """)
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


# ============ TESTLAR ============

def generate_test_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))


async def create_test(creator_id, creator_name, title, answers):
    code = generate_test_code()
    async with aiosqlite.connect(DB_PATH) as db:
        # Unique code bo'lgunicha qayta urinish
        while True:
            try:
                await db.execute("""
                    INSERT INTO tests (creator_id, creator_name, test_code, title, answers, question_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (creator_id, creator_name, code, title, answers.upper(), len(answers)))
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


# ============ NATIJALAR ============

async def save_result(user_id, test_id, correct, total, percentage, cert_path):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO results (user_id, test_id, correct, total, percentage, cert_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, test_id, correct, total, percentage, cert_path))
        await db.commit()


async def get_user_results(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT r.*, t.title, t.test_code, t.creator_name
            FROM results r
            JOIN tests t ON r.test_id = t.id
            WHERE r.user_id = ?
            ORDER BY r.taken_at DESC
            LIMIT 20
        """, (user_id,)) as cur:
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
