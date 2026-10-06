import asyncio
import html
import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.states import CardPayment
from bot.keyboards import main_menu_kb, card_timeout_kb, card_cancel_kb
from bot.config import (
    CARD_NUMBERS, CARD_OWNER_NAME, PAYMENT_GROUP_ID,
    CARD_PAYMENT_TIMEOUT_SECONDS,
)
from bot.services import ai_verify
from bot.services.payment_common import complete_payment, is_payment_admin
from bot.services.pricing import format_som
from bot.database import (
    create_card_payment, attach_receipt, set_ai_verdict, set_card_payment_status,
    get_card_payment, set_card_payment_group_message, update_user_phone, get_user,
    list_admin_ids,
)

router = Router()
logger = logging.getLogger(__name__)

# payment_id -> asyncio.Task (jarayon xotirasida; bot qayta ishga tushsa taymerlar yo'qoladi - bu normal holat)
_TIMEOUT_TASKS: dict[int, asyncio.Task] = {}


def _normalize_phone(raw: str) -> str | None:
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits.startswith("998") and len(digits) == 12:
        return digits
    if len(digits) == 9:
        return "998" + digits
    return None


def _cards_text() -> str:
    lines = [f"To'lovni <b>{CARD_OWNER_NAME}</b> nomiga quyidagi kartalardan biriga o'tkazing:\n"]
    for bank, numbers in CARD_NUMBERS.items():
        for num in numbers:
            lines.append(f"• {bank}: <code>{num.replace(' ', '')}</code>")
    return "\n".join(lines)


def _admin_review_kb(payment_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"cardapprove:{payment_id}")
    builder.button(text="❌ Rad etish", callback_data=f"cardreject:{payment_id}")
    builder.adjust(2)
    return builder.as_markup()


async def start_card_payment(message: Message, state: FSMContext, purpose: str, amount_som: float, payload: str):
    await state.set_state(CardPayment.waiting_phone)
    await state.update_data(purpose=purpose, amount_som=amount_som, payload=payload)
    await message.answer("Aloqa uchun telefon raqamingizni kiriting (masalan: 998901234567):")


@router.message(CardPayment.waiting_phone)
async def process_card_phone(message: Message, state: FSMContext):
    phone = _normalize_phone(message.text or "")
    if not phone:
        await message.answer("Telefon raqami noto'g'ri formatda. Masalan: 998901234567 shaklida yuboring.")
        return
    telegram_id = message.chat.id
    await update_user_phone(telegram_id, phone)

    data = await state.get_data()
    payment_id = data.get("payment_id") or await create_card_payment(
        telegram_id, data["amount_som"], data["purpose"], data["payload"]
    )
    await state.update_data(payment_id=payment_id)
    await state.set_state(CardPayment.waiting_receipt)

    await message.answer(
        _cards_text() + (
            f"\n\n<b>To'lanadigan summa: {format_som(data['amount_som'])} so'm</b>\n\n"
            "To'lovni amalga oshirgach, to'lov chekini (skrinshot yoki PDF) shu yerga yuboring 👇\n"
            f"<i>Diqqat: to'lov uchun {CARD_PAYMENT_TIMEOUT_SECONDS // 60} daqiqa vaqtingiz bor.</i>"
        ),
        parse_mode="HTML",
        reply_markup=card_cancel_kb(payment_id),
    )

    bot = message.bot
    task = asyncio.create_task(_timeout_watcher(payment_id, telegram_id, bot))
    _TIMEOUT_TASKS[payment_id] = task


async def _timeout_watcher(payment_id: int, chat_id: int, bot: Bot):
    try:
        await asyncio.sleep(CARD_PAYMENT_TIMEOUT_SECONDS)
    except asyncio.CancelledError:
        return
    payment = await get_card_payment(payment_id)
    if payment and payment["status"] == "chek_kutilmoqda":
        await bot.send_message(
            chat_id,
            "⏰ 5 daqiqa o'tdi, hali to'lov cheki yuborilmadi. Davom etasizmi?",
            reply_markup=card_timeout_kb(payment_id),
        )
    _TIMEOUT_TASKS.pop(payment_id, None)


