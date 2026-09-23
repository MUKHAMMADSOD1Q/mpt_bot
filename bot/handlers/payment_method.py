from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.handlers.click_payment import start_click_payment
from bot.handlers.card_payment import start_card_payment
from bot.keyboards import main_menu_kb
from bot.services.payment_common import payment_method_kb

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


@router.callback_query(F.data == "paymethod:extend")
async def method_extend(callback: CallbackQuery, state: FSMContext):
    await callback.answer("✅ 5 daqiqa qo'shildi.")
    await callback.message.answer(
        "To'lovni yakunlash uchun quyidagi usullardan birini tanlang. "
        "Yana 5 daqiqa qo'shildi.",
        reply_markup=payment_method_kb(),
    )


@router.callback_query(F.data == "paymethod:cancel")
async def method_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ To'lov bekor qilindi.", reply_markup=main_menu_kb())
    await callback.answer()
