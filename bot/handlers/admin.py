import asyncio
import datetime
import html
import os
import tempfile

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile

from bot.config import DB_PATH, ADMIN_IDS, PAYMENT_GROUP_ID, SUBSCRIPTIONS, OWNER_ID, SOFF_SELLER_PANEL_URL, TARIFFS
from bot.states import AdminBroadcast, AdminSetPrice
from bot.keyboards import admin_menu_kb, main_menu_kb
from bot.services.pricing import format_som
from bot.services.legacy_import import import_legacy_db, is_sqlite_file
from bot.services.payment_common import subscription_covers, send_payment_request_dm
from bot.database import (
    add_mpt_balance, get_user, set_subscription, set_admin_mode, list_all_users,
    get_total_paid_revenue, get_or_create_user, list_open_orders, list_open_service_orders,
    get_service_order, set_service_order_price,
)

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS or user_id == OWNER_ID


# ==================== REJIM ====================

@router.message(Command("admin"))
async def toggle_admin_mode(message: Message):
    """Adminlar uchun admin rejimini almashtiradi."""
    if not is_admin(message.from_user.id):
        return
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    new_mode = not bool(user.get("is_admin_mode"))
    await set_admin_mode(message.from_user.id, new_mode)
    if new_mode:
        await message.answer("🛠 Admin rejasi yoqildi.", reply_markup=admin_menu_kb())
    else:
        await message.answer("👤 Oddiy foydalanuvchi rejasiga qaytdingiz.", reply_markup=main_menu_kb())


@router.message(F.text == "🔙 Oddiy rejimga qaytish")
async def back_to_user_mode(message: Message):
    if not is_admin(message.from_user.id):
        return
    await set_admin_mode(message.from_user.id, False)
    await message.answer("👤 Oddiy foydalanuvchi rejasiga qaytdingiz.", reply_markup=main_menu_kb())


@router.message(Command("groupid"))
async def cmd_groupid(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    await message.answer(f"Ushbu chat ID: <code>{message.chat.id}</code>", parse_mode="HTML")


@router.message(Command("testpaymentgroup"))
async def test_payment_group(message: Message, bot: Bot):
    if not is_admin(message.from_user.id) or message.chat.type != "private":
        return
    try:
        sent = await bot.send_message(PAYMENT_GROUP_ID, "🔎 Botning to'lovlar guruhi aloqasi tekshirildi.")
    except Exception as error:
        await message.answer(
            f"⚠️ Guruhga xabar yuborilmadi (ID: {PAYMENT_GROUP_ID}): {html.escape(str(error))}"
        )
        return
    await message.answer(
        f"✅ Test xabari yuborildi. Guruh ID: <code>{PAYMENT_GROUP_ID}</code>, "
        f"xabar ID: <code>{sent.message_id}</code>.",
        parse_mode="HTML",
    )


# ==================== ESKI BAZANI IMPORT QILISH ====================

@router.message(Command("importdb"))
async def importdb_help(message: Message):
    if message.from_user.id != OWNER_ID or message.chat.type != "private":
        return
    await message.answer(
        "Eski bazani import qilish uchun <b>DataBase.db</b> faylini shu chatga yuboring va "
        "izoh (caption) qismiga <code>/importdb</code> deb yozing.",
        parse_mode="HTML",
    )


@router.message(F.document, F.caption.startswith("/importdb"))
async def importdb_run(message: Message, bot: Bot):
    if message.from_user.id != OWNER_ID or message.chat.type != "private":
        return
    tmp_path = os.path.join(tempfile.gettempdir(), f"legacy_{message.from_user.id}.db")
    try:
        await bot.download(message.document, destination=tmp_path)
        if not is_sqlite_file(tmp_path):
            await message.answer("⚠️ Bu SQLite bazasi emas. To'g'ri DataBase.db faylini yuboring.")
            return
        await message.answer("⏳ Import boshlandi...")
        report = await asyncio.to_thread(import_legacy_db, tmp_path)
    except Exception as e:
        await message.answer(f"⚠️ Import xatolik bilan tugadi: {e}")
        return
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)  # shaxsiy ma'lumotli faylni serverda qoldirmaymiz

    admins = ", ".join(report["admin_ids"]) or "-"
    await message.answer(
        "✅ Import yakunlandi!\n\n"
        f"Eski bazadagi qatorlar: {report['old_rows']}\n"
        f"Noyob foydalanuvchilar: {report['distinct_users']}\n"
        f"🆕 Yangi qo'shildi: {report['new_users']}\n"
        f"♻️ Avvaldan bor edi: {report['already_existed']}\n"
        f"📞 Haqiqiy telefon raqami bor: {report['with_valid_phone']}\n"
        f"🧾 Eski buyurtmalar tarixi: +{report['legacy_orders_added']}\n"
        f"🛍 Tayyor mahsulotlar: +{report['products_added']}\n\n"
        f"Eski adminlar ID: {admins}\n"
        "<i>(Ularni ADMIN_IDS ga o'zingiz qo'shasiz.)</i>",
        parse_mode="HTML",
    )


