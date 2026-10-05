from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.handlers.click_payment import start_click_payment
from bot.handlers.card_payment import start_card_payment

router = Router()


@router.callback_query(F.data == "paymethod:click")
async def method_click(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.answer()
    await start_click_payment(
        callback.message, state,
        purpose=data["pm_purpose"], amount_som=data["pm_amount_som"], payload=data["pm_payload"],
    )


@router.callback_query(F.data == "paymethod:card")
async def method_card(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.answer()
    await start_card_payment(
        callback.message, state,
        purpose=data["pm_purpose"], amount_som=data["pm_amount_som"], payload=data["pm_payload"],
    )
