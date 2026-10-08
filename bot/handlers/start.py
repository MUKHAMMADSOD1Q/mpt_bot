import html

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import OWNER_ID
from bot.database import get_or_create_user, set_user_language
from bot.keyboards import (
    main_menu_kb, admin_menu_kb, contact_kb, games_kb, admin_contact_prompt_kb,
    settings_kb, bot_language_kb,
)
from bot.states import OrderPresentation
from bot.texts import ABOUT_US_HTML, build_guide, chunk_text
from bot.i18n import menu_labels, normalize_language, tr
from bot.services.user_locale import get_user_locale

router = Router()


def _menu_for(user: dict, user_id: int):
    language = normalize_language(user.get("lang"))
    return admin_menu_kb(super_admin=user_id == OWNER_ID) if user.get("is_admin_mode") else main_menu_kb(language)


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name,
    )
    language = normalize_language(user.get("lang"))
    text = tr(language, "start", name=html.escape(message.from_user.full_name))
    await message.answer(text, reply_markup=_menu_for(user, message.from_user.id))


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    user = await get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name,
    )
    language = normalize_language(user.get("lang"))
    await message.answer(tr(language, "menu_title"), reply_markup=_menu_for(user, message.from_user.id))


@router.message(F.text.in_(menu_labels("ai")))
@router.message(F.text.in_(menu_labels("manual_presentation")))
async def ai_menu(message: Message, state: FSMContext):
    from bot.database import get_user

    await state.clear()
    await state.update_data(ai_only_free=True)
    await state.set_state(OrderPresentation.waiting_topic)
    user = await get_user(message.from_user.id)
    language = normalize_language(user.get("lang") if user else None)
    await message.answer(
        tr(language, "ai_start"),
        reply_markup=admin_contact_prompt_kb(language),
    )


@router.message(F.text.in_(menu_labels("settings")))
async def open_settings(message: Message):
    from bot.database import get_user

    user = await get_user(message.from_user.id)
    language = normalize_language(user.get("lang") if user else None)
    await message.answer(
        tr(language, "settings_title"),
        reply_markup=settings_kb(language),
    )


@router.callback_query(F.data.startswith("settings:"))
async def settings_action(callback: CallbackQuery):
    from bot.database import get_user

    user = await get_user(callback.from_user.id)
    language = normalize_language(user.get("lang") if user else None)
    action = callback.data.split(":", 1)[1]
    if action == "language":
        await callback.message.answer(
            tr(language, "language_title"),
            reply_markup=bot_language_kb(),
        )
    elif action == "contact":
        await callback.message.answer(
            tr(language, "settings_contact_text"),
            reply_markup=contact_kb(language),
        )
    elif action == "about":
        await callback.message.answer(
            ABOUT_US_HTML if language == "uz" else tr(language, "settings_about_text"),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    elif action == "guide":
        await callback.message.answer(tr(language, "guide_text"))
    else:
        await callback.answer(tr(language, "unknown_settings_action"), show_alert=True)
        return
    await callback.answer()


@router.callback_query(F.data.startswith("botlang:"))
async def select_bot_language(callback: CallbackQuery):
    language = callback.data.split(":", 1)[1]
    if language not in {"uz", "ru", "en", "tg", "kk", "ky", "tk"}:
        await callback.answer(tr(language, "unknown_language"), show_alert=True)
        return
    await get_or_create_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.full_name,
    )
    await set_user_language(callback.from_user.id, language)
    await callback.message.answer(
        tr(language, "language_saved"),
        reply_markup=main_menu_kb(language),
    )
    await callback.answer()


@router.callback_query(F.data == "show_admin_contacts")
async def show_admin_contacts(callback: CallbackQuery):
    from bot.database import get_user

    user = await get_user(callback.from_user.id)
    language = normalize_language(user.get("lang") if user else None)
    await callback.message.answer(
        tr(language, "settings_contact_text"),
        reply_markup=contact_kb(language),
    )
    await callback.answer()


@router.message(F.text.in_(menu_labels("games")))
async def games_menu(message: Message):
    language = await get_user_locale(message.from_user.id)
    await message.answer(tr(language, "games_intro"), reply_markup=games_kb())


@router.message(F.text == "🤝 Biz haqimizda")
async def about_us(message: Message):
    language = await get_user_locale(message.from_user.id)
    await message.answer(
        ABOUT_US_HTML if language == "uz" else tr(language, "settings_about_text"),
        parse_mode="HTML", disable_web_page_preview=True,
    )


@router.message(F.text == "📖 Foydalanish qo'llanmasi")
async def guide(message: Message):
    language = await get_user_locale(message.from_user.id)
    for part in chunk_text(build_guide() if language == "uz" else tr(language, "guide_text")):
        await message.answer(part, parse_mode="HTML", disable_web_page_preview=True)