@router.message(Command("backupdb"))
async def backup_db(message: Message, bot: Bot):
    """Bazaning zaxira nusxasini faqat egasining shaxsiy chatiga yuboradi.
    Server (Railway Volume) muammo bo'lsa ham ma'lumotlaringiz yo'qolmasligi uchun
    vaqti-vaqti bilan (masalan haftada bir) shu buyruqni bajarib, faylni saqlab qo'ying."""
    if message.from_user.id != OWNER_ID or message.chat.type != "private":
        return
    import sqlite3

    def _snapshot(dest: str):
        src = sqlite3.connect(DB_PATH)
        dst = sqlite3.connect(dest)
        with dst:
            src.backup(dst)  # ishlayotgan bazadan ham xavfsiz nusxa oladi
        src.close()
        dst.close()

    dest = os.path.join(tempfile.gettempdir(), "mpt_bot_backup.db")
    try:
        await asyncio.to_thread(_snapshot, dest)
        stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        await bot.send_document(
            message.chat.id, FSInputFile(dest, filename=f"mpt_bot_backup_{stamp}.db"),
            caption="🗄 Baza zaxira nusxasi. Xavfsiz joyda saqlang — ichida foydalanuvchilar ma'lumotlari bor.",
        )
    except Exception as e:
        await message.answer(f"⚠️ Zaxira nusxa olinmadi: {e}")
    finally:
        if os.path.exists(dest):
            os.remove(dest)


# ==================== STATISTIKA / BUYURTMALAR ====================

@router.message(F.text == "📊 Statistika")
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    users = await list_all_users()
    revenue = await get_total_paid_revenue()
    text = (
        f"👥 Jami foydalanuvchilar: {len(users)}\n\n"
        f"💳 Click orqali to'lovlar: {revenue['click_count']} ta, jami {format_som(revenue['click_total'])} so'm\n"
        f"🏦 Karta orqali to'lovlar: {revenue['card_count']} ta, jami {format_som(revenue['card_total'])} so'm\n\n"
        "<i>Diqqat: bu — bot orqali qayd etilgan va tasdiqlangan to'lovlar yig'indisi, "
        "haqiqiy bank/karta balansi emas. Aniq balansni bank ilovangizdan tekshiring.</i>"
    )
    await message.answer(text, parse_mode="HTML")


def _sub_line(user: dict | None) -> str:
    if user and user.get("subscription_type") and user.get("subscription_expiry"):
        return f"{user['subscription_type']} ({user['subscription_expiry'][:10]} gacha)"
    return "yo'q"


