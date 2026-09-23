from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.states import CardPayment
from bot.keyboards import main_menu_kb
from bot.config import CARD_NUMBERS, CARD_OWNER_NAME, ADMIN_IDS, PAYMENT_GROUP_ID
from bot.services import ai_verify
from bot.services.payment_common import complete_payment
from bot.services.pricing import format_som
from bot.database import (
    create_card_payment, attach_receipt, set_ai_verdict, set_card_payment_status,
    get_card_payment, update_user_phone,
)

router = Router()


async def _can_review_payment(callback: CallbackQuery, bot: Bot) -> bool:
    """Payment-group moderators may review receipts; private users may not."""
    user_id = callback.from_user.id
    if user_id in ADMIN_IDS:
        return True
    if not callback.message or callback.message.chat.id != PAYMENT_GROUP_ID:
        return False
    member = await bot.get_chat_member(PAYMENT_GROUP_ID, user_id)
    return member.status in {"creator", "administrator"}


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
            lines.append(f"• {bank}: <code>{num}</code>")
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
    await message.answer(
        "KARTA to'lovini yakunlash uchun telefon raqamingizni kiriting "
        "(masalan: 998901234567):"
    )


@router.message(CardPayment.waiting_phone)
async def process_card_phone(message: Message, state: FSMContext):
    phone = _normalize_phone(message.text or "")
    if not phone:
        await message.answer("Telefon raqami noto'g'ri formatda. Masalan: 998901234567 shaklida yuboring.")
        return
    await update_user_phone(message.from_user.id, phone)

    data = await state.get_data()
    await state.set_state(CardPayment.waiting_receipt)
    await message.answer(
        _cards_text() + (
            f"\n\n<b>To'lanadigan summa: {format_som(data['amount_som'])} so'm</b>\n\n"
            "To'lovni amalga oshirgach, to'lov chekini (skrinshot yoki PDF) shu yerga yuboring 👇"
        ),
        parse_mode="HTML",
    )


@router.message(CardPayment.waiting_receipt, F.photo | F.document)
async def process_receipt(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    telegram_id = message.from_user.id

    if message.photo:
        file_id = message.photo[-1].file_id
        mime_type = "image/jpeg"
    else:
        file_id = message.document.file_id
        mime_type = message.document.mime_type or "application/octet-stream"

    payment_id = await create_card_payment(telegram_id, data["amount_som"], data["purpose"], data["payload"])
    await attach_receipt(payment_id, file_id, mime_type)

    await message.answer("✅ Chek qabul qilindi, tekshirilmoqda...")

    tg_file = await bot.get_file(file_id)
    file_bytes_io = await bot.download_file(tg_file.file_path)
    file_bytes = file_bytes_io.read()

    verdict = await ai_verify.verify_receipt(file_bytes, mime_type, data["amount_som"])
    await set_ai_verdict(payment_id, verdict.get("verdict", "noma'lum"), verdict.get("reason", ""))

    auto_ok = (
        verdict.get("available")
        and verdict.get("verdict") == "haqiqiy"
        and verdict.get("looks_like_real_receipt")
        and verdict.get("amount_matches")
    )

    if auto_ok:
        await set_card_payment_status(payment_id, "tasdiqlandi")
        await complete_payment(telegram_id, data["purpose"], data["payload"], bot, data["amount_som"])
        if PAYMENT_GROUP_ID:
            await bot.send_message(
                PAYMENT_GROUP_ID,
                f"✅ To'lov №{payment_id} avtomatik tasdiqlandi.\n"
                f"USER_ID: {telegram_id}\n"
                f"Summa: {format_som(data['amount_som'])} so'm",
            )
        await message.answer("✅ To'lovingiz AI tomonidan avtomatik tasdiqlandi!", reply_markup=main_menu_kb())
    else:
        reason = verdict.get("reason", "—")
        await message.answer(
            "⏳ Chekingiz admin tomonidan qo'lda tekshiriladi (odatda tez orada). "
            "Tasdiqlangach xabar beramiz.",
            reply_markup=main_menu_kb(),
        )
        caption = (
            f"🧾 Yangi chek — to'lov №{payment_id}\n"
            f"Foydalanuvchi: @{message.from_user.username or '-'} (id: {telegram_id})\n"
            f"Maqsad: {data['purpose']} | Summa: {format_som(data['amount_som'])} so'm\n"
            f"AI xulosasi: {verdict.get('verdict', 'nomalum')} — {reason}"
        )
        if PAYMENT_GROUP_ID:
            if message.photo:
                await bot.send_photo(
                    PAYMENT_GROUP_ID, file_id, caption=caption,
                    reply_markup=_admin_review_kb(payment_id),
                )
            else:
                await bot.send_document(
                    PAYMENT_GROUP_ID, file_id, caption=caption,
                    reply_markup=_admin_review_kb(payment_id),
                )

    await state.clear()


@router.message(CardPayment.waiting_receipt)
async def wrong_receipt_format(message: Message):
    await message.answer("Iltimos, to'lov chekini rasm (screenshot) yoki PDF fayl sifatida yuboring.")


@router.callback_query(F.data.startswith("cardapprove:"))
async def admin_approve(callback: CallbackQuery, bot: Bot):
    if not await _can_review_payment(callback, bot):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    payment_id = int(callback.data.split(":", 1)[1])
    payment = await get_card_payment(payment_id)
    if not payment or payment["status"] == "tasdiqlandi":
        await callback.answer("Allaqachon ko'rib chiqilgan.", show_alert=True)
        return
    await set_card_payment_status(payment_id, "tasdiqlandi")
    await complete_payment(payment["telegram_id"], payment["purpose"], payment["payload"], bot, payment["amount_som"])
    await callback.message.answer(f"✅ To'lov №{payment_id} tasdiqlandi.")
    await callback.answer()


@router.callback_query(F.data.startswith("cardreject:"))
async def admin_reject(callback: CallbackQuery, bot: Bot):
    if not await _can_review_payment(callback, bot):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    payment_id = int(callback.data.split(":", 1)[1])
    payment = await get_card_payment(payment_id)
    if not payment:
        await callback.answer("Topilmadi.", show_alert=True)
        return
    await set_card_payment_status(payment_id, "rad_etildi")
    await bot.send_message(payment["telegram_id"], "❌ To'lov chekingiz tasdiqlanmadi. Admin bilan bog'laning.")
    await callback.message.answer(f"❌ To'lov №{payment_id} rad etildi.")
    await callback.answer()
