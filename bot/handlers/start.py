from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.database import get_or_create_user
from bot.keyboards import main_menu_kb, admin_menu_kb, contact_kb, games_kb
from bot.texts import ABOUT_US_HTML, build_guide, chunk_text

router = Router()


def _menu_for(user: dict):
    return admin_menu_kb() if user.get("is_admin_mode") else main_menu_kb()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    text = (
        f"Assalomu alaykum, {message.from_user.full_name}! 👋\n\n"
        "Men — talabalar va ish egalari uchun taqdimot, referat, kurs ishi, "
        "hujjatlar va boshqa xizmatlarni tez va sifatli tayyorlashda yordam beruvchi botman.\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang:"
    )
    await message.answer(text, reply_markup=_menu_for(user))


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer("Bosh menyu:", reply_markup=_menu_for(user))


@router.message(F.text == "🤖 Sun'iy intellekt yordamida")
async def ai_menu(message: Message):
    await message.answer(
        "🤖 Bu bo'lim vaqtinchalik ishlamayapti, tez vaqt ichida ishga tushiriladi.\n\n"
        "Murojaat uchun admin yoki owner profillariga yozing:",
        reply_markup=contact_kb(),
    )


@router.message(F.text == "ℹ️ Admin bilan bog'lanish")
async def contact_admin(message: Message):
    await message.answer("Admin bilan bog'lanish uchun quyidagilardan birini tanlang:", reply_markup=contact_kb())


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
