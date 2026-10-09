import datetime
import logging
import os
import tempfile
import asyncio

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import SUBSCRIPTIONS, PAYMENT_GROUP_ID, FILES_GROUP_ID, TARIFFS, GEMINI_API_KEY
from bot.keyboards import admin_contact_prompt_kb
from bot.services.pricing import format_som
from bot.i18n import tr
from bot.services.user_locale import get_user_locale
from bot.database import (
    add_mpt_balance, set_subscription, set_order_status, get_order, get_user,
    get_service_order, set_service_order_status, set_order_paid_via, is_admin_user,
)

logger = logging.getLogger(__name__)


def _ai_failure_message(error: Exception) -> str:
    from bot.services.ai_content import AIContentError

    if isinstance(error, AIContentError):
        detail = str(error).casefold()
        if "429" in detail or "quota" in detail or "rate limit" in detail:
            return "Gemini API limiti tugagan bo'lishi mumkin. Keyinroq qayta urinib ko'ring."
        if "401" in detail or "403" in detail or "api key" in detail or "api_key" in detail:
            return "Gemini API kaliti noto'g'ri yoki hosting sozlamasida mavjud emas."
        return "Gemini API so'rovida xatolik yuz berdi."
    if isinstance(error, FileNotFoundError) or "shablon" in str(error).casefold():
        return "PowerPoint shabloni topilmadi."
    return "Taqdimotni yaratishda ichki xatolik yuz berdi."


async def _deliver_generated_presentation(bot: Bot, order: dict) -> bool:
    from bot.services.ai_content import generate_presentation_slides
    from bot.services.pptx_generator import (
        build_presentation,
        pick_random_template,
        presentation_filename,
    )

    if order["tariff"] != "bepul":
        raise ValueError("AI orqali hozircha faqat bepul tarifdagi buyurtma tayyorlanadi.")
    template_path = pick_random_template(
        "bepul", allowed_files=("1.pptx", "2.pptx", "3.pptx"),
    )
    if not template_path:
        raise RuntimeError("Taqdimot uchun PowerPoint shablon topilmadi.")

    content_pages = order["pages"] - 2
    if content_pages < 1:
        raise ValueError("Taqdimotda titul va yakuniy sahifadan tashqari matn sahifasi bo'lishi kerak.")
    slides = await generate_presentation_slides(
        order["topic"], content_pages, order.get("language") or "O'zbek",
    )
    language = await get_user_locale(order["telegram_id"])
    output_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as output:
            output_path = output.name
        await asyncio.to_thread(
            build_presentation,
            template_path=template_path,
            output_path=output_path,
            topic=order["topic"],
            full_name=order.get("full_name") or "",
            institution=order.get("institution") or "",
            direction=order.get("direction") or "",
            total_pages=order["pages"],
            slides_content=slides,
        )
        await bot.send_document(
            order["telegram_id"],
            FSInputFile(output_path, filename=presentation_filename(order["topic"])),
            caption=tr(language, "generated_presentation_ready", topic=order["topic"], id=order["id"]),
        )
    finally:
        if output_path and os.path.exists(output_path):
            os.remove(output_path)

    await set_order_status(order["id"], "bajarildi")
    try:
        await bot.send_message(
            FILES_GROUP_ID,
            f"✅ AI taqdimoti foydalanuvchiga yuborildi.\n"
            f"REF:order-{order['id']}\n"
            f"👤 USER_ID: {order['telegram_id']}",
        )
    except Exception:
        logger.exception("AI bilan tayyorlangan taqdimot haqida guruhga xabar yuborilmadi")
    return True


async def is_payment_admin(user_id: int, bot: Bot) -> bool:
    if await is_admin_user(user_id):
        return True
    try:
        member = await bot.get_chat_member(PAYMENT_GROUP_ID, user_id)
        return member.status in {"administrator", "creator"}
    except Exception:
        logger.exception("To'lov guruhi admini huquqini tekshirib bo'lmadi (user_id=%s)", user_id)
        return False


def payment_method_kb(language: str = "uz"):
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(language, "pay_click"), callback_data="paymethod:click")
    builder.button(text=tr(language, "pay_card"), callback_data="paymethod:card")
    builder.button(text=tr(language, "menu_back"), callback_data="nav:back")
    builder.adjust(2)
    return builder.as_markup()


