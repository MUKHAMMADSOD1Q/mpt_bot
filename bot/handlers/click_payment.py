import random
import logging
import time

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import PAYMENT_GROUP_ID
from bot.database import (
    create_click_payment, get_click_payment, get_user, set_click_payment_group_message,
    set_click_payment_status, update_user_phone,
    list_admin_ids,
)
from bot.keyboards import (
    click_app_choice_kb, click_game_answers_kb, click_game_done_kb, click_phone_kb, click_wait_kb,
    main_menu_kb,
)
from bot.services import click_api
from bot.services.payment_common import complete_payment, is_payment_admin
from bot.states import ClickPayment
from bot.i18n import tr
from bot.services.user_locale import get_user_locale

router = Router()
logger = logging.getLogger(__name__)


def _normalize_phone(raw: str) -> str | None:
    digits = "".join(char for char in raw if char.isdigit())
    if digits.startswith("998") and len(digits) == 12:
        return digits
    if len(digits) == 9:
        return "998" + digits
    return None


def _click_review_kb(merchant_trans_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"clickapprove:{merchant_trans_id}")
    builder.button(text="❌ Rad etish", callback_data=f"clickreject:{merchant_trans_id}")
    builder.adjust(2)
    return builder.as_markup()


async def _notify_click_payment_group(merchant_trans_id: str, channel: str, bot: Bot):
    payment = await get_click_payment(merchant_trans_id)
    if not payment:
        return
    user = await get_user(payment["telegram_id"])
    username = f"@{user['username']}" if user and user.get("username") else "-"
    text = (
        f"💳 Yangi Click to'lovi — {channel}\n"
        f"👤 Foydalanuvchi: {username} (ID: {payment['telegram_id']})\n"
        f"💰 Summa: {payment['amount_som']:,.0f} so'm\n"
        f"🧾 Maqsad: {payment['purpose']}\n"
        f"🔖 Transaction: <code>{merchant_trans_id}</code>\n\n"
        "Admin to'lov tushganini tekshirib, tasdiqlashi yoki rad etishi mumkin."
    )
    try:
        sent = await bot.send_message(
            PAYMENT_GROUP_ID, text, reply_markup=_click_review_kb(merchant_trans_id)
        )
        await set_click_payment_group_message(merchant_trans_id, sent.message_id)
    except Exception:
        logger.exception(
            "Click to'lovini guruhga yuborib bo'lmadi (chat_id=%s, mti=%s)",
            PAYMENT_GROUP_ID, merchant_trans_id,
        )
        for admin_id in await list_admin_ids():
            if not admin_id:
                continue
            try:
                await bot.send_message(
                    admin_id,
                    f"⚠️ To'lovlar guruhiga yuborilmadi. Shaxsiy zaxira xabar.\n\n{text}",
                    reply_markup=_click_review_kb(merchant_trans_id),
                )
            except Exception:
                logger.exception(
                    "Click to'lovini adminga yuborib bo'lmadi (admin_id=%s, mti=%s)",
                    admin_id, merchant_trans_id,
                )


async def start_click_payment(message: Message, state: FSMContext, purpose: str, amount_som: float, payload: str):
    telegram_id = message.chat.id
    language = await get_user_locale(telegram_id)
    merchant_trans_id = f"{purpose}-{telegram_id}-{int(time.time())}"
    await create_click_payment(telegram_id, merchant_trans_id, amount_som, purpose, payload)
    await state.update_data(click_merchant_trans_id=merchant_trans_id)
    await state.set_state(ClickPayment.waiting_app_choice)
    await message.answer(
        tr(language, "click_intro"),
        reply_markup=click_app_choice_kb(language),
    )


async def _send_checkout(message: Message, state: FSMContext, merchant_trans_id: str, intro: str):
    payment = await get_click_payment(merchant_trans_id)
    pay_url = click_api.build_checkout_url(payment["amount_som"], merchant_trans_id)
    await _notify_click_payment_group(merchant_trans_id, "havola", message.bot)
    language = await get_user_locale(message.chat.id)
    await message.answer(intro, reply_markup=click_wait_kb(merchant_trans_id, pay_url, language))
    await state.clear()


