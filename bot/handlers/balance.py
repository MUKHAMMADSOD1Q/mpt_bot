from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database import get_or_create_user, get_user
from bot.keyboards import subscription_kb, mpt_topup_amounts_kb
from bot.config import SUBSCRIPTIONS, ADMIN_USERNAME, MPT_PRICE_SOM
from bot.services.payment_common import ask_payment_method
from bot.i18n import menu_labels, tr
from bot.services.user_locale import get_user_locale
from bot.config import MPT_PRICE_SOM
from bot.services.pricing import format_som

router = Router()


def _balance_actions_kb(language: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(language, "buy_mpt"), callback_data="menu:buympt")
    builder.button(text=tr(language, "buy_subscription"), callback_data="menu:subs")
    builder.button(text=tr(language, "menu_back"), callback_data="nav:back")
    builder.adjust(1)
    return builder.as_markup()


@router.message(F.text.in_(menu_labels("balance")))
async def balance_menu(message: Message):
    user = await get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name,
    )
    language = await get_user_locale(message.from_user.id)
    text = tr(language, "balance", balance=user["mpt_balance"])
    if user.get("subscription_type") and user.get("subscription_expiry"):
        subscription_type = user["subscription_type"]
        name = tr(language, f"subscription_{subscription_type}") if subscription_type in {"1oy", "3oy", "6oy", "9oy", "12oy"} else subscription_type
        text += tr(language, "active_subscription", name=name, date=user["subscription_expiry"][:10])
    text += "\n" + tr(language, "balance_options", admin=ADMIN_USERNAME)
    await message.answer(text, parse_mode="HTML", reply_markup=_balance_actions_kb(language))


@router.callback_query(F.data == "menu:buympt")
async def show_mpt_amounts(callback: CallbackQuery):
    language = await get_user_locale(callback.from_user.id)
    await callback.message.answer(
        f"{tr(language, 'mpt_info', price=format_som(MPT_PRICE_SOM))}\n\n{tr(language, 'choose_mpt_amount')}",
        parse_mode="HTML",
        reply_markup=mpt_topup_amounts_kb(language),
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
    language = await get_user_locale(callback.from_user.id)
    await callback.message.answer(f"{tr(language, 'sub_info')}\n\n{tr(language, 'choose_subscription')}", parse_mode="HTML", reply_markup=subscription_kb(language))
    await callback.answer()


@router.callback_query(F.data.startswith("sub:"))
async def subscription_chosen(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":", 1)[1]
    sub = SUBSCRIPTIONS[key]
    await callback.answer()
    await ask_payment_method(callback.message, state, purpose="sub", amount_som=sub["som"], payload=key)
