import datetime
import logging

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import ADMIN_IDS, OWNER_ID, SUBSCRIPTIONS, PAYMENT_GROUP_ID, FILES_GROUP_ID, TARIFFS
from bot.services.pricing import format_som
from bot.database import (
    add_mpt_balance, set_subscription, set_order_status, get_order, get_user,
    get_service_order, set_service_order_status, set_order_paid_via,
)

logger = logging.getLogger(__name__)


async def is_payment_admin(user_id: int, bot: Bot) -> bool:
    if user_id in ADMIN_IDS or user_id == OWNER_ID:
        return True
    try:
        member = await bot.get_chat_member(PAYMENT_GROUP_ID, user_id)
        return member.status in {"administrator", "creator"}
    except Exception:
        logger.exception("To'lov guruhi admini huquqini tekshirib bo'lmadi (user_id=%s)", user_id)
        return False


def payment_method_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Click orqali", callback_data="paymethod:click")
    builder.button(text="🏦 Kartaga to'lov", callback_data="paymethod:card")
    builder.adjust(2)
    return builder.as_markup()


async def ask_payment_method(message: Message, state: FSMContext, purpose: str, amount_som: float, payload: str):
    """Har qanday to'lov (MPT, obuna, buyurtma, xizmat) shu funksiya orqali boshlanadi —
    foydalanuvchi Click yoki Karta orasida tanlaydi."""
    await state.update_data(pm_purpose=purpose, pm_amount_som=amount_som, pm_payload=payload)
    await message.answer(
        f"To'lanadigan summa: <b>{format_som(amount_som)} so'm</b>.\n\n"
        "To'lov usulini tanlang:",
        parse_mode="HTML",
        reply_markup=payment_method_kb(),
    )


async def complete_payment(telegram_id: int, purpose: str, payload: str, bot: Bot, amount_som: float = None,
                            paid_via: str = "to'lov"):
    """To'lov turiga (purpose) qarab tegishli amalni bajaradi: MPT qo'shish,
    obuna faollashtirish yoki buyurtma/xizmatni 'to'landi' deb belgilash.
    paid_via: "Click", "Karta" yoki "MPT balansi" — hisobot uchun."""
    user = await get_user(telegram_id)
    username = user["username"] if user else "-"
    phone = (user.get("phone") if user else None) or "-"

    if purpose == "mpt":
        mpt_amount = float(payload)
        await add_mpt_balance(telegram_id, mpt_amount)
        await bot.send_message(telegram_id, f"💰 Balansingizga {mpt_amount:.1f} MPT qo'shildi!")
        await _post_to_payment_group(bot, (
            f"💰 MPT to'ldirish ({paid_via})\n"
            f"👤 @{username} (id: {telegram_id})\n"
            f"Miqdor: {mpt_amount:.1f} MPT ({format_som(amount_som or 0)} so'm)\n\n"
            f"✅ To'lov tasdiqlandi."
        ))

    elif purpose == "sub":
        sub = SUBSCRIPTIONS[payload]
        expiry = (datetime.datetime.utcnow() + datetime.timedelta(days=sub["days"])).isoformat()
        await set_subscription(telegram_id, payload, expiry)
        await bot.send_message(telegram_id, f"📅 “{sub['title']}” obunangiz faollashtirildi!")
        await _post_to_payment_group(bot, (
            f"📅 Obuna sotib olindi ({paid_via})\n"
            f"👤 @{username} (id: {telegram_id})\n"
            f"Tarif: {sub['title']} ({format_som(sub['som'])} so'm)\n\n"
            f"✅ To'lov tasdiqlandi."
        ))

    elif purpose == "order":
        order_id = int(payload)
        await set_order_status(order_id, "tolandi")
        await set_order_paid_via(order_id, paid_via)
        order = await get_order(order_id)
        await bot.send_message(
            telegram_id,
            f"✅ To'lovingiz qabul qilindi! Ish ko'lamiga qarab 1-5 soat ichida tayyor bo'lib, "
            f"adminlar tomonidan sizga yuboriladi. (Buyurtma №{order_id})",
        )
        if order:
            price_per_page = order["price_som"] / order["pages"] if order["pages"] else 0
            await _post_to_payment_group(bot, (
                f"👤 Ism: {order['full_name']}\n"
                f"🔗 Username: @{username}\n"
                f"📞 Telefon raqam: {phone}\n"
                f"📄 Prezentatsiya turi: {TARIFFS.get(order['tariff'], {}).get('title', order['tariff'])}\n"
                f"📝 Prezentatsiya mavzusi: {order['topic']}\n"
                f"📑 Sahifalar soni: {order['pages']}\n"
                f"💵 1 sahifa uchun narx: {format_som(price_per_page)}\n"
                f"💰 Umumiy narx: {format_som(order['price_som'])}\n"
                f"USER_ID: {telegram_id}\n"
                f"To'lov usuli: {paid_via}\n\n"
                f"✅ To'lov tasdiqlandi."
            ))
        await notify_files_group_ready(bot, kind="order", record_id=order_id)

    elif purpose == "service":
        service_order_id = int(payload)
        await set_service_order_status(service_order_id, "tolandi")
        service = await get_service_order(service_order_id)
        await bot.send_message(
            telegram_id,
            f"✅ To'lovingiz qabul qilindi! Ish ko'lamiga qarab 1-5 soat ichida tayyor bo'lib, "
            f"adminlar tomonidan sizga yuboriladi.",
        )
        if service:
            await _post_to_payment_group(bot, (
                f"👤 Ism: @{username}\n"
                f"📞 Telefon raqam: {phone}\n"
                f"📄 Xizmat: {service['service_type']}\n"
                f"📝 Mavzu: {service['topic']}\n"
                f"💰 Narx: {format_som(service['price_som'])}\n"
                f"USER_ID: {telegram_id}\n"
                f"To'lov usuli: {paid_via}\n\n"
                f"✅ To'lov tasdiqlandi."
            ))
        await notify_files_group_ready(bot, kind="service", record_id=service_order_id)


