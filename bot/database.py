import datetime
import aiosqlite

from bot.config import ADMIN_IDS, DB_PATH, OWNER_ID


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                telegram_name TEXT,
                mpt_balance REAL DEFAULT 0,
                subscription_type TEXT,
                subscription_expiry TEXT,
                phone TEXT,
                lang TEXT,
                is_admin_mode INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_admins (
                telegram_id INTEGER PRIMARY KEY,
                created_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ready_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                productname TEXT,
                product_url TEXT UNIQUE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS legacy_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                order_type TEXT,
                order_name TEXT,
                order_date TEXT,
                UNIQUE(telegram_id, order_type, order_name, order_date)
            )
        """)
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
                telegram_name TEXT,
                institution TEXT,
                direction TEXT,
                language TEXT,
                status TEXT DEFAULT 'kutilmoqda',
                group_message_id INTEGER,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS service_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                service_type TEXT,
                topic TEXT,
                summary_text TEXT,
                telegram_name TEXT,
                price_som REAL,
                status TEXT DEFAULT 'kutilmoqda',
                group_message_id INTEGER,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS manual_presentations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                pages INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                institution TEXT,
                direction TEXT,
                language TEXT NOT NULL,
                paragraphs TEXT NOT NULL,
                image_file_ids TEXT NOT NULL DEFAULT '[]',
                template_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'generating',
                document_file_id TEXT,
                created_at TEXT NOT NULL
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
                group_message_id INTEGER,
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
                status TEXT DEFAULT 'chek_kutilmoqda',
                group_message_id INTEGER,
                created_at TEXT
            )
        """)
        # Eski bazalarda ustunlar bo'lmasligi mumkin - xavfsiz qo'shish
        migrations = [
            ("users", "phone", "TEXT"),
            ("users", "is_admin_mode", "INTEGER DEFAULT 0"),
            ("users", "lang", "TEXT"),
            ("users", "telegram_name", "TEXT"),
            ("orders", "paid_via", "TEXT"),
            ("orders", "group_message_id", "INTEGER"),
            ("orders", "telegram_name", "TEXT"),
            ("service_orders", "telegram_name", "TEXT"),
            ("click_payments", "group_message_id", "INTEGER"),
            ("card_payments", "group_message_id", "INTEGER"),
        ]
        for table, column, coltype in migrations:
            try:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
            except Exception:
                pass
        await db.commit()


# ---------------- USERS ----------------

async def get_or_create_user(
    telegram_id: int, username: str | None, telegram_name: str | None = None,
) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        if row:
            await db.execute(
                "UPDATE users SET username = ?, telegram_name = COALESCE(?, telegram_name) "
                "WHERE telegram_id = ?",
                (username, telegram_name, telegram_id),
            )
            await db.commit()
            cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cur.fetchone()
            return dict(row)
        await db.execute(
            "INSERT INTO users (telegram_id, username, telegram_name, mpt_balance, created_at) "
            "VALUES (?, ?, ?, 0, ?)",
            (telegram_id, username, telegram_name, datetime.datetime.utcnow().isoformat()),
        )
        await db.commit()
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return dict(row)


async def update_user_telegram_profile(telegram_id: int, username: str | None, telegram_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (telegram_id, username, telegram_name, mpt_balance, created_at)
               VALUES (?, ?, ?, 0, ?)
               ON CONFLICT(telegram_id) DO UPDATE SET
                   username = excluded.username,
                   telegram_name = excluded.telegram_name""",
            (telegram_id, username, telegram_name, datetime.datetime.utcnow().isoformat()),
        )
        await db.commit()


async def get_user(telegram_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def set_user_language(telegram_id: int, language: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET lang = ? WHERE telegram_id = ?",
            (language, telegram_id),
        )
        await db.commit()


async def create_manual_presentation(data: dict) -> int:
    import json

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO manual_presentations
               (telegram_id, topic, pages, full_name, institution, direction, language,
                paragraphs, image_file_ids, template_name, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'generating', ?)""",
            (
                data["telegram_id"], data["topic"], data["pages"], data["full_name"],
                data.get("institution") or "", data.get("direction") or "", data["language"],
                json.dumps(data["paragraphs"], ensure_ascii=False),
                json.dumps(data["image_file_ids"], ensure_ascii=False),
                data["template_name"], datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
        )
        await db.commit()
        return cur.lastrowid


async def get_manual_presentation(presentation_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM manual_presentations WHERE id = ?", (presentation_id,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def set_manual_presentation_status(
    presentation_id: int,
    expected_status: str,
    status: str,
    document_file_id: str | None = None,
) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """UPDATE manual_presentations
               SET status = ?, document_file_id = COALESCE(?, document_file_id)
               WHERE id = ? AND status = ?""",
            (status, document_file_id, presentation_id, expected_status),
        )
        await db.commit()
        return cur.rowcount == 1


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


