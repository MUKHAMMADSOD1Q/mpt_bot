import html

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, User

from bot.states import OrderPresentation, OrderConfirm, PreCal
from bot.keyboards import (
    skip_kb, language_choice_kb, presentation_entry_kb, precal_tariff_kb, precal_approve_kb,
    free_tariff_kb,
)
from bot.services.validators import is_valid_topic, is_valid_pages, is_valid_full_name, is_valid_optional_text
from bot.services.pricing import calculate_price, format_som
from bot.services.group_orders import begin_confirmation, tashkent_timestamp
from bot.config import MIN_PAGES, MAX_PAGES, TARIFFS
from bot.database import get_user, update_user_telegram_profile
from bot.i18n import menu_labels, normalize_language, tr
from bot.keyboards import tariff_kb
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


async def _ui_language(user_id: int) -> str:
    user = await get_user(user_id)
    return normalize_language(user.get("lang") if user else None)


# ==================== KIRISH: buyurtma yoki PreCal ====================

@router.message(F.text.in_(menu_labels("presentation")))
async def presentation_entry(message: Message, state: FSMContext):
    language = await _ui_language(message.from_user.id)
    await state.clear()
    await message.answer(
        "What would you like to do?\n\n"
        "🧮 <b>PreCal</b> — calculate a presentation price without placing an order."
        if language == "en" else
        "Nima qilmoqchisiz?\n\n"
        "🧮 <b>PreCal</b> — buyurtma bermasdan taqdimot narxini hisoblab ko'rish.",
        parse_mode="HTML",
        reply_markup=presentation_entry_kb(),
    )


@router.callback_query(F.data == "pres:order")
async def start_order(callback: CallbackQuery, state: FSMContext):
    language = await _ui_language(callback.from_user.id)
    await state.clear()
    await state.set_state(OrderPresentation.waiting_topic)
    await callback.message.answer(
        tr(language, "topic_prompt") + (
            "\n\n<i>Please make the topic as clear and specific as possible.</i>"
            if language == "en" else ""
        ),
        parse_mode="HTML",
    )
    await callback.answer()


# ==================== PRECAL ====================

@router.callback_query(F.data == "pres:precal")
async def precal_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(PreCal.waiting_tariff)
    await callback.message.answer(
        "🧮 <b>PreCal</b> — qaysi ta'rifda hisoblaymiz?\n\n"
        "<i>Narxlar taqdimotning bir sahifasi uchun ko'rsatilgan.</i>",
        parse_mode="HTML",
        reply_markup=precal_tariff_kb(),
    )
    await callback.answer()


@router.callback_query(PreCal.waiting_tariff, F.data.startswith("precal_t:"))
async def precal_tariff(callback: CallbackQuery, state: FSMContext):
    await state.update_data(tariff=callback.data.split(":", 1)[1])
    await state.set_state(PreCal.waiting_pages)
    await callback.message.answer("Taqdimot nechta sahifali bo'lsin?")
    await callback.answer()


@router.message(PreCal.waiting_pages)
async def precal_pages(message: Message, state: FSMContext):
    ok, value = is_valid_pages(message.text or "", MIN_PAGES, MAX_PAGES)
    if not ok:
        await message.answer(f"Iltimos, faqat raqam kiriting ({MIN_PAGES}-{MAX_PAGES} oralig'ida).")
        return
    await state.update_data(pages=value)
    await state.set_state(PreCal.waiting_language)
    await message.answer("Taqdimot qaysi tilda bo'lsin?", reply_markup=language_choice_kb("precal_lang"))


async def _show_precal_result(message: Message, state: FSMContext):
    data = await state.get_data()
    p = calculate_price(data["tariff"], data["pages"], data["language"])
    extra = ""
    if p["surcharge_per_page_som"]:
        extra = f"\n🌐 Chet tili uchun +{format_som(p['surcharge_per_page_som'])} so'm/sahifa hisobga olingan."
    await state.set_state(PreCal.waiting_approval)
    await message.answer(
        f"🧮 <b>Hisob-kitob</b>\n\n"
        f"Ta'rif: <b>{p['tariff_title']}</b>\nSahifalar: {p['pages']}\nTil: {data['language']}\n"
        f"1 sahifa: {format_som(p['price_per_page_som'])} so'm{extra}\n\n"
        f"💰 Jami: <b>{format_som(p['price_som'])} so'm</b> ({p['price_mpt']:.1f} MPT)\n\n"
        "Narx ma'qulmi?",
        parse_mode="HTML",
        reply_markup=precal_approve_kb(),
    )


@router.callback_query(PreCal.waiting_language, F.data.startswith("precal_lang:"))
async def precal_language(callback: CallbackQuery, state: FSMContext):
    await state.update_data(language=callback.data.split(":", 1)[1])
    await callback.answer()
    await _show_precal_result(callback.message, state)


@router.callback_query(PreCal.waiting_approval, F.data == "precal_ok")
async def precal_approved(callback: CallbackQuery, state: FSMContext):
    await state.update_data(precal=True)
    await state.set_state(OrderPresentation.waiting_topic)
    await callback.message.answer("Ajoyib! Endi taqdimot mavzusini kiriting:")
    await callback.answer()


