import asyncio
import datetime

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import SUBSCRIPTIONS, PAYMENT_GROUP_ID
from bot.services.pricing import format_som
from bot.database import (
    add_mpt_balance, set_subscription, set_order_status, get_order, get_user,
)


def payment_method_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 CLICK", callback_data="paymethod:click")
    builder.button(text="🏦 KARTA", callback_data="paymethod:card")
    builder.button(text="⏰ 5 daqiqa ko'paytirish", callback_data="paymethod:extend")
    builder.button(text="❌ Bekor qilish", callback_data="paymethod:cancel")
    builder.adjust(2)
    return builder.as_markup()


async def _payment_timeout_job(message: Message, state: FSMContext, purpose: str, amount_som: float, payload: str):
    await asyncio.sleep(300)
    data = await state.get_data()
    if data.get("pm_purpose") != purpose or data.get("pm_amount_som") != amount_som or data.get("pm_payload") != payload:
        return
    await message.answer(
        "⏰ 5 daqiqa yakunlandi. To'lovni davom ettirish uchun 5 daqiqa qo'shishni yoki bekor qilishni tanlang:",
        reply_markup=payment_method_kb(),
    )


async def ask_payment_method(message: Message, state: FSMContext, purpose: str, amount_som: float, payload: str):
    """Har qanday to'lov (MPT, obuna, buyurtma) shu funksiya orqali boshlanadi —
    foydalanuvchi KARTA yoki CLICK orasida tanlaydi."""
    await state.update_data(pm_purpose=purpose, pm_amount_som=amount_som, pm_payload=payload)
    asyncio.create_task(_payment_timeout_job(message, state, purpose, amount_som, payload))
    await message.answer(
        f"To'lanadigan summa: <b>{format_som(amount_som)} so'm</b>.\n\n"
        "To'lov usulini tanlang: <b>KARTA</b> yoki <b>CLICK</b>.\n\n"
        "Agar 5 daqiqa ichida to'lov qilinmasa yoki chek yuborilmasa, "
        "5 daqiqalik qo'shimcha vaqt yoki bekor qilish taklifi ko'rsatiladi.",
        parse_mode="HTML",
        reply_markup=payment_method_kb(),
    )


async def complete_payment(telegram_id: int, purpose: str, payload: str, bot: Bot, amount_som: float = None):
    """To'lov turiga (purpose) qarab tegishli amalni bajaradi: MPT qo'shish,
    obuna faollashtirish yoki buyurtmani 'to'landi' deb belgilash."""
    user = await get_user(telegram_id)

    if purpose == "mpt":
        mpt_amount = float(payload)
        await add_mpt_balance(telegram_id, mpt_amount)
        await bot.send_message(telegram_id, f"💰 Balansingizga {mpt_amount:.1f} MPT qo'shildi!")
        await _post_to_group(bot, (
            f"💰 MPT to'ldirish\n"
            f"👤 @{user['username'] if user else '-'} (id: {telegram_id})\n"
            f"Miqdor: {mpt_amount:.1f} MPT ({format_som(amount_som or 0)} so'm)\n\n"
            f"✅ Qabul qilindi."
        ))

    elif purpose == "sub":
        sub = SUBSCRIPTIONS[payload]
        expiry = (datetime.datetime.utcnow() + datetime.timedelta(days=sub["days"])).isoformat()
        await set_subscription(telegram_id, payload, expiry)
        await bot.send_message(telegram_id, f"📅 “{sub['title']}” obunangiz faollashtirildi!")
        await _post_to_group(bot, (
            f"📅 Obuna sotib olindi\n"
            f"👤 @{user['username'] if user else '-'} (id: {telegram_id})\n"
            f"Tarif: {sub['title']} ({format_som(sub['som'])} so'm)\n\n"
            f"✅ Qabul qilindi."
        ))

    elif purpose == "order":
        order_id = int(payload)
        await set_order_status(order_id, "tolandi")
        order = await get_order(order_id)
        await bot.send_message(telegram_id, f"✅ To'lovingiz qabul qilindi! №{order_id} buyurtmangiz ishlanmoqda.")
        if order:
            from bot.config import TARIFFS
            price_per_page = order["price_som"] / order["pages"] if order["pages"] else 0
            phone = (user.get("phone") if user else None) or "-"
            username = user["username"] if user else "-"
            await _post_to_group(bot, (
                f"👤 Ism: {order['full_name']}\n"
                f"🔗 Username: @{username}\n"
                f"📞 Telefon raqam: {phone}\n"
                f"📄 Prezentatsiya turi: {TARIFFS.get(order['tariff'], {}).get('title', order['tariff'])}\n"
                f"📝 Prezentatsiya mavzusi: {order['topic']}\n"
                f"📑 Sahifalar soni: {order['pages']}\n"
                f"💵 1 sahifa uchun narx: {format_som(price_per_page)}\n"
                f"💰 Umumiy narx: {format_som(order['price_som'])}\n\n"
                f"✅ Qabul qilindi."
            ))


async def _post_to_group(bot: Bot, text: str):
    if not PAYMENT_GROUP_ID:
        return
    try:
        await bot.send_message(PAYMENT_GROUP_ID, text)
    except Exception:
        pass
