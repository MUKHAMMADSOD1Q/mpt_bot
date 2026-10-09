import asyncio
import datetime
import html
from io import BytesIO
import os
import tempfile

from openpyxl import Workbook
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile

from bot.config import DB_PATH, PAYMENT_GROUP_ID, SUBSCRIPTIONS, OWNER_ID, SOFF_SELLER_PANEL_URL, TARIFFS
from bot.states import AdminBroadcast, AdminSetPrice
from bot.keyboards import admin_menu_kb
from bot.services.pricing import format_som
from bot.services.legacy_import import import_legacy_db, is_sqlite_file
from bot.services.payment_common import subscription_covers, send_payment_request_dm
from bot.i18n import tr
from bot.services.user_locale import get_user_locale
from bot.database import (
    add_mpt_balance, get_user, set_subscription, set_admin_mode, list_all_users,
    count_all_users,
    get_total_paid_revenue, get_or_create_user, list_open_orders, list_open_service_orders,
    get_service_order, set_service_order_price, is_admin_user, list_admin_ids,
    add_admin, remove_admin, list_all_users_with_order_history,
)
from bot.services.user_locale import localized_main_menu

router = Router()


async def is_admin(user_id: int) -> bool:
    return await is_admin_user(user_id)


# ==================== REJIM ====================

@router.message(Command("admin"))
async def toggle_admin_mode(message: Message, state: FSMContext):
    """Adminlar uchun admin rejimini almashtiradi."""
    if not await is_admin(message.from_user.id):
        await message.answer(tr(await get_user_locale(message.from_user.id), "admin_access_denied"))
        return
    await state.clear()
    user = await get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name,
    )
    new_mode = not bool(user.get("is_admin_mode"))
    await set_admin_mode(message.from_user.id, new_mode)
    if new_mode:
        await message.answer(
            "🛠 Admin rejasi yoqildi.",
            reply_markup=admin_menu_kb(super_admin=message.from_user.id == OWNER_ID),
        )
    else:
        await message.answer(
            "👤 Oddiy foydalanuvchi rejasiga qaytdingiz.",
            reply_markup=await localized_main_menu(message.from_user.id),
        )