@router.message(F.text == "🧾 Kutayotgan buyurtmalar")
async def admin_pending(message: Message):
    if not is_admin(message.from_user.id):
        return
    orders = await list_open_orders()
    services = await list_open_service_orders()
    if not orders and not services:
        await message.answer("Kutilayotgan buyurtmalar yo'q.")
        return

    chunks = []
    for o in orders:
        user = await get_user(o["telegram_id"])
        nick = f"@{user['username']}" if user and user.get("username") else "yo'q"
        phone = (user.get("phone") if user else None) or "yo'q"
        balance = user["mpt_balance"] if user else 0
        tariff_title = TARIFFS.get(o["tariff"], {}).get("title", o["tariff"])
        if o["status"] == "tolandi":
            state_line = f"✅ To'langan ({o.get('paid_via') or '-'}) — fayl kutilmoqda"
        elif subscription_covers(user, o["tariff"]):
            state_line = "Oylik obuna doirasida (MPT/so'm yechilmaydi)"
        elif balance >= o["price_mpt"]:
            state_line = f"MPT balansidan yechiladi: {o['price_mpt']:.1f} MPT"
        else:
            state_line = f"So'mda to'lov kutilmoqda: {format_som(o['price_som'])} so'm"
        chunks.append(
            f"🎓 Taqdimot №{o['id']}\n"
            f"USER_ID: {o['telegram_id']}\n📞 Raqam: {phone}\n🔗 Nickname: {nick}\n"
            f"📝 Mavzu: {o['topic']}\n📑 Sahifa: {o['pages']}\n📄 Ta'rif: {tariff_title}\n"
            f"💰 Balans: {balance:.1f} MPT | Obuna: {_sub_line(user)}\n"
            f"💳 Shu ish uchun: {o['price_mpt']:.1f} MPT / {format_som(o['price_som'])} so'm\n"
            f"📌 Holat: {state_line}"
        )
    for sv in services:
        user = await get_user(sv["telegram_id"])
        nick = f"@{user['username']}" if user and user.get("username") else "yo'q"
        phone = (user.get("phone") if user else None) or "yo'q"
        price = format_som(sv["price_som"]) + " so'm" if sv["price_som"] else "kelishiladi"
        chunks.append(
            f"🛠 Xizmat №{sv['id']} ({sv['service_type']})\n"
            f"USER_ID: {sv['telegram_id']}\n📞 Raqam: {phone}\n🔗 Nickname: {nick}\n"
            f"📝 Mavzu: {sv['topic']}\n💰 Narx: {price}\n📌 Holat: {sv['status']}"
        )

    buf = ""
    for c in chunks:
        if len(buf) + len(c) > 3800:
            await message.answer(buf)
            buf = ""
        buf += c + "\n\n"
    if buf:
        await message.answer(buf)


@router.message(F.text == "🛍 Soff.uz'ga yuklash")
async def admin_soff_upload(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "Yangi mahsulot yuklash uchun sotuvchi panelingizga o'ting:\n"
        f"{SOFF_SELLER_PANEL_URL}\n\n"
        "<i>Eslatma: yuklashni avtomatlashtirish uchun soff.uz'ning yuklash API'si haqida "
        "ma'lumot kerak — bersangiz, keyingi bosqichda ulab beraman.</i>",
        parse_mode="HTML",
    )


# ==================== XABAR YUBORISH ====================

@router.message(F.text == "👤 Foydalanuvchiga xabar")
async def admin_msg_one_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminBroadcast.waiting_target_id)
    await message.answer("Foydalanuvchining Telegram ID raqamini kiriting:")


@router.message(AdminBroadcast.waiting_target_id)
async def admin_msg_one_get_id(message: Message, state: FSMContext):
    if not (message.text or "").strip().isdigit():
        await message.answer("Iltimos, faqat raqam (Telegram ID) kiriting.")
        return
    await state.update_data(target_id=int(message.text.strip()))
    await state.set_state(AdminBroadcast.waiting_single_message)
    await message.answer("Endi yuboriladigan xabar matnini kiriting:")


@router.message(AdminBroadcast.waiting_single_message)
async def admin_msg_one_send(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    try:
        await bot.send_message(data["target_id"], message.text)
        await message.answer("✅ Xabar yuborildi.", reply_markup=admin_menu_kb())
    except Exception as e:
        await message.answer(f"⚠️ Xabar yuborilmadi: {e}", reply_markup=admin_menu_kb())
    await state.clear()


@router.message(F.text == "📢 Barchaga xabar")
async def admin_broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminBroadcast.waiting_broadcast_message)
    await message.answer("Barcha foydalanuvchilarga yuboriladigan xabar matnini kiriting:")