async def set_admin_mode(telegram_id: int, enabled: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_admin_mode = ? WHERE telegram_id = ?",
            (1 if enabled else 0, telegram_id),
        )
        await db.commit()


async def is_admin_user(telegram_id: int) -> bool:
    if telegram_id == OWNER_ID or telegram_id in ADMIN_IDS:
        return True
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT 1 FROM bot_admins WHERE telegram_id = ?", (telegram_id,))
        return await cur.fetchone() is not None


async def list_admin_ids() -> list[int]:
    admin_ids = list(dict.fromkeys(ADMIN_IDS + ([OWNER_ID] if OWNER_ID else [])))
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT telegram_id FROM bot_admins ORDER BY telegram_id")
        admin_ids.extend(row[0] for row in await cur.fetchall() if row[0] not in admin_ids)
    return admin_ids


async def add_admin(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO bot_admins (telegram_id, created_at) VALUES (?, ?)",
            (telegram_id, datetime.datetime.now(datetime.timezone.utc).isoformat()),
        )
        await db.commit()


async def remove_admin(telegram_id: int) -> bool:
    if telegram_id == OWNER_ID or telegram_id in ADMIN_IDS:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM bot_admins WHERE telegram_id = ?", (telegram_id,))
        await db.commit()
        return cur.rowcount > 0


async def list_all_users() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users ORDER BY created_at")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def count_all_users() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        row = await cur.fetchone()
        return int(row[0])