async def _send_invoice(message: Message, state: FSMContext, merchant_trans_id: str, phone: str):
    payment = await get_click_payment(merchant_trans_id)
    try:
        response = await click_api.create_invoice(payment["amount_som"], phone, merchant_trans_id)
    except Exception:
        response = {}

    if response.get("error_code") == 0:
        language = await get_user_locale(payment["telegram_id"])
        await update_user_phone(payment["telegram_id"], phone)
        await _notify_click_payment_group(merchant_trans_id, "ClickSuperApp invoice", message.bot)
        await message.answer(
            tr(language, "click_invoice_sent"),
            reply_markup=click_wait_kb(merchant_trans_id, language=language),
        )
        await state.clear()
        return

    language = await get_user_locale(payment["telegram_id"])
    await message.answer(tr(language, "click_invoice_failed"))
    await _send_checkout(message, state, merchant_trans_id, tr(language, "payment_link"))


@router.callback_query(ClickPayment.waiting_app_choice, F.data == "clickapp:yes")
async def click_app_available(callback: CallbackQuery, state: FSMContext):
    language = await get_user_locale(callback.from_user.id)
    await callback.answer()
    await state.set_state(ClickPayment.waiting_phone)
    await callback.message.answer(
        tr(language, "click_phone_prompt"),
        reply_markup=click_phone_kb(language),
    )


@router.callback_query(ClickPayment.waiting_app_choice, F.data == "clickapp:no")
async def click_app_unavailable(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = await get_user_locale(callback.from_user.id)
    await callback.answer()
    await _send_checkout(
        callback.message, state, data["click_merchant_trans_id"],
        tr(language, "click_checkout_intro"),
    )


@router.message(ClickPayment.waiting_phone)
async def click_phone_received(message: Message, state: FSMContext):
    language = await get_user_locale(message.from_user.id)
    if message.contact:
        if message.contact.user_id != message.from_user.id:
            await message.answer(tr(language, "share_own_phone"))
            return
        raw_phone = message.contact.phone_number
    else:
        raw_phone = message.text or ""
    phone = _normalize_phone(raw_phone)
    if not phone:
        await message.answer(tr(language, "phone_invalid"))
        return
    data = await state.get_data()
    await message.answer(tr(language, "phone_received"), reply_markup=ReplyKeyboardRemove())
    await _send_invoice(message, state, data["click_merchant_trans_id"], phone)


def _new_math_question(progress: int) -> tuple[str, int, list[int]]:
    if progress < 3:
        left, right = random.randint(1, 10), random.randint(1, 10)
        operation = random.choice(("+", "-"))
    elif progress < 7:
        left, right = random.randint(10, 50), random.randint(2, 10)
        operation = random.choice(("+", "-", "×"))
    else:
        operation = random.choice(("+", "-", "×", "÷"))
        if operation == "÷":
            right = random.randint(2, 12)
            left = right * random.randint(2, 12)
        else:
            left, right = random.randint(12, 100), random.randint(2, 12)

    if operation == "-" and right > left:
        left, right = right, left
    answer = {"+": left + right, "-": left - right, "×": left * right}.get(operation)
    if operation == "÷":
        answer = left // right
    options = {answer}
    while len(options) < 4:
        options.add(max(0, answer + random.randint(-10, 10)))
    return f"{left} {operation} {right} = ?", answer, random.sample(list(options), 4)


async def _show_math_question(message: Message, state: FSMContext, progress: int):
    question, answer, options = _new_math_question(progress)
    await state.update_data(game_answer=answer)
    language = await get_user_locale(message.chat.id)
    text = tr(language, "math_question", number=progress + 1, question=question)
    markup = click_game_answers_kb(options, language)
    question_prefix = tr(language, "math_question", number="", question="").splitlines()[0].split("/", 1)[0]
    if message.text and message.text.startswith(question_prefix):
        await message.edit_text(text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("clickgame:start:"))
async def click_game_start(callback: CallbackQuery, state: FSMContext):
    language = await get_user_locale(callback.from_user.id)
    merchant_trans_id = callback.data.rsplit(":", 1)[1]
    payment = await get_click_payment(merchant_trans_id)
    if not payment or payment["telegram_id"] != callback.from_user.id:
        await callback.answer(tr(language, "payment_not_found"), show_alert=True)
        return
    if payment["status"] == "tolandi":
        await callback.answer(tr(language, "payment_already_approved"), show_alert=True)
        return
    await state.update_data(game_merchant_trans_id=merchant_trans_id, game_progress=0)
    await state.set_state(ClickPayment.playing_game)
    await callback.answer()
    await _show_math_question(callback.message, state, 0)


@router.callback_query(ClickPayment.playing_game, F.data.startswith("clickgame:answer:"))
async def click_game_answer(callback: CallbackQuery, state: FSMContext):
    language = await get_user_locale(callback.from_user.id)
    data = await state.get_data()
    try:
        selected = int(callback.data.rsplit(":", 1)[1])
    except ValueError:
        await callback.answer(tr(language, "answer_invalid"), show_alert=True)
        return
    if selected != data.get("game_answer"):
        await callback.answer(tr(language, "answer_wrong"))
        await _show_math_question(callback.message, state, data["game_progress"])
        return

    progress = data["game_progress"] + 1
    await callback.answer(tr(language, "answer_correct") if progress < 10 else tr(language, "game_complete"))
    if progress == 10:
        merchant_trans_id = data["game_merchant_trans_id"]
        await state.clear()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            tr(language, "game_done"),
            reply_markup=click_game_done_kb(merchant_trans_id, language),
        )
        return
    await state.update_data(game_progress=progress)
    await _show_math_question(callback.message, state, progress)


