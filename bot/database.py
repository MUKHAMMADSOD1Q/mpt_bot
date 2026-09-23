import datetime
import aiosqlite

from bot.config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                mpt_balance REAL DEFAULT 0,
                subscription_type TEXT,
                subscription_expiry TEXT,
                phone TEXT,
                is_admin_mode INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        # Eski bazalarda ustun bo'lmasligi mumkin - xavfsiz qo'shish
        for column, coltype in [("phone", "TEXT"), ("is_admin_mode", "INTEGER DEFAULT 0")]:
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {column} {coltype}")
            except Exception:
                pass
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                topic TEXT,
                pages INTEGER,
                tariff TEXT,
                price_som REAL,
                price_mpt REAL,
                full_name TEXT,
                institution TEXT,
                direction TEXT,
                language TEXT,
                status TEXT DEFAULT 'kutilmoqda',
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS click_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                merchant_trans_id TEXT UNIQUE,
                amount_som REAL,
                purpose TEXT,
                payload TEXT,
                status TEXT DEFAULT 'kutilmoqda',
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS card_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                amount_som REAL,
                purpose TEXT,
                payload TEXT,
                receipt_file_id TEXT,
                receipt_type TEXT,
                ai_verdict TEXT,
                ai_note TEXT,
                status TEXT DEFAULT 'tekshirilmoqda',
                created_at TEXT
            )
        """)
        await db.commit()


async def get_or_create_user(telegram_id: int, username: str | None) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        if row:
            return dict(row)
        await db.execute(
            "INSERT INTO users (telegram_id, username, mpt_balance, created_at) VALUES (?, ?, 0, ?)",
            (telegram_id, username, datetime.datetime.utcnow().isoformat()),
        )
        await db.commit()
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return dict(row)


async def get_user(telegram_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def add_mpt_balance(telegram_id: int, amount: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET mpt_balance = mpt_balance + ? WHERE telegram_id = ?",
            (amount, telegram_id),
        )
        await db.commit()


async def deduct_mpt_balance(telegram_id: int, amount: float) -> bool:
    user = await get_user(telegram_id)
    if not user or user["mpt_balance"] < amount:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET mpt_balance = mpt_balance - ? WHERE telegram_id = ?",
            (amount, telegram_id),
        )
        await db.commit()
    return True


async def set_subscription(telegram_id: int, sub_type: str, expiry: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET subscription_type = ?, subscription_expiry = ? WHERE telegram_id = ?",
            (sub_type, expiry, telegram_id),
        )
        await db.commit()


async def update_user_phone(telegram_id: int, phone: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET phone = ? WHERE telegram_id = ?", (phone, telegram_id))
        await db.commit()


async def create_order(data: dict) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO orders
               (telegram_id, topic, pages, tariff, price_som, price_mpt,
                full_name, institution, direction, language, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'kutilmoqda', ?)""",
            (
                data["telegram_id"], data["topic"], data["pages"], data["tariff"],
                data["price_som"], data["price_mpt"], data["full_name"],
                data.get("institution"), data.get("direction"), data.get("language"),
                datetime.datetime.utcnow().isoformat(),
            ),
        )
        await db.commit()
        return cur.lastrowid


async def get_order(order_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_order_for_delivery(reference: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if reference.isdigit():
            cur = await db.execute("SELECT * FROM orders WHERE id = ?", (int(reference),))
        else:
            cur = await db.execute(
                "SELECT * FROM orders WHERE topic LIKE ? ORDER BY id DESC LIMIT 1",
                (f"%{reference}%",),
            )
        row = await cur.fetchone()
        return dict(row) if row else None


async def set_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()


async def create_click_payment(telegram_id: int, merchant_trans_id: str, amount_som: float, purpose: str, payload: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO click_payments
               (telegram_id, merchant_trans_id, amount_som, purpose, payload, status, created_at)
               VALUES (?, ?, ?, ?, ?, 'kutilmoqda', ?)""",
            (telegram_id, merchant_trans_id, amount_som, purpose, payload,
             datetime.datetime.utcnow().isoformat()),
        )
        await db.commit()
        return cur.lastrowid


async def get_click_payment(merchant_trans_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM click_payments WHERE merchant_trans_id = ?", (merchant_trans_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def set_click_payment_status(merchant_trans_id: str, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE click_payments SET status = ? WHERE merchant_trans_id = ?",
            (status, merchant_trans_id),
        )
        await db.commit()


async def list_pending_orders() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM orders WHERE status = 'kutilmoqda' ORDER BY id")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def set_admin_mode(telegram_id: int, enabled: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_admin_mode = ? WHERE telegram_id = ?",
            (1 if enabled else 0, telegram_id),
        )
        await db.commit()


async def list_all_users() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users ORDER BY created_at")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_total_paid_revenue() -> dict:
    """Bot orqali qayd etilgan (Click + karta) tasdiqlangan to'lovlar yig'indisi.
    DIQQAT: bu haqiqiy bank/karta balansi EMAS — faqat bot orqali o'tgan va
    tasdiqlangan to'lovlarning yozuvi. Haqiqiy bank balansini faqat bankingiz
    ilovasi/bank API orqali bilib olishingiz mumkin."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT COALESCE(SUM(amount_som), 0) AS total, COUNT(*) AS cnt FROM click_payments WHERE status = 'tolandi'")
        click_row = dict(await cur.fetchone())
        cur = await db.execute("SELECT COALESCE(SUM(amount_som), 0) AS total, COUNT(*) AS cnt FROM card_payments WHERE status = 'tasdiqlandi'")
        card_row = dict(await cur.fetchone())
        return {
            "click_total": click_row["total"], "click_count": click_row["cnt"],
            "card_total": card_row["total"], "card_count": card_row["cnt"],
        }


async def create_card_payment(telegram_id: int, amount_som: float, purpose: str, payload: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO card_payments (telegram_id, amount_som, purpose, payload, status, created_at)
               VALUES (?, ?, ?, ?, 'tekshirilmoqda', ?)""",
            (telegram_id, amount_som, purpose, payload, datetime.datetime.utcnow().isoformat()),
        )
        await db.commit()
        return cur.lastrowid


async def attach_receipt(payment_id: int, file_id: str, file_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE card_payments SET receipt_file_id = ?, receipt_type = ? WHERE id = ?",
            (file_id, file_type, payment_id),
        )
        await db.commit()


async def set_ai_verdict(payment_id: int, verdict: str, note: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE card_payments SET ai_verdict = ?, ai_note = ? WHERE id = ?",
            (verdict, note, payment_id),
        )
        await db.commit()


async def set_card_payment_status(payment_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE card_payments SET status = ? WHERE id = ?", (status, payment_id))
        await db.commit()


async def get_card_payment(payment_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM card_payments WHERE id = ?", (payment_id,))
        row = await cur.fetchone()
        return dict(row) if row else None