async def ask_payment_method(message: Message, state: FSMContext, purpose: str, amount_som: float, payload: str):
    """Har qanday to'lov (MPT, obuna, buyurtma, xizmat) shu funksiya orqali boshlanadi —
    foydalanuvchi Click yoki Karta orasida tanlaydi."""
    await state.update_data(pm_purpose=purpose, pm_amount_som=amount_som, pm_payload=payload)
    language = await get_user_locale(message.chat.id)
    await message.answer(
        tr(language, "payment_total", amount=format_som(amount_som)),
        parse_mode="HTML",
        reply_markup=payment_method_kb(language),
    )


async def complete_payment(telegram_id: int, purpose: str, payload: str, bot: Bot, amount_som: float = None,
                            paid_via: str = "to'lov"):
    """To'lov turiga (purpose) qarab tegishli amalni bajaradi: MPT qo'shish,
    obuna faollashtirish yoki buyurtma/xizmatni 'to'landi' deb belgilash.
    paid_via: "Click", "Karta" yoki "MPT balansi" — hisobot uchun."""
    user = await get_user(telegram_id)
    language = await get_user_locale(telegram_id)
    username = user["username"] if user else "-"
    phone = (user.get("phone") if user else None) or "-"

    if purpose == "mpt":
        mpt_amount = float(payload)
        await add_mpt_balance(telegram_id, mpt_amount)
        await bot.send_message(telegram_id, tr(language, "mpt_added", amount=mpt_amount))
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
        await bot.send_message(telegram_id, tr(language, "subscription_activated", name=tr(language, f"subscription_{payload}")))
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
            tr(language, "order_payment_delivered", id=order_id),
        )
        if order:
            price_per_page = order["price_som"] / order["pages"] if order["pages"] else 0
            await _post_to_payment_group(bot, (
                f"👤 Ism: {order['full_name']}\n"
                f"👤 Telegramdagi ism: {order.get('telegram_name') or (user.get('telegram_name') if user else '-')}\n"
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
            tr(language, "service_payment_delivered"),
        )
        if service:
            await _post_to_payment_group(bot, (
                f"👤 Telegramdagi ism: {service.get('telegram_name') or (user.get('telegram_name') if user else '-')}\n"
                f"🔗 Username: @{username}\n"
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
    """To'lov tasdiqlangach, taqdimotni AI bilan yuboradi yoki qo'lda tayyorlashga qoldiradi."""
    failure_reason = ""
    if kind == "order":
        order = await get_order(record_id)
        if not order:
            logger.error("Taqdimot buyurtmasi topilmadi: order_id=%s", record_id)
            return
        if order["status"] != "tolandi":
            logger.info(
                "Taqdimot qayta generatsiya qilinmadi: order_id=%s status=%s",
                record_id,
                order["status"],
            )
            return
        if order["tariff"] == "bepul" and GEMINI_API_KEY:
            try:
                await _deliver_generated_presentation(bot, order)
                return
            except Exception as error:
                reason = _ai_failure_message(error)
                failure_reason = f"\n⚠️ AI avtomatik tayyorlay olmadi: {reason}"
                logger.exception("Taqdimotni AI bilan tayyorlash yoki yuborish muvaffaqiyatsiz (order_id=%s)", record_id)
        elif order["tariff"] == "bepul":
            failure_reason = "\n⚠️ GEMINI_API_KEY sozlanmagan — qo'lda tayyorlang."
        else:
            failure_reason = "\nℹ️ AI generatsiyasi hozircha faqat bepul tarifda ishlaydi."
        text = (
            f"🆕 Fayl tayyorlanishi kerak\n"
            f"Buyurtma №{record_id}\n"
            f"REF:order-{record_id}\n"
            f"📝 Mavzu: {order['topic']}\n"
            f"📑 Sahifalar: {order['pages']}\n"
            f"👤 USER_ID: {order['telegram_id']}\n\n"
            f"{failure_reason}\n"
            f"Faylni captioniga /send {record_id} yozib guruhga yuboring yoki ushbu xabarga REPLY qiling."
        )
        if failure_reason and order["tariff"] == "bepul":
            try:
                language = await get_user_locale(order["telegram_id"])
                await bot.send_message(
                    order["telegram_id"],
                    tr(language, "ai_manual_notice"),
                    reply_markup=admin_contact_prompt_kb(language),
                )
            except Exception:
                logger.exception(
                    "AI generatsiyasi bajarilmagani haqida foydalanuvchiga xabar yuborilmadi "
                    "(order_id=%s telegram_id=%s)",
                    record_id,
                    order["telegram_id"],
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
        logger.exception(
            "Fayl tayyorlash xabarini guruhga yuborib bo'lmadi (chat_id=%s record_id=%s)",
            FILES_GROUP_ID,
            record_id,
        )


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