@router.callback_query(F.data.startswith("clickcheck:"))
async def check_payment(callback: CallbackQuery, bot: Bot, state: FSMContext):
    language = await get_user_locale(callback.from_user.id)
    merchant_trans_id = callback.data.split(":", 1)[1]
    payment = await get_click_payment(merchant_trans_id)
    if not payment or payment["telegram_id"] != callback.from_user.id:
        await callback.answer(tr(language, "payment_not_found"), show_alert=True)
        return
    if payment["status"] == "tolandi":
        await callback.answer(tr(language, "payment_already_approved"), show_alert=True)
        return
    if payment["status"] == "rad_etildi":
        await callback.answer(tr(language, "payment_rejected"), show_alert=True)
        return

    status = await click_api.check_payment_status_by_mti(merchant_trans_id)
    if not click_api.is_paid(status):
        await callback.answer(tr(language, "payment_pending"), show_alert=True)
        return

    await callback.answer(tr(language, "click_waiting_admin"), show_alert=True)


@router.callback_query(F.data.startswith("clickapprove:"))
async def click_admin_approve(callback: CallbackQuery, bot: Bot):
    if not await is_payment_admin(callback.from_user.id, bot):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    merchant_trans_id = callback.data.split(":", 1)[1]
    payment = await get_click_payment(merchant_trans_id)
    if not payment or payment["status"] != "kutilmoqda":
        await callback.answer("Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
        return
    try:
        status = await click_api.check_payment_status_by_mti(merchant_trans_id)
    except Exception:
        logger.exception("Click to'lov holatini tekshirib bo'lmadi (mti=%s)", merchant_trans_id)
        await callback.answer("Click holatini tekshirib bo'lmadi. Keyinroq qayta urinib ko'ring.", show_alert=True)
        return
    if not click_api.is_paid(status):
        await callback.answer("Click tizimida to'lov hali bajarilmagan.", show_alert=True)
        return

    await set_click_payment_status(merchant_trans_id, "tolandi")
    await complete_payment(
        payment["telegram_id"], payment["purpose"], payment["payload"], bot,
        payment["amount_som"], paid_via="Click",
    )
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"✅ Click to'lovi tasdiqlandi — {callback.from_user.full_name}."
    )
    await callback.answer("To'lov tasdiqlandi.")


@router.callback_query(F.data.startswith("clickreject:"))
async def click_admin_reject(callback: CallbackQuery, bot: Bot):
    if not await is_payment_admin(callback.from_user.id, bot):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    merchant_trans_id = callback.data.split(":", 1)[1]
    payment = await get_click_payment(merchant_trans_id)
    if not payment or payment["status"] != "kutilmoqda":
        await callback.answer("Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await set_click_payment_status(merchant_trans_id, "rad_etildi")
    await bot.send_message(
        payment["telegram_id"],
        "❌ Click to'lov so'rovingiz admin tomonidan rad etildi. Mablag' yechilgan bo'lsa, admin bilan bog'laning.",
    )
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"❌ Click to'lovi rad etildi — {callback.from_user.full_name}."
    )
    await callback.answer("To'lov rad etildi.")