@router.message(F.text == "🔙 Oddiy rejimga qaytish")
async def back_to_user_mode(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    await set_admin_mode(message.from_user.id, False)
    await message.answer(
        "👤 Oddiy foydalanuvchi rejasiga qaytdingiz.",
        reply_markup=await localized_main_menu(message.from_user.id),
    )


@router.message(Command("groupid"))
async def cmd_groupid(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    await message.answer(f"Ushbu chat ID: <code>{message.chat.id}</code>", parse_mode="HTML")


@router.message(Command("testpaymentgroup"))
async def test_payment_group(message: Message, bot: Bot):
    if not await is_admin(message.from_user.id) or message.chat.type != "private":
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


@router.message(F.text == "👥 Adminlarni boshqarish")
async def show_admin_management(message: Message):
    if message.from_user.id != OWNER_ID or message.chat.type != "private":
        await message.answer("Bu bo'lim faqat superadmin uchun.")
        return
    admins = await list_admin_ids()
    admin_list = "\n".join(f"• <code>{admin_id}</code>" for admin_id in admins) or "Hozircha admin yo'q."
    await message.answer(
        "👥 <b>Adminlarni boshqarish</b>\n\n"
        f"{admin_list}\n\n"
        "Admin tayinlash: <code>/addadmin TELEGRAM_ID</code>\n"
        "Adminlikni bekor qilish: <code>/removeadmin TELEGRAM_ID</code>",
        parse_mode="HTML",
    )


@router.message(Command("addadmin"))
async def cmd_addadmin(message: Message):
    if message.from_user.id != OWNER_ID or message.chat.type != "private":
        await message.answer("Bu amal faqat superadmin uchun.")
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit() or int(parts[1]) <= 0:
        await message.answer("Foydalanish: /addadmin TELEGRAM_ID")
        return
    telegram_id = int(parts[1])
    await add_admin(telegram_id)
    await message.answer(f"✅ <code>{telegram_id}</code> admin sifatida tayinlandi.", parse_mode="HTML")


@router.message(Command("removeadmin"))
async def cmd_removeadmin(message: Message):
    if message.from_user.id != OWNER_ID or message.chat.type != "private":
        await message.answer("Bu amal faqat superadmin uchun.")
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit() or int(parts[1]) <= 0:
        await message.answer("Foydalanish: /removeadmin TELEGRAM_ID")
        return
    telegram_id = int(parts[1])
    if await remove_admin(telegram_id):
        await message.answer(f"✅ <code>{telegram_id}</code> adminlikdan olindi.", parse_mode="HTML")
    elif await is_admin(telegram_id):
        await message.answer("Bu admin .env sozlamasi orqali belgilangan va paneldan olib tashlanmaydi.")
    else:
        await message.answer("Bu Telegram ID tayinlangan adminlar ro'yxatida yo'q.")


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
    if not await is_admin(message.from_user.id):
        return
    user_count = await count_all_users()
    revenue = await get_total_paid_revenue()
    text = (
        f"👥 Jami foydalanuvchilar: {user_count}\n\n"
        f"💳 Click orqali to'lovlar: {revenue['click_count']} ta, jami {format_som(revenue['click_total'])} so'm\n"
        f"🏦 Karta orqali to'lovlar: {revenue['card_count']} ta, jami {format_som(revenue['card_total'])} so'm\n\n"
        "<i>Diqqat: bu — bot orqali qayd etilgan va tasdiqlangan to'lovlar yig'indisi, "
        "haqiqiy bank/karta balansi emas. Aniq balansni bank ilovangizdan tekshiring.</i>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "👥 Foydalanuvchilar ma'lumoti")
async def admin_users_export(message: Message):
    if not await is_admin(message.from_user.id):
        return
    if message.chat.type != "private":
        await message.answer("Foydalanuvchilar ma'lumoti maxfiy. Eksportni adminning shaxsiy chatida oching.")
        return

    users = await list_all_users_with_order_history()
    await message.answer(f"👥 Bazada jami {len(users)} ta foydalanuvchi bor.")
    preview = []
    for user in users:
        preview.append(
            f"🆔 {user['telegram_id']} | "
            f"Ism: {user.get('telegram_name') or '—'} | "
            f"Ism-familiya: {user.get('full_name') or '—'} | "
            f"Username: @{user['username']}" if user.get("username") else
            f"🆔 {user['telegram_id']} | "
            f"Ism: {user.get('telegram_name') or '—'} | "
            f"Ism-familiya: {user.get('full_name') or '—'} | Username: —"
        )
        preview[-1] += (
            f" | Telefon: {user.get('phone') or '—'}"
            f" | Til: {user.get('lang') or '—'}"
            f" | Balans: {user.get('mpt_balance') or 0} MPT"
        )
    if preview:
        chunk = ""
        for line in preview:
            if len(chunk) + len(line) + 1 > 3500:
                await message.answer(chunk)
                chunk = ""
            chunk += line + "\n"
        if chunk:
            await message.answer(chunk)
    else:
        await message.answer("Hozircha bazada foydalanuvchi yo'q.")

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Foydalanuvchilar"
    worksheet.append([
        "Telegram ID", "Telegram ismi", "Ism-familiya", "Username", "Telefon",
        "Til", "MPT balans", "Obuna", "Obuna tugash sanasi", "Admin rejimi",
        "Ro'yxatdan o'tgan", "Buyurtmalar soni", "Buyurtmalar tarixi",
    ])

    for user in users:
        history = user["order_history"]
        history_text = "; ".join(
            f"{item['order_type']}: {item['order_date'] or '-'}" for item in history
        )
        worksheet.append([
            user["telegram_id"],
            _excel_safe_text(user.get("telegram_name")),
            _excel_safe_text(user.get("full_name")),
            _excel_safe_text(f"@{user['username']}" if user.get("username") else ""),
            _excel_safe_text(user.get("phone")),
            _excel_safe_text(user.get("lang")),
            user.get("mpt_balance") or 0,
            _excel_safe_text(user.get("subscription_type")),
            _excel_safe_text(user.get("subscription_expiry")),
            "Ha" if user.get("is_admin_mode") else "Yo'q",
            _excel_safe_text(user.get("created_at")),
            len(history),
            _excel_safe_text(history_text),
        ])

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    for column, width in {
        "A": 16, "B": 28, "C": 28, "D": 22, "E": 20, "F": 14,
        "G": 14, "H": 20, "I": 24, "J": 14, "K": 26, "L": 18,
        "M": 70,
    }.items():
        worksheet.column_dimensions[column].width = width

    output = BytesIO()
    workbook.save(output)
    file = BufferedInputFile(
        output.getvalue(),
        filename=f"foydalanuvchilar_{datetime.datetime.now():%Y%m%d_%H%M}.xlsx",
    )
    await message.answer_document(
        file,
        caption=f"👥 Jami foydalanuvchilar: {len(users)}",
    )


def _excel_safe_text(value: str | None) -> str:
    if value is None:
        return ""
    text = str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def _sub_line(user: dict | None) -> str:
    if user and user.get("subscription_type") and user.get("subscription_expiry"):
        return f"{user['subscription_type']} ({user['subscription_expiry'][:10]} gacha)"
    return "yo'q"


@router.message(F.text == "🧾 Kutayotgan buyurtmalar")
async def admin_pending(message: Message):
    if not await is_admin(message.from_user.id):
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
        full_name = o.get("full_name") or "yo'q"
        telegram_name = o.get("telegram_name") or (user.get("telegram_name") if user else None) or "yo'q"
        institution = o.get("institution") or "O'tkazib yuborgan"
        direction = o.get("direction") or "O'tkazib yuborgan"
        language = o.get("language") or "yo'q"
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
            f"👤 Telegramdagi ism: {telegram_name}\n"
            f"📝 Mavzu: {o['topic']}\n📑 Sahifa: {o['pages']}\n📄 Ta'rif: {tariff_title}\n"
            f"👤 Ism: {full_name}\n"
            f"🏫 Ta'lim muassasasi: {institution}\n"
            f"🎓 Yo'nalish/guruh: {direction}\n"
            f"🌐 Til: {language}\n"
            f"💰 Balans: {balance:.1f} MPT | Obuna: {_sub_line(user)}\n"
            f"💳 Shu ish uchun: {o['price_mpt']:.1f} MPT / {format_som(o['price_som'])} so'm\n"
            f"📌 Holat: {state_line}"
        )
    for sv in services:
        user = await get_user(sv["telegram_id"])
        nick = f"@{user['username']}" if user and user.get("username") else "yo'q"
        phone = (user.get("phone") if user else None) or "yo'q"
        price = format_som(sv["price_som"]) + " so'm" if sv["price_som"] else "kelishiladi"
        summary = sv.get("summary_text") or (
            f"🛠 Xizmat №{sv['id']} ({sv['service_type']})\n"
            f"USER_ID: {sv['telegram_id']}\n📞 Raqam: {phone}\n🔗 Nickname: {nick}\n"
            f"📝 Mavzu: {sv['topic']}"
        )
        chunks.append(
            f"{summary}\n💰 Joriy narx: {price}\n📌 Holat: {sv['status']}"
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
    if not await is_admin(message.from_user.id):
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
    if not await is_admin(message.from_user.id):
        return
    await state.set_state(AdminBroadcast.waiting_target_id)
    await message.answer("Foydalanuvchining Telegram ID raqamini kiriting:")


@router.message(AdminBroadcast.waiting_target_id)
async def admin_msg_one_get_id(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await state.clear()
        return
    if not (message.text or "").strip().isdigit():
        await message.answer("Iltimos, faqat raqam (Telegram ID) kiriting.")
        return
    await state.update_data(target_id=int(message.text.strip()))
    await state.set_state(AdminBroadcast.waiting_single_message)
    await message.answer("Endi yuboriladigan xabar yoki faylni yuboring:")


@router.message(AdminBroadcast.waiting_single_message)
async def admin_msg_one_send(message: Message, state: FSMContext, bot: Bot):
    if not await is_admin(message.from_user.id):
        await state.clear()
        return
    data = await state.get_data()
    try:
        await bot.copy_message(
            chat_id=data["target_id"], from_chat_id=message.chat.id, message_id=message.message_id
        )
        await message.answer(
            "✅ Xabar yuborildi.",
            reply_markup=admin_menu_kb(super_admin=message.from_user.id == OWNER_ID),
        )
    except Exception as e:
        await message.answer(
            f"⚠️ Xabar yuborilmadi: {e}",
            reply_markup=admin_menu_kb(super_admin=message.from_user.id == OWNER_ID),
        )
    await state.clear()


@router.message(F.text == "📢 Barchaga xabar")
async def admin_broadcast_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.set_state(AdminBroadcast.waiting_broadcast_message)
    await message.answer("Barcha foydalanuvchilarga yuboriladigan xabar yoki faylni yuboring:")


@router.message(AdminBroadcast.waiting_broadcast_message)
async def admin_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    if not await is_admin(message.from_user.id):
        await state.clear()
        return
    users = await list_all_users()
    await state.clear()
    await message.answer(f"Yuborish boshlandi ({len(users)} foydalanuvchiga). Bu bir necha daqiqa olishi mumkin...")
    sent, failed = 0, 0
    for user in users:
        try:
            await bot.copy_message(
                chat_id=user["telegram_id"], from_chat_id=message.chat.id, message_id=message.message_id
            )
            sent += 1
        except Exception:
            failed += 1  # botni bloklaganlar va h.k.
        await asyncio.sleep(0.05)  # Telegram flood-limitiga tushmaslik uchun
    await message.answer(
        f"✅ Yuborildi: {sent} ta, xato: {failed} ta.",
        reply_markup=admin_menu_kb(super_admin=message.from_user.id == OWNER_ID),
    )


# ==================== NARX BELGILASH (kelishiladigan xizmatlar) ====================

@router.callback_query(F.data.startswith("svc_setprice:"))
async def svc_setprice_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
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
    if not await is_admin(message.from_user.id):
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
        language = await get_user_locale(service["telegram_id"])
        await send_payment_request_dm(
            bot, state.storage, service["telegram_id"], "service", amount, str(service["id"]),
            intro=tr(language, "service_priced", topic=service["topic"], amount=format_som(amount)),
        )
        await message.answer(f"✅ Narx {format_som(amount)} so'm belgilandi, foydalanuvchiga to'lov so'rovi yuborildi.")
    except Exception as e:
        await message.answer(f"⚠️ Foydalanuvchiga yuborib bo'lmadi: {e}")


# ==================== BALANS / OBUNA (qo'lda) ====================

@router.message(Command("addmpt"))
async def cmd_addmpt(message: Message):
    """/addmpt <telegram_id> <miqdor>"""
    if not await is_admin(message.from_user.id):
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
    if not await is_admin(message.from_user.id):
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