@router.callback_query(F.data.startswith("cardextend:"))
async def extend_timeout(callback: CallbackQuery):
    payment_id = int(callback.data.split(":", 1)[1])
    payment = await get_card_payment(payment_id)
    if not payment or payment["status"] != "chek_kutilmoqda":
        await callback.answer("Bu to'lov endi faol emas.", show_alert=True)
        return
    task = asyncio.create_task(_timeout_watcher(payment_id, payment["telegram_id"], callback.bot))
    _TIMEOUT_TASKS[payment_id] = task
    await callback.message.answer(
        "➕ Yana 5 daqiqa qo'shildi. Chekni shu vaqt ichida yuboring.",
        reply_markup=card_cancel_kb(payment_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cardgiveup:"))
async def give_up_payment(callback: CallbackQuery, state: FSMContext):
    payment_id = int(callback.data.split(":", 1)[1])
    task = _TIMEOUT_TASKS.pop(payment_id, None)
    if task:
        task.cancel()
    await set_card_payment_status(payment_id, "bekor_qilindi")
    await state.clear()
    await callback.message.answer("❌ To'lov bekor qilindi.", reply_markup=main_menu_kb())
    await callback.answer()


@router.message(CardPayment.waiting_receipt, F.photo | F.document)
async def process_receipt(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    telegram_id = message.chat.id
    payment_id = data["payment_id"]

    task = _TIMEOUT_TASKS.pop(payment_id, None)
    if task:
        task.cancel()

    if message.photo:
        file_id = message.photo[-1].file_id
        mime_type = "image/jpeg"
    else:
        file_id = message.document.file_id
        mime_type = message.document.mime_type or "application/octet-stream"

    await attach_receipt(payment_id, file_id, mime_type)
    await message.answer("✅ Chek qabul qilindi, adminlarga yuborilmoqda...", reply_markup=main_menu_kb())
    user = await get_user(telegram_id)
    username = user["username"] if user else "-"
    phone = (user.get("phone") if user else None) or "-"

    caption = (
        f"🧾 Yangi karta to'lovi — №{payment_id}\n"
        f"👤 @{username} (id: {telegram_id})\n"
        f"📞 Telefon: {phone}\n"
        f"Maqsad: {data['purpose']} | Summa: {format_som(data['amount_som'])} so'm\n\n"
        "🤖 AI xulosasi: tekshirilmoqda...\n\n"
        f"Adminlar, iltimos chekni ko'zdan kechirib tasdiqlang yoki rad eting:"
    )
    delivered_to = []
    try:
        if message.photo:
            sent = await bot.send_photo(
                PAYMENT_GROUP_ID, file_id, caption=caption, reply_markup=_admin_review_kb(payment_id)
            )
        else:
            sent = await bot.send_document(
                PAYMENT_GROUP_ID, file_id, caption=caption, reply_markup=_admin_review_kb(payment_id)
            )
        await set_card_payment_group_message(payment_id, sent.message_id)
        delivered_to.append((PAYMENT_GROUP_ID, sent.message_id))
    except Exception:
        logger.exception("Karta chekini to'lov guruhiga yuborib bo'lmadi (chat_id=%s)", PAYMENT_GROUP_ID)
        for admin_id in await list_admin_ids():
            if not admin_id:
                continue
            try:
                if message.photo:
                    sent = await bot.send_photo(
                        admin_id, file_id, caption=caption, reply_markup=_admin_review_kb(payment_id)
                    )
                else:
                    sent = await bot.send_document(
                        admin_id, file_id, caption=caption, reply_markup=_admin_review_kb(payment_id)
                    )
                delivered_to.append((admin_id, sent.message_id))
            except Exception:
                logger.exception("Karta chekini adminga shaxsiy yuborib bo'lmadi (admin_id=%s)", admin_id)

    if delivered_to:
        await message.answer("✅ Chek adminlarga yuborildi, tekshiruv kutilmoqda.", reply_markup=main_menu_kb())
    else:
        await message.answer(
            "⚠️ Chek qabul qilindi, ammo adminlarga yetkazilmadi. Iltimos, admin bilan bog'laning.",
            reply_markup=main_menu_kb(),
        )

    try:
        tg_file = await bot.get_file(file_id)
        file_bytes_io = await bot.download_file(tg_file.file_path)
        verdict = await ai_verify.verify_receipt(file_bytes_io.read(), mime_type, data["amount_som"])
    except Exception as error:
        logger.exception("Chekni AI tekshiruviga tayyorlab bo'lmadi (payment_id=%s)", payment_id)
        verdict = {"verdict": "xatolik", "reason": str(error)}

    ai_label = verdict.get("verdict", "noma'lum")
    ai_reason = str(verdict.get("reason", "-"))[:300]
    await set_ai_verdict(payment_id, ai_label, ai_reason)
    updated_caption = caption.replace(
        "🤖 AI xulosasi: tekshirilmoqda...",
        f"🤖 AI xulosasi: {html.escape(ai_label)} — {html.escape(ai_reason)}",
    )
    for chat_id, group_message_id in delivered_to:
        try:
            await bot.edit_message_caption(
                chat_id=chat_id,
                message_id=group_message_id,
                caption=updated_caption,
                reply_markup=_admin_review_kb(payment_id),
            )
        except Exception:
            logger.exception("AI xulosasini chek xabariga qo'shib bo'lmadi (chat_id=%s)", chat_id)

    await state.clear()


@router.message(CardPayment.waiting_receipt)
async def wrong_receipt_format(message: Message):
    await message.answer("Iltimos, to'lov chekini rasm (screenshot) yoki PDF fayl sifatida yuboring.")


@router.callback_query(F.data.startswith("cardapprove:"))
async def admin_approve(callback: CallbackQuery, bot: Bot):
    if not await is_payment_admin(callback.from_user.id, bot):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    payment_id = int(callback.data.split(":", 1)[1])
    payment = await get_card_payment(payment_id)
    if not payment or payment["status"] != "tekshirilmoqda":
        await callback.answer("Allaqachon ko'rib chiqilgan.", show_alert=True)
        return
    await set_card_payment_status(payment_id, "tasdiqlandi")
    await complete_payment(payment["telegram_id"], payment["purpose"], payment["payload"], bot,
                            payment["amount_som"], paid_via="Karta")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"✅ To'lov №{payment_id} tasdiqlandi — {callback.from_user.full_name} tomonidan.")
    await callback.answer()


@router.callback_query(F.data.startswith("cardreject:"))
async def admin_reject(callback: CallbackQuery, bot: Bot):
    if not await is_payment_admin(callback.from_user.id, bot):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    payment_id = int(callback.data.split(":", 1)[1])
    payment = await get_card_payment(payment_id)
    if not payment or payment["status"] != "tekshirilmoqda":
        await callback.answer("Bu chek allaqachon ko'rib chiqilgan yoki topilmadi.", show_alert=True)
        return
    await set_card_payment_status(payment_id, "rad_etildi")
    try:
        await bot.send_message(payment["telegram_id"], "❌ To'lov chekingiz tasdiqlanmadi. Admin bilan bog'laning.")
    except Exception:
        logger.exception("Chek rad etilgani haqida userga xabar yuborilmadi (payment_id=%s)", payment_id)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"❌ To'lov №{payment_id} rad etildi — {callback.from_user.full_name} tomonidan.")
    await callback.answer()
