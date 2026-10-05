"""
Eski bot bazasini (DataBase.db) yangi botga ko'chirish.

Eski baza tuzilishi:
    users(user_id, lang, name, phone_number, order_type, order_name, order_date)
    admins(user_id)
    ready_products(productname, product_url)

Import QAYTA-QAYTA ishga tushirilsa ham xavfsiz (idempotent): mavjud foydalanuvchilar
ustidan yozilmaydi, faqat bo'sh maydonlar (telefon, til, ism) to'ldiriladi.
"""

import sqlite3

from bot.config import DB_PATH

SQLITE_MAGIC = b"SQLite format 3\x00"
_NO_ORDER_VALUES = {"", "false", "none", "null"}


def is_sqlite_file(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(16) == SQLITE_MAGIC
    except OSError:
        return False


def _clean_phone(raw) -> str | None:
    """Faqat haqiqiy raqamlarni qoldiradi. "O'tkazib yuborgan" kabi matnlar -> None."""
    if not raw:
        return None
    digits = "".join(ch for ch in str(raw) if ch.isdigit())
    if digits.startswith("998") and len(digits) == 12:
        return digits
    if len(digits) == 9:
        return "998" + digits
    return None


def import_legacy_db(old_path: str, new_path: str | None = None) -> dict:
    """Sinxron funksiya — botda asyncio.to_thread orqali chaqiring."""
    new_path = new_path or DB_PATH
    old = sqlite3.connect(f"file:{old_path}?mode=ro", uri=True)
    new = sqlite3.connect(new_path)
    report = {
        "old_rows": 0, "distinct_users": 0, "new_users": 0, "already_existed": 0,
        "with_valid_phone": 0, "legacy_orders_added": 0, "products_added": 0, "admin_ids": [],
    }
    try:
        # ---- users ----
        rows = old.execute(
            "SELECT user_id, lang, name, phone_number, order_type, order_name, order_date FROM users"
        ).fetchall()
        report["old_rows"] = len(rows)

        merged: dict[int, dict] = {}
        legacy_orders = []
        for user_id, lang, name, phone, order_type, order_name, order_date in rows:
            try:
                uid = int(str(user_id).strip())
            except (TypeError, ValueError):
                continue
            m = merged.setdefault(uid, {"lang": None, "name": None, "phone": None, "created": None})
            m["lang"] = m["lang"] or (lang or None)
            m["name"] = m["name"] or (name.strip() if isinstance(name, str) and name.strip() else None)
            m["phone"] = m["phone"] or _clean_phone(phone)
            if order_date and (m["created"] is None or str(order_date) < m["created"]):
                m["created"] = str(order_date)
            if order_type and str(order_type).strip().lower() not in _NO_ORDER_VALUES:
                legacy_orders.append((uid, str(order_type), order_name or "", str(order_date or "")))

        report["distinct_users"] = len(merged)
        report["with_valid_phone"] = sum(1 for m in merged.values() if m["phone"])

        existing = {r[0] for r in new.execute("SELECT telegram_id FROM users")}
        for uid, m in merged.items():
            if uid in existing:
                report["already_existed"] += 1
                new.execute(
                    "UPDATE users SET phone = COALESCE(phone, ?), lang = COALESCE(lang, ?), "
                    "full_name = COALESCE(full_name, ?) WHERE telegram_id = ?",
                    (m["phone"], m["lang"], m["name"], uid),
                )
            else:
                new.execute(
                    "INSERT OR IGNORE INTO users (telegram_id, full_name, phone, lang, mpt_balance, created_at) "
                    "VALUES (?, ?, ?, ?, 0, ?)",
                    (uid, m["name"], m["phone"], m["lang"], m["created"]),
                )
                report["new_users"] += 1

        # ---- eski buyurtmalar tarixi ----
        for rec in legacy_orders:
            cur = new.execute(
                "INSERT OR IGNORE INTO legacy_orders (telegram_id, order_type, order_name, order_date) "
                "VALUES (?, ?, ?, ?)", rec,
            )
            report["legacy_orders_added"] += cur.rowcount

        # ---- tayyor mahsulotlar ----
        try:
            for name, url in old.execute("SELECT productname, product_url FROM ready_products"):
                cur = new.execute(
                    "INSERT OR IGNORE INTO ready_products (productname, product_url) VALUES (?, ?)", (name, url)
                )
                report["products_added"] += cur.rowcount
        except sqlite3.Error:
            pass

        # ---- adminlar (faqat hisobot uchun; ADMIN_IDS ni o'zingiz belgilaysiz) ----
        try:
            report["admin_ids"] = [str(r[0]) for r in old.execute("SELECT user_id FROM admins")]
        except sqlite3.Error:
            pass

        new.commit()
    finally:
        old.close()
        new.close()
    return report