async def get_user_order_history(telegram_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT created_at AS order_date, 'Taqdimot' AS order_type
                 FROM orders WHERE telegram_id = ?
               UNION ALL
               SELECT created_at AS order_date, service_type AS order_type
                 FROM service_orders WHERE telegram_id = ?
               UNION ALL
               SELECT order_date, order_type
                 FROM legacy_orders WHERE telegram_id = ?""",
            (telegram_id, telegram_id, telegram_id),
        )
        rows = [dict(row) for row in await cur.fetchall()]
    return sorted(rows, key=lambda row: row["order_date"] or "")


async def list_all_users_with_order_history() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users ORDER BY created_at")
        users = [dict(row) for row in await cur.fetchall()]
        cur = await db.execute(
            """SELECT telegram_id, created_at AS order_date, 'Taqdimot' AS order_type
                 FROM orders
               UNION ALL
               SELECT telegram_id, created_at AS order_date, service_type AS order_type
                 FROM service_orders
               UNION ALL
               SELECT telegram_id, order_date, order_type
                 FROM legacy_orders"""
        )
        orders_by_user: dict[int, list[dict]] = {}
        for row in await cur.fetchall():
            if row["telegram_id"] is not None:
                orders_by_user.setdefault(row["telegram_id"], []).append({
                    "order_date": row["order_date"],
                    "order_type": row["order_type"],
                })

    for user in users:
        history = orders_by_user.get(user["telegram_id"], [])
        user["order_history"] = sorted(history, key=lambda row: row["order_date"] or "")
    return users


# ---------------- PRESENTATION ORDERS ----------------

async def create_order(data: dict) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO orders
               (telegram_id, topic, pages, tariff, price_som, price_mpt,
                full_name, telegram_name, institution, direction, language, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'kutilmoqda', ?)""",
            (
                data["telegram_id"], data["topic"], data["pages"], data["tariff"],
                data["price_som"], data["price_mpt"], data["full_name"], data.get("telegram_name"),
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


async def set_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()


async def set_order_group_message(order_id: int, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET group_message_id = ? WHERE id = ?", (message_id, order_id))
        await db.commit()


async def list_pending_orders() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM orders WHERE status = 'kutilmoqda' ORDER BY id")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ---------------- SERVICE ORDERS (mustaqil ish, taklifnoma, logo, va h.k.) ----------------

async def create_service_order(
    telegram_id: int,
    service_type: str,
    topic: str,
    summary_text: str,
    price_som: float,
    telegram_name: str | None = None,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO service_orders
               (telegram_id, service_type, topic, summary_text, telegram_name, price_som, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'kutilmoqda', ?)""",
            (
                telegram_id, service_type, topic, summary_text, telegram_name,
                price_som, datetime.datetime.utcnow().isoformat(),
            ),
        )
        await db.commit()
        return cur.lastrowid


async def get_service_order(service_order_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM service_orders WHERE id = ?", (service_order_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def set_service_order_status(service_order_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE service_orders SET status = ? WHERE id = ?", (status, service_order_id))
        await db.commit()


async def set_service_order_group_message(service_order_id: int, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE service_orders SET group_message_id = ? WHERE id = ?", (message_id, service_order_id))
        await db.commit()


async def list_pending_files() -> list[dict]:
    """Fayl kutilayotgan (to'lov qilingan, lekin hali fayl yuborilmagan) barcha
    buyurtmalar — ham taqdimotlar (orders), ham xizmatlar (service_orders)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        result = []
        cur = await db.execute("SELECT * FROM orders WHERE status = 'tolandi'")
        for r in await cur.fetchall():
            d = dict(r)
            d["kind"] = "order"
            result.append(d)
        cur = await db.execute("SELECT * FROM service_orders WHERE status = 'tolandi'")
        for r in await cur.fetchall():
            d = dict(r)
            d["kind"] = "service"
            result.append(d)
        return result


# ---------------- CLICK TO'LOVLARI ----------------

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


async def set_click_payment_group_message(merchant_trans_id: str, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE click_payments SET group_message_id = ? WHERE merchant_trans_id = ?",
            (message_id, merchant_trans_id),
        )
        await db.commit()


# ---------------- KARTA TO'LOVLARI ----------------

async def create_card_payment(telegram_id: int, amount_som: float, purpose: str, payload: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO card_payments (telegram_id, amount_som, purpose, payload, status, created_at)
               VALUES (?, ?, ?, ?, 'chek_kutilmoqda', ?)""",
            (telegram_id, amount_som, purpose, payload, datetime.datetime.utcnow().isoformat()),
        )
        await db.commit()
        return cur.lastrowid


async def attach_receipt(payment_id: int, file_id: str, file_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE card_payments SET receipt_file_id = ?, receipt_type = ?, status = 'tekshirilmoqda' WHERE id = ?",
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


async def set_card_payment_group_message(payment_id: int, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE card_payments SET group_message_id = ? WHERE id = ?", (message_id, payment_id))
        await db.commit()


async def get_card_payment(payment_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM card_payments WHERE id = ?", (payment_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


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


# ---------------- TAYYOR MAHSULOTLAR (eski bazadan / zaxira ro'yxat) ----------------

async def list_ready_products() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT productname, product_url FROM ready_products ORDER BY id")
        return [dict(r) for r in await cur.fetchall()]


async def set_order_paid_via(order_id: int, paid_via: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET paid_via = ? WHERE id = ?", (paid_via, order_id))
        await db.commit()


async def set_service_order_price(service_order_id: int, price_som: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE service_orders SET price_som = ? WHERE id = ?", (price_som, service_order_id))
        await db.commit()


async def list_open_orders() -> list[dict]:
    """Admin uchun: to'lov kutilayotgan yoki to'langan-u fayl yuborilmagan taqdimot buyurtmalari."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM orders WHERE status IN ('kutilmoqda', 'tolandi') ORDER BY id")
        return [dict(r) for r in await cur.fetchall()]


async def list_open_service_orders() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM service_orders WHERE status IN ('kutilmoqda', 'tolandi') ORDER BY id")
        return [dict(r) for r in await cur.fetchall()]