@router.message(AdminBroadcast.waiting_broadcast_message)
async def admin_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    users = await list_all_users()
    await state.clear()
    await message.answer(f"Yuborish boshlandi ({len(users)} foydalanuvchiga). Bu bir necha daqiqa olishi mumkin...")
    sent, failed = 0, 0
    for user in users:
        try:
            await bot.send_message(user["telegram_id"], message.text)
            sent += 1
        except Exception:
            failed += 1  # botni bloklaganlar va h.k.
        await asyncio.sleep(0.05)  # Telegram flood-limitiga tushmaslik uchun
    await message.answer(f"✅ Yuborildi: {sent} ta, xato: {failed} ta.", reply_markup=admin_menu_kb())


# ==================== NARX BELGILASH (kelishiladigan xizmatlar) ====================

@router.callback_query(F.data.startswith("svc_setprice:"))
async def svc_setprice_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    service_order_id = int(callback.data.split(":", 1)[1])
    await state.set_state(AdminSetPrice.waiting_amount)
    await state.update_data(service_order_id=service_order_id)
    await callback.message.answer(
        f"Xizmat №{service_order_id} uchun kelishilgan narxni so'mda yuboring (faqat raqam):"
    )
    await callback.answer()


@router.message(AdminSetPrice.waiting_amount)
async def svc_setprice_amount(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    raw = (message.text or "").replace(" ", "").replace(".", "").replace(",", "")
    if not raw.isdigit() or int(raw) <= 0:
        await message.answer("Iltimos, narxni faqat raqamlarda yuboring. Masalan: 1500000")
        return
    amount = int(raw)
    data = await state.get_data()
    service = await get_service_order(data["service_order_id"])
    if not service:
        await message.answer("Xizmat topilmadi.")
        await state.clear()
        return
    await set_service_order_price(service["id"], amount)
    await state.clear()
    try:
        await send_payment_request_dm(
            bot, state.storage, service["telegram_id"], "service", amount, str(service["id"]),
            intro=f"💰 “{service['topic']}” buyurtmangiz uchun narx belgilandi: {format_som(amount)} so'm.",
        )
        await message.answer(f"✅ Narx {format_som(amount)} so'm belgilandi, foydalanuvchiga to'lov so'rovi yuborildi.")
    except Exception as e:
        await message.answer(f"⚠️ Foydalanuvchiga yuborib bo'lmadi: {e}")


# ==================== BALANS / OBUNA (qo'lda) ====================

@router.message(Command("addmpt"))
async def cmd_addmpt(message: Message):
    """/addmpt <telegram_id> <miqdor>"""
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Foydalanish: /addmpt <telegram_id> <miqdor>")
        return
    try:
        telegram_id, amount = int(parts[1]), float(parts[2])
    except ValueError:
        await message.answer("Noto'g'ri format. Masalan: /addmpt 123456789 50")
        return
    await add_mpt_balance(telegram_id, amount)
    user = await get_user(telegram_id)
    balance = user["mpt_balance"] if user else amount
    await message.answer(f"✅ {telegram_id} ga {amount} MPT qo'shildi. Yangi balans: {balance:.1f} MPT")


@router.message(Command("addsub"))
async def cmd_addsub(message: Message):
    """/addsub <telegram_id> <tarif_kaliti>"""
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3 or parts[2] not in SUBSCRIPTIONS:
        await message.answer(f"Foydalanish: /addsub <telegram_id> <{', '.join(SUBSCRIPTIONS.keys())}>")
        return
    telegram_id = int(parts[1])
    sub = SUBSCRIPTIONS[parts[2]]
    expiry = (datetime.datetime.utcnow() + datetime.timedelta(days=sub["days"])).isoformat()
    await set_subscription(telegram_id, parts[2], expiry)
    await message.answer(f"✅ {telegram_id} uchun “{sub['title']}” obunasi {expiry[:10]} gacha faollashtirildi.")
