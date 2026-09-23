import time

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.states import ClickPayment
from bot.keyboards import click_check_kb, main_menu_kb
from bot.services import click_api
from bot.services.payment_common import complete_payment
from bot.database import create_click_payment, get_click_payment, set_click_payment_status, update_user_phone

router = Router()


def _normalize_phone(raw: str) -> str | None:
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits.startswith("998") and len(digits) == 12:
        return digits
    if len(digits) == 9:  # masalan 901234567
        return "998" + digits
    return None


async def start_click_payment(message: Message, state: FSMContext, purpose: str, amount_som: float, payload: str):
    """balance.py / presentation_order.py / payment_method.py shu funksiyani chaqirib,
    Click orqali to'lov jarayonini boshlaydi."""
    await state.set_state(ClickPayment.waiting_phone)
    await state.update_data(purpose=purpose, amount_som=amount_som, payload=payload)
    await message.answer(
        "CLICK to'lov so'rovini yuborish uchun raqamingizni kiriting "
        "(masalan: 998901234567):",
    )


@router.message(ClickPayment.waiting_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = _normalize_phone(message.text or "")
    if not phone:
        await message.answer("Telefon raqami noto'g'ri formatda. Masalan: 998901234567 shaklida yuboring.")
        return

    data = await state.get_data()
    telegram_id = message.from_user.id
    await update_user_phone(telegram_id, phone)
    merchant_trans_id = f"{data['purpose']}-{telegram_id}-{int(time.time())}"

    result = await click_api.create_invoice(data["amount_som"], phone, merchant_trans_id)

    if result.get("error_code") != 0:
        error_note = result.get("error_note", "noma'lum xatolik")
        await message.answer(
            f"⚠️ To'lov so'rovini yaratib bo'lmadi: {error_note}.\n"
            "Iltimos, telefon raqamini tekshirib qayta urinib ko'ring yoki admin bilan bog'laning.",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        return

    await create_click_payment(telegram_id, merchant_trans_id, data["amount_som"], data["purpose"], data["payload"])

    await message.answer(
        f"✅ To'lov so'rovi <b>{phone}</b> raqamiga yuborildi!\n\n"
        "Click ilovangizni (yoki SMS xabarni) oching va to'lovni tasdiqlang. "
        "Tasdiqlagach, pastdagi tugmani bosing:",
        parse_mode="HTML",
        reply_markup=click_check_kb(merchant_trans_id),
    )
    await state.clear()


@router.callback_query(F.data.startswith("clickcheck:"))
async def check_payment(callback: CallbackQuery, bot: Bot):
    merchant_trans_id = callback.data.split(":", 1)[1]
    payment = await get_click_payment(merchant_trans_id)
    if not payment:
        await callback.answer("To'lov topilmadi.", show_alert=True)
        return
    if payment["status"] == "tolandi":
        await callback.answer("Bu to'lov allaqachon tasdiqlangan ✅", show_alert=True)
        return

    status = await click_api.check_payment_status_by_mti(merchant_trans_id)

    if not click_api.is_paid(status):
        await callback.answer(
            "Hali to'lov tasdiqlanmadi. Click ilovasida to'lovni yakunlab, "
            "yana bir bor tekshiring.",
            show_alert=True,
        )
        return

    await set_click_payment_status(merchant_trans_id, "tolandi")
    await complete_payment(payment["telegram_id"], payment["purpose"], payment["payload"], bot, payment["amount_som"])
    await callback.message.answer("✅ To'lovingiz tasdiqlandi, rahmat!", reply_markup=main_menu_kb())
    await callback.answer()