@router.callback_query(PreCal.waiting_approval, F.data == "precal_cheaper")
async def precal_cheaper(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current = TARIFFS[data["tariff"]]["som"]
    cheaper = [(k, t) for k, t in TARIFFS.items() if t["som"] < current]
    if not cheaper:
        await callback.message.answer("Bu allaqachon eng arzon ta'rif 🙂 Xohlasangiz, sahifalar sonini kamaytirib ko'ring.")
        await callback.answer()
        return
    builder = InlineKeyboardBuilder()
    lines = ["💸 <b>Arzonroq ta'riflar</b> (sizning sahifa soni va tilingiz bo'yicha):\n"]
    for key, t in reversed(cheaper):
        p = calculate_price(key, data["pages"], data["language"])
        lines.append(f"• {t['title']} — {format_som(p['price_som'])} so'm")
        builder.button(text=f"{t['title']} — {format_som(p['price_som'])} so'm", callback_data=f"precal_pick:{key}")
    builder.adjust(1)
    await callback.message.answer("\n".join(lines), parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(PreCal.waiting_approval, F.data.startswith("precal_pick:"))
async def precal_pick(callback: CallbackQuery, state: FSMContext):
    await state.update_data(tariff=callback.data.split(":", 1)[1])
    await callback.answer()
    await _show_precal_result(callback.message, state)


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
        tr(language, "pages_prompt"),
        parse_mode="HTML",
    )


@router.message(OrderPresentation.waiting_pages)
async def process_pages(message: Message, state: FSMContext):
    language = await _ui_language(message.from_user.id)
    ok, value = is_valid_pages(message.text or "", MIN_PAGES, MAX_PAGES)
    if not ok:
        await message.answer(tr(language, "pages_invalid", minimum=MIN_PAGES, maximum=MAX_PAGES))
        return
    await state.update_data(pages=value)
    await state.set_state(OrderPresentation.waiting_fullname)
    await message.answer(tr(language, "fullname_prompt"))


@router.message(OrderPresentation.waiting_fullname)
async def process_fullname(message: Message, state: FSMContext):
    language = await _ui_language(message.from_user.id)
    if not is_valid_full_name(message.text or ""):
        await message.answer(tr(language, "fullname_invalid"))
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(OrderPresentation.waiting_institution)
    await message.answer(
        tr(language, "institution_prompt"),
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
    await ask_direction(message, state)


@router.callback_query(OrderPresentation.waiting_institution, F.data == "skip")
async def skip_institution(callback: CallbackQuery, state: FSMContext):
    await state.update_data(institution="")
    await callback.answer()
    await ask_direction(callback.message, state)


async def ask_direction(message: Message, state: FSMContext):
    language = await _ui_language(message.from_user.id)
    await state.set_state(OrderPresentation.waiting_direction)
    await message.answer(
        tr(language, "direction_prompt"),
        parse_mode="HTML",
        reply_markup=skip_kb(language),
    )


async def after_direction(message: Message, state: FSMContext, from_user: User):
    data = await state.get_data()
    if data.get("precal"):  # ta'rif va til PreCal da tanlangan — to'g'ridan-to'g'ri xulosaga
        await build_summary(message, state, data["tariff"], from_user)
    else:
        await ask_language(message, state)


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
    await after_direction(callback.message, state, callback.from_user)


async def ask_language(message: Message, state: FSMContext):
    language = await _ui_language(message.from_user.id)
    await state.set_state(OrderPresentation.waiting_language)
    await message.answer(
        tr(language, "output_language_prompt"),
        parse_mode="HTML",
        reply_markup=language_choice_kb("pres_lang"),
    )


@router.callback_query(OrderPresentation.waiting_language, F.data.startswith("pres_lang:"))
async def process_language(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(language=callback.data.split(":", 1)[1])
    await ask_tariff(callback.message, state, edit=True)


async def ask_tariff(message: Message, state: FSMContext, edit: bool = False):
    language = await _ui_language(message.from_user.id)
    await state.set_state(OrderPresentation.waiting_tariff)
    data = await state.get_data()
    keyboard = free_tariff_kb(language) if data.get("ai_only_free") else tariff_kb()
    text = (
        (tr(language, "ai_free_only") + "\n\n" if data.get("ai_only_free") else "")
        + tr(language, "tariff_prompt")
    )
    if edit:
        try:
            await message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            return
        except TelegramBadRequest:
            pass
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


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

    preview = (
        f"Siz, <b>{pricing['tariff_title']}</b> tarif rejasida, "
        f"“{data['topic']}” mavzusida {data['pages']}ta sahifali ({language}) taqdimot tayyorlamoqchisiz.\n\n"
        f"Buyurtmaning umumiy narxi — <b>{format_som(pricing['price_som'])} so'm</b> "
        f"({pricing['price_mpt']:.1f} MPT).\n\nTasdiqlaysizmi?"
    )
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
