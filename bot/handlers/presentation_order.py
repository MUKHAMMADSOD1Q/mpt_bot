import html

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, User

from bot.states import OrderPresentation, OrderConfirm, PreCal
from bot.keyboards import (
    back_only_kb, skip_kb, language_choice_kb, presentation_entry_kb, precal_tariff_kb,
    precal_approve_kb, manual_start_kb,
)
from bot.services.validators import is_valid_topic, is_valid_pages, is_valid_full_name, is_valid_optional_text
from bot.services.pricing import calculate_price, format_som
from bot.services.group_orders import begin_confirmation, tashkent_timestamp
from bot.config import MAX_PAGES, TARIFFS
from bot.database import get_user, update_user_telegram_profile
from bot.i18n import menu_labels, normalize_language, tr
from bot.keyboards import tariff_kb
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()
MIN_PRESENTATION_PAGES = 3


async def _ui_language(user_id: int) -> str:
    user = await get_user(user_id)
    return normalize_language(user.get("lang") if user else None)


# ==================== KIRISH: buyurtma yoki PreCal ====================

@router.message(F.text.in_(menu_labels("presentation")))
async def presentation_entry(message: Message, state: FSMContext):
    language = await _ui_language(message.from_user.id)
    await state.clear()
    await message.answer(
        tr(language, "presentation_entry_intro"),
        parse_mode="HTML",
        reply_markup=presentation_entry_kb(language),
    )


@router.callback_query(F.data == "pres:order")
async def start_order(callback: CallbackQuery, state: FSMContext):
    language = await _ui_language(callback.from_user.id)
    await state.clear()
    await state.set_state(OrderPresentation.waiting_topic)
    await callback.message.answer(
        tr(language, "topic_prompt") + "\n\n<i>" + tr(language, "topic_note") + "</i>",
        parse_mode="HTML",
        reply_markup=back_only_kb(language),
    )
    await callback.answer()


# ==================== PRECAL ====================

@router.callback_query(F.data == "pres:precal")
async def precal_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(PreCal.waiting_tariff)
    language = await _ui_language(callback.from_user.id)
    await callback.message.answer(
        tr(language, "precal_intro"),
        parse_mode="HTML",
        reply_markup=precal_tariff_kb(language),
    )
    await callback.answer()


@router.callback_query(PreCal.waiting_tariff, F.data.startswith("precal_t:"))
async def precal_tariff(callback: CallbackQuery, state: FSMContext):
    language = await _ui_language(callback.from_user.id)
    await state.update_data(tariff=callback.data.split(":", 1)[1])
    await state.set_state(PreCal.waiting_pages)
    await callback.message.answer(tr(language, "pages_enter"))
    await callback.answer()


@router.message(PreCal.waiting_pages)
async def precal_pages(message: Message, state: FSMContext):
    language = await _ui_language(message.from_user.id)
    ok, value = is_valid_pages(message.text or "", MIN_PRESENTATION_PAGES, MAX_PAGES)
    if not ok:
        await message.answer(tr(language, "pages_invalid_short", minimum=MIN_PRESENTATION_PAGES, maximum=MAX_PAGES))
        return
    await state.update_data(pages=value)
    await state.set_state(PreCal.waiting_language)
    await message.answer(
        tr(language, "output_language_prompt"),
        reply_markup=language_choice_kb("precal_lang", language),
    )


async def _show_precal_result(message: Message, state: FSMContext, user_id: int):
    language = await _ui_language(user_id)
    data = await state.get_data()
    p = calculate_price(data["tariff"], data["pages"], data["language"])
    extra = ""
    if p["surcharge_per_page_som"]:
        extra = tr(language, "precal_surcharge", amount=format_som(p["surcharge_per_page_som"]))
    await state.set_state(PreCal.waiting_approval)
    await message.answer(
        tr(language, "precal_result", tariff=tr(language, f"tariff_{data['tariff']}"), pages=p["pages"],
           language=data["language"], per_page=format_som(p["price_per_page_som"]),
           total=format_som(p["price_som"]), mpt=p["price_mpt"], extra=extra),
        parse_mode="HTML",
        reply_markup=precal_approve_kb(language),
    )


@router.callback_query(PreCal.waiting_language, F.data.startswith("precal_lang:"))
async def precal_language(callback: CallbackQuery, state: FSMContext):
    if not isinstance(callback.message, Message):
        await callback.answer()
        return
    await state.update_data(language=callback.data.split(":", 1)[1])
    await callback.answer()
    await _show_precal_result(callback.message, state, callback.from_user.id)


@router.callback_query(PreCal.waiting_approval, F.data == "precal_ok")
async def precal_approved(callback: CallbackQuery, state: FSMContext):
    language = await _ui_language(callback.from_user.id)
    await state.update_data(precal=True)
    await state.set_state(OrderPresentation.waiting_topic)
    await callback.message.answer(tr(language, "precal_next"))
    await callback.answer()