async def notify_files_group_ready(bot: Bot, kind: str, record_id: int):
    """To'lov tasdiqlangach, "Userlar fayllari" guruhiga tayyorlanishi kerak
    bo'lgan ish haqida xabar joylaydi. Admin tayyor faylni shu xabarga REPLY
    qilib yuborsa, bot avtomatik userga yo'naltiradi."""
    if kind == "order":
        order = await get_order(record_id)
        if not order:
            return
        text = (
            f"🆕 Fayl tayyorlanishi kerak\n"
            f"Buyurtma №{record_id}\n"
            f"REF:order-{record_id}\n"
            f"📝 Mavzu: {order['topic']}\n"
            f"📑 Sahifalar: {order['pages']}\n"
            f"👤 USER_ID: {order['telegram_id']}\n\n"
            f"Faylni captioniga /send {record_id} yozib guruhga yuboring yoki ushbu xabarga REPLY qiling."
        )
    else:
        service = await get_service_order(record_id)
        if not service:
            return
        text = (
            f"🆕 Fayl tayyorlanishi kerak\n"
            f"Xizmat №{record_id}\n"
            f"REF:service-{record_id}\n"
            f"📄 Xizmat: {service['service_type']}\n"
            f"📝 Mavzu: {service['topic']}\n"
            f"👤 USER_ID: {service['telegram_id']}\n\n"
            f"Faylni captioniga /send service-{record_id} yozib guruhga yuboring yoki ushbu xabarga REPLY qiling."
        )
    try:
        await bot.send_message(FILES_GROUP_ID, text)
    except Exception:
        pass


async def _post_to_payment_group(bot: Bot, text: str):
    try:
        await bot.send_message(PAYMENT_GROUP_ID, text)
    except Exception:
        logger.exception("To'lov xabarini guruhga yuborib bo'lmadi (chat_id=%s)", PAYMENT_GROUP_ID)


def subscription_covers(user: dict | None, tariff_key: str) -> bool:
    """Foydalanuvchining faol oylik obunasi shu ta'rifni qamrab oladimi?"""
    if not user or not user.get("subscription_type") or not user.get("subscription_expiry"):
        return False
    try:
        expiry = datetime.datetime.fromisoformat(user["subscription_expiry"])
    except ValueError:
        return False
    if expiry < datetime.datetime.utcnow():
        return False
    sub = SUBSCRIPTIONS.get(user["subscription_type"])
    return bool(sub and tariff_key in sub["unlocks"])


async def send_payment_request_dm(bot: Bot, storage, telegram_id: int, purpose: str, amount_som: float, payload: str, intro: str):
    """Admin narx belgilagach, userning shaxsiy chatiga Click/Karta tanlovini yuboradi."""
    from aiogram.fsm.storage.base import StorageKey
    key = StorageKey(bot_id=bot.id, chat_id=telegram_id, user_id=telegram_id)
    user_state = FSMContext(storage=storage, key=key)
    msg = await bot.send_message(telegram_id, intro)
    await ask_payment_method(msg, user_state, purpose=purpose, amount_som=amount_som, payload=payload)
