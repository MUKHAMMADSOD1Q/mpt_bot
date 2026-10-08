from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.states import OrderConfirm
from bot.services.group_orders import (
    post_pending_group_message, mark_group_message, confirm2_kb, attach_keyboard, ACCEPTED_MARK, CANCELLED_MARK,
)
from bot.keyboards import setprice_kb
from bot.services.payment_common import ask_payment_method
from bot.database import (
    create_order, set_order_group_message, set_order_status,
    deduct_mpt_balance, create_service_order, set_service_order_group_message,
    get_user, set_order_paid_via, update_user_telegram_profile,
)
from bot.services.user_locale import localized_main_menu
from bot.services.payment_common import subscription_covers
from bot.services.group_orders import append_order_history
from bot.i18n import tr
from bot.services.user_locale import get_user_locale

router = Router()


@router.callback_query(OrderConfirm.confirm1, F.data == "flow_confirm")
async def step_one_confirmed(callback: CallbackQuery, state: FSMContext, bot: Bot):
    language = await get_user_locale(callback.from_user.id)
    data = await state.get_data()
    if not data.get("group_message_id"):
        msg_id, full_text = await post_pending_group_message(bot, data["group_lines"])
        await state.update_data(group_message_id=msg_id, group_full_text=full_text)
    await state.set_state(OrderConfirm.confirm2)
    await callback.message.answer(
        tr(language, "confirm_warning"),
        reply_markup=confirm2_kb(language),
    )
    await callback.answer()


@router.callback_query(OrderConfirm.confirm2, F.data == "flow_confirm")
async def step_two_confirmed(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    data["group_full_text"] = await mark_group_message(
        bot, data["group_message_id"], data["group_full_text"], ACCEPTED_MARK,
    )
    await callback.answer()

    if data["flow_kind"] == "presentation":
        await _finalize_presentation(callback, state, bot, data)
    else:
        await _finalize_service(callback, state, bot, data)


@router.callback_query(F.data == "flow_cancel")
async def flow_cancelled(callback: CallbackQuery, state: FSMContext, bot: Bot):
    language = await get_user_locale(callback.from_user.id)
    data = await state.get_data()
    if data.get("group_message_id"):
        await mark_group_message(bot, data["group_message_id"], data["group_full_text"], CANCELLED_MARK)
    await state.clear()
    await callback.message.answer(
        tr(language, "order_cancelled"),
        reply_markup=await localized_main_menu(callback.from_user.id),
    )
    await callback.answer()


async def _finalize_presentation(callback: CallbackQuery, state: FSMContext, bot: Bot, data: dict):
    telegram_id = data["telegram_id"]
    language = await get_user_locale(telegram_id)
    await update_user_telegram_profile(
        telegram_id, callback.from_user.username, callback.from_user.full_name,
    )
    order_id = await create_order({
        "telegram_id": telegram_id,
        "topic": data["topic"],
        "pages": data["pages"],
        "tariff": data["tariff"],
        "price_som": data["price_som"],
        "price_mpt": data["price_mpt"],
        "full_name": data["full_name"],
        "telegram_name": callback.from_user.full_name,
        "institution": data.get("institution"),
        "direction": data.get("direction"),
        "language": data.get("language"),
    })
    await set_order_group_message(order_id, data["group_message_id"])
    data["group_full_text"] = await append_order_history(
        bot, data["group_message_id"], data["group_full_text"], telegram_id,
    )

    user = await get_user(telegram_id)
    mpt_needed = data["price_mpt"]
    if mpt_needed == 0:
        paid_via = "Bepul tarif"
    elif subscription_covers(user, data["tariff"]):
        paid_via = "Oylik obuna doirasida"
    elif await deduct_mpt_balance(telegram_id, mpt_needed):
        paid_via = "MPT balansidan"
    else:
        paid_via = None

    await state.clear()

    if paid_via:
        display_paid_via = tr(language, {
            "Bepul tarif": "payment_via_free",
            "Oylik obuna doirasida": "payment_via_subscription",
            "MPT balansidan": "payment_via_mpt",
        }.get(paid_via, "payment_via_other"))
        await set_order_status(order_id, "tolandi")
        await set_order_paid_via(order_id, paid_via)
        await callback.message.answer(
            tr(language, "payment_accepted", via=display_paid_via, id=order_id),
            reply_markup=await localized_main_menu(telegram_id),
        )
        from bot.services.payment_common import notify_files_group_ready
        await notify_files_group_ready(bot, kind="order", record_id=order_id)
    else:
        await callback.message.answer(
            tr(language, "insufficient_balance")
        )
        await ask_payment_method(callback.message, state, purpose="order", amount_som=data["price_som"], payload=str(order_id))


async def _finalize_service(callback: CallbackQuery, state: FSMContext, bot: Bot, data: dict):
    telegram_id = data["telegram_id"]
    language = await get_user_locale(telegram_id)
    await update_user_telegram_profile(
        telegram_id, callback.from_user.username, callback.from_user.full_name,
    )
    service_order_id = await create_service_order(
        telegram_id, data["service_type"], data["topic"], data.get("summary_text", ""),
        data.get("price_som") or 0, callback.from_user.full_name,
    )
    await set_service_order_group_message(service_order_id, data["group_message_id"])
    data["group_full_text"] = await append_order_history(
        bot, data["group_message_id"], data["group_full_text"], telegram_id,
    )
    price_som = data.get("price_som")

    await state.clear()

    if price_som:
        await callback.message.answer(
            tr(language, "service_payment_prompt"),
            reply_markup=await localized_main_menu(telegram_id),
        )
        await ask_payment_method(callback.message, state, purpose="service", amount_som=price_som, payload=str(service_order_id))
    else:
        await attach_keyboard(bot, data["group_message_id"], setprice_kb(service_order_id))
        await callback.message.answer(
            tr(language, "service_accepted"),
            reply_markup=await localized_main_menu(telegram_id),
        )
