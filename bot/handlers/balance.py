from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database import get_or_create_user, get_user
from bot.keyboards import subscription_kb, mpt_topup_amounts_kb
from bot.config import SUBSCRIPTIONS, ADMIN_USERNAME, MPT_PRICE_SOM
from bot.services.payment_common import ask_payment_method
from bot.texts import MPT_INFO, SUB_INFO

router = Router()


def _balance_actions_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🪙 MPT sotib olish", callback_data="menu:buympt")
    builder.button(text="📅 Obuna sotib olish", callback_data="menu:subs")
    builder.adjust(1)
    return builder.as_markup()


@router.message(F.text == "💳 Balans va obuna")
async def balance_menu(message: Message):
    user = await get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name,
    )
    text = f"💰 Sizning balansingiz: <b>{user['mpt_balance']:.1f} MPT</b>\n"
    if user.get("subscription_type") and user.get("subscription_expiry"):
        text += f"📅 Faol obuna: {user['subscription_type']} (tugash sanasi: {user['subscription_expiry'][:10]})\n"
    text += (
        f"\nMPT sotib olish yoki obuna rasmiylashtirish uchun to'lov qiling, "
        f"yoki to'g'ridan-to'g'ri @{ADMIN_USERNAME} ga murojaat qiling:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=_balance_actions_kb())


@router.callback_query(F.data == "menu:buympt")
async def show_mpt_amounts(callback: CallbackQuery):
    await callback.message.answer(
        f"{MPT_INFO}\n\nNechta MPT sotib olmoqchisiz?",
        parse_mode="HTML",
        reply_markup=mpt_topup_amounts_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buympt:"))
async def buy_mpt(callback: CallbackQuery, state: FSMContext):
    mpt_amount = float(callback.data.split(":", 1)[1])
    amount_som = mpt_amount * MPT_PRICE_SOM
    await callback.answer()
    await ask_payment_method(callback.message, state, purpose="mpt", amount_som=amount_som, payload=str(mpt_amount))


@router.callback_query(F.data == "menu:subs")
async def show_subscriptions(callback: CallbackQuery):
    await callback.message.answer(f"{SUB_INFO}\n\nObuna turini tanlang:", parse_mode="HTML", reply_markup=subscription_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("sub:"))
async def subscription_chosen(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":", 1)[1]
    sub = SUBSCRIPTIONS[key]
    await callback.answer()
    await ask_payment_method(callback.message, state, purpose="sub", amount_som=sub["som"], payload=key)