@router.callback_query(PreCal.waiting_approval, F.data == "precal_cheaper")
async def precal_cheaper(callback: CallbackQuery, state: FSMContext):
    language = await _ui_language(callback.from_user.id)
    data = await state.get_data()
    current = TARIFFS[data["tariff"]]["som"]
    cheaper = [(k, t) for k, t in TARIFFS.items() if t["som"] < current]
    if not cheaper:
        await callback.message.answer(tr(language, "precal_already_cheapest"))
        await callback.answer()
        return
    builder = InlineKeyboardBuilder()
    lines = [tr(language, "precal_cheaper_title") + "\n"]
    for key, t in reversed(cheaper):
        p = calculate_price(key, data["pages"], data["language"])
        title = tr(language, f"tariff_{key}")
        lines.append(f"• {title} — {format_som(p['price_som'])} UZS")
        builder.button(text=f"{title} — {format_som(p['price_som'])} UZS", callback_data=f"precal_pick:{key}")
    builder.button(text=tr(language, "menu_back"), callback_data="nav:back")
    builder.adjust(1)
    await callback.message.answer("\n".join(lines), parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(PreCal.waiting_approval, F.data.startswith("precal_pick:"))
async def precal_pick(callback: CallbackQuery, state: FSMContext):
    if not isinstance(callback.message, Message):
        await callback.answer()
        return
    await state.update_data(tariff=callback.data.split(":", 1)[1])
    await callback.answer()
    await _show_precal_result(callback.message, state, callback.from_user.id)


# ==================== ODDIY BUYURTMA OQIMI ====================

@router.message(OrderPresentation.waiting_topic)
async def process_topic(message: Message, state: FSMContext):
    language = await _ui_language(message.from_user.id)
    if not is_valid_topic(message.text or ""):
        await message.answer(tr(language, "topic_invalid"))
        return
    await state.update_data(topic=message.text.strip())
    data = await state.get_data()
    if data.get("precal"):  # sahifa soni PreCal da allaqachon aniqlangan
        await state.set_state(OrderPresentation.waiting_fullname)
        await message.answer(tr(language, "fullname_prompt"))
        return
    await state.set_state(OrderPresentation.waiting_pages)
    await message.answer(
        tr(language, "manual_pages_prompt" if data.get("manual_mode") else "pages_prompt"),
        parse_mode="HTML",
    )


@router.message(OrderPresentation.waiting_pages)
async def process_pages(message: Message, state: FSMContext):
    language = await _ui_language(message.from_user.id)
    data = await state.get_data()
    minimum = MIN_PRESENTATION_PAGES
    ok, value = is_valid_pages(message.text or "", minimum, MAX_PAGES)
    if not ok:
        error_key = "manual_pages_invalid" if data.get("manual_mode") else "pages_invalid"
        await message.answer(tr(language, error_key, minimum=minimum, maximum=MAX_PAGES))
        return
    await state.update_data(pages=value)
    await state.set_state(OrderPresentation.waiting_fullname)
    prompt_key = "manual_fullname_prompt" if data.get("manual_mode") else "fullname_prompt"
    await message.answer(tr(language, prompt_key))


@router.message(OrderPresentation.waiting_fullname)
async def process_fullname(message: Message, state: FSMContext):
    language = await _ui_language(message.from_user.id)
    if not is_valid_full_name(message.text or ""):
        await message.answer(tr(language, "fullname_invalid"))
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(OrderPresentation.waiting_institution)
    data = await state.get_data()
    prompt_key = "manual_institution_prompt" if data.get("manual_mode") else "institution_prompt"
    await message.answer(
        tr(language, prompt_key),
        parse_mode="HTML",
        reply_markup=skip_kb(language),
    )


@router.message(OrderPresentation.waiting_institution)
async def process_institution(message: Message, state: FSMContext):
    language = await _ui_language(message.from_user.id)
    if not is_valid_optional_text(message.text or ""):
        await message.answer(tr(language, "institution_invalid"))
        return
    await state.update_data(institution=message.text.strip())
    await ask_direction(message, state, message.from_user.id)


@router.callback_query(OrderPresentation.waiting_institution, F.data == "skip")
async def skip_institution(callback: CallbackQuery, state: FSMContext):
    await state.update_data(institution="")
    await callback.answer()
    if isinstance(callback.message, Message):
        await ask_direction(callback.message, state, callback.from_user.id)


async def ask_direction(message: Message, state: FSMContext, user_id: int):
    language = await _ui_language(user_id)
    data = await state.get_data()
    prompt_key = "manual_direction_prompt" if data.get("manual_mode") else "direction_prompt"
    await state.set_state(OrderPresentation.waiting_direction)
    await message.answer(
        tr(language, prompt_key),
        parse_mode="HTML",
        reply_markup=skip_kb(language),
    )


async def after_direction(message: Message, state: FSMContext, from_user: User):
    data = await state.get_data()
    if data.get("precal"):  # ta'rif va til PreCal da tanlangan — to'g'ridan-to'g'ri xulosaga
        await build_summary(message, state, data["tariff"], from_user)
    else:
        await ask_language(message, state, from_user.id)


@router.message(OrderPresentation.waiting_direction)
async def process_direction(message: Message, state: FSMContext):
    language = await _ui_language(message.from_user.id)
    if not is_valid_optional_text(message.text or ""):
        await message.answer(tr(language, "direction_invalid"))
        return
    await state.update_data(direction=message.text.strip())
    await after_direction(message, state, message.from_user)


@router.callback_query(OrderPresentation.waiting_direction, F.data == "skip")
async def skip_direction(callback: CallbackQuery, state: FSMContext):
    await state.update_data(direction="")
    await callback.answer()
    if isinstance(callback.message, Message):
        await after_direction(callback.message, state, callback.from_user)


async def ask_language(message: Message, state: FSMContext, user_id: int):
    language = await _ui_language(user_id)
    data = await state.get_data()
    prompt_key = "manual_language_prompt" if data.get("manual_mode") else "output_language_prompt"
    await state.set_state(OrderPresentation.waiting_language)
    await message.answer(
        tr(language, prompt_key),
        parse_mode="HTML",
        reply_markup=language_choice_kb("pres_lang", language),
    )


@router.callback_query(OrderPresentation.waiting_language, F.data.startswith("pres_lang:"))
async def process_language(callback: CallbackQuery, state: FSMContext):
    if not isinstance(callback.message, Message):
        await callback.answer()
        return
    await callback.answer()
    await state.update_data(language=callback.data.split(":", 1)[1])
    await ask_tariff(callback.message, state, callback.from_user.id, edit=True)


async def ask_tariff(message: Message, state: FSMContext, user_id: int, edit: bool = False):
    language = await _ui_language(user_id)
    await state.set_state(OrderPresentation.waiting_tariff)
    data = await state.get_data()
    keyboard = manual_start_kb(language) if data.get("ai_only_free") else tariff_kb(language)
    text = (
        tr(language, "manual_begin_prompt")
        if data.get("ai_only_free")
        else tr(language, "tariff_prompt")
    )
    if edit:
        try:
            await message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            return
        except TelegramBadRequest:
            pass
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(OrderPresentation.waiting_tariff, F.data == "manual:begin")
async def begin_free_manual_presentation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("ai_only_free"):
        await callback.answer(
            tr(await _ui_language(callback.from_user.id), "ai_free_only"),
            show_alert=True,
        )
        return
    await callback.answer()
    from bot.handlers.manual_presentation import begin_manual_presentation

    await begin_manual_presentation(callback, state, data)


@router.callback_query(OrderPresentation.waiting_tariff, F.data.startswith("tariff:"))
async def process_tariff(callback: CallbackQuery, state: FSMContext):
    tariff_key = callback.data.split(":", 1)[1]
    data = await state.get_data()
    if data.get("ai_only_free") and tariff_key != "bepul":
        await callback.answer(tr(await _ui_language(callback.from_user.id), "ai_free_only"), show_alert=True)
        return
    await callback.answer()
    if data.get("ai_only_free"):
        from bot.handlers.manual_presentation import begin_manual_presentation

        await begin_manual_presentation(callback, state, data)
        return
    await build_summary(callback.message, state, tariff_key, callback.from_user)


async def build_summary(message: Message, state: FSMContext, tariff_key: str, from_user: User):
    data = await state.get_data()
    language = data.get("language") or "O'zbek"
    pricing = calculate_price(tariff_key, data["pages"], language)

    telegram_id = from_user.id
    user = await get_user(telegram_id)
    await update_user_telegram_profile(telegram_id, from_user.username, from_user.full_name)
    phone = (user.get("phone") if user else None) or "O'tkazib yuborgan"
    username = from_user.username or "-"
    institution = data.get("institution") or "O'tkazib yuborgan"
    direction = data.get("direction") or "O'tkazib yuborgan"

    group_lines = [
        f"👤 Ism: {data['full_name']}",
        f"👤 Telegramdagi ism: {html.escape(from_user.full_name)}",
        f"🔗 Username: @{username}",
        f"📞 Telefon raqam: {phone}",
        f"🏫 Ta'lim muassasasi: {institution}",
        f"🎓 Yo'nalish/guruh: {direction}",
        f"📄 Prezentatsiya turi: {pricing['tariff_title']}",
        f"📝 Prezentatsiya mavzusi: {data['topic']}",
        f"📑 Sahifalar soni: {data['pages']}",
        f"🌐 Til: {language}",
        f"💵 1 sahifa uchun narx: {format_som(pricing['price_per_page_som'])}",
        f"💰 Umumiy narx: {format_som(pricing['price_som'])}",
        f"USER_ID: {telegram_id}",
        f"🕒 Sana/vaqt: {tashkent_timestamp()}",
    ]

    ui_language = await _ui_language(telegram_id)
    preview = tr(ui_language, "presentation_preview",
                  tariff=tr(ui_language, f"tariff_{tariff_key}"), topic=data["topic"],
                  pages=data["pages"], language=language, total=format_som(pricing["price_som"]),
                  mpt=pricing["price_mpt"])
    await begin_confirmation(
        message, state,
        flow_kind="presentation",
        tariff=tariff_key, language=language, **pricing,
        topic=data["topic"], full_name=data["full_name"],
        institution=data.get("institution", ""), direction=data.get("direction", ""),
        telegram_id=telegram_id,
        group_lines=group_lines,
        preview_text=preview,
    )
