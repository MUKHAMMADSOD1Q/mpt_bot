from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import OWNER_ID
from bot.database import get_or_create_user
from bot.keyboards import (
    main_menu_kb, admin_menu_kb, contact_kb, games_kb, admin_contact_prompt_kb,
)
from bot.states import OrderPresentation
from bot.texts import ABOUT_US_HTML, build_guide, chunk_text

router = Router()


def _menu_for(user: dict, user_id: int):
    return admin_menu_kb(super_admin=user_id == OWNER_ID) if user.get("is_admin_mode") else main_menu_kb()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name,
    )
    text = (
        f"Assalomu alaykum, {message.from_user.full_name}! 👋\n\n"
        "Men — talabalar va ish egalari uchun taqdimot, referat, kurs ishi, "
        "hujjatlar va boshqa xizmatlarni tez va sifatli tayyorlashda yordam beruvchi botman.\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang:"
    )
    await message.answer(text, reply_markup=_menu_for(user, message.from_user.id))


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    user = await get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name,
    )
    await message.answer("Bosh menyu:", reply_markup=_menu_for(user, message.from_user.id))


@router.message(F.text == "🤖 Sun'iy intellekt yordamida")
async def ai_menu(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(ai_only_free=True)
    await state.set_state(OrderPresentation.waiting_topic)
    await message.answer(
        "🤖 Hozircha AI faqat bepul taqdimot tayyorlaydi.\n"
        "Taqdimot mavzusini kiriting:",
        reply_markup=admin_contact_prompt_kb(),
    )


@router.message(F.text == "ℹ️ Admin bilan bog'lanish")
async def contact_admin(message: Message):
    await message.answer("Admin bilan bog'lanish uchun quyidagilardan birini tanlang:", reply_markup=contact_kb())


@router.callback_query(F.data == "show_admin_contacts")
async def show_admin_contacts(callback: CallbackQuery):
    await callback.message.answer(
        "Admin bilan bog'lanish uchun quyidagilardan birini tanlang:",
        reply_markup=contact_kb(),
    )
    await callback.answer()


@router.message(F.text == "🎮 O'yin va ko'ngil ochish")
async def games_menu(message: Message):
    await message.answer("Ko'ngil ochish uchun havolalar:", reply_markup=games_kb())


@router.message(F.text == "🤝 Biz haqimizda")
async def about_us(message: Message):
    await message.answer(ABOUT_US_HTML, parse_mode="HTML", disable_web_page_preview=True)


@router.message(F.text == "📖 Foydalanish qo'llanmasi")
async def guide(message: Message):
    for part in chunk_text(build_guide()):
        await message.answer(part, parse_mode="HTML", disable_web_page_preview=True)
