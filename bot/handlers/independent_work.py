from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.states import IndependentWork
from bot.keyboards import independent_work_type_kb, yes_no_kb, language_choice_kb
from bot.services.validators import is_valid_topic, is_valid_pages
from bot.services.pricing import format_som
from bot.services.group_orders import begin_confirmation, tashkent_timestamp
from bot.config import MIN_PAGES, MAX_PAGES, INDEPENDENT_WORK_TYPES, LANGUAGE_SURCHARGE_PER_PAGE
from bot.database import get_user
from bot.i18n import menu_labels, tr
from bot.services.user_locale import get_user_locale

router = Router()


@router.message(F.text.in_(menu_labels("independent")))
async def start_independent_work(message: Message, state: FSMContext):
    language = await get_user_locale(message.from_user.id)
    await state.set_state(IndependentWork.waiting_type)
    await message.answer(tr(language, "ind_type"), reply_markup=independent_work_type_kb(language))


@router.callback_query(IndependentWork.waiting_type, F.data.startswith("iw_type:"))
async def choose_type(callback: CallbackQuery, state: FSMContext):
    language = await get_user_locale(callback.from_user.id)
    work_type = callback.data.split(":", 1)[1]
    await state.update_data(work_type=work_type)
    await state.set_state(IndependentWork.waiting_topic)
    await callback.message.answer(tr(language, "topic_enter"))
    await callback.answer()


@router.message(IndependentWork.waiting_topic)
async def process_topic(message: Message, state: FSMContext):
    language = await get_user_locale(message.from_user.id)
    if not is_valid_topic(message.text):
        await message.answer(tr(language, "topic_invalid_short"))
        return
    await state.update_data(topic=message.text.strip())
    await state.set_state(IndependentWork.waiting_pages)
    await message.answer(tr(language, "pages_enter"))


@router.message(IndependentWork.waiting_pages)
async def process_pages(message: Message, state: FSMContext):
    language = await get_user_locale(message.from_user.id)
    ok, value = is_valid_pages(message.text, MIN_PAGES, MAX_PAGES)
    if not ok:
        await message.answer(tr(language, "pages_invalid_short", minimum=MIN_PAGES, maximum=MAX_PAGES))
        return
    await state.update_data(pages=value)
    await state.set_state(IndependentWork.waiting_images)
    await message.answer(tr(language, "images_question"), reply_markup=yes_no_kb("iw_img", language))


@router.callback_query(IndependentWork.waiting_images, F.data.startswith("iw_img:"))
async def process_images(callback: CallbackQuery, state: FSMContext):
    language = await get_user_locale(callback.from_user.id)
    has_images = callback.data.endswith(":ha")
    await state.update_data(has_images=has_images)
    await state.set_state(IndependentWork.waiting_graphics)
    await callback.message.answer(tr(language, "graphics_question"), reply_markup=yes_no_kb("iw_graf", language))
    await callback.answer()


@router.callback_query(IndependentWork.waiting_graphics, F.data.startswith("iw_graf:"))
async def process_graphics(callback: CallbackQuery, state: FSMContext):
    language_ui = await get_user_locale(callback.from_user.id)
    has_graphics = callback.data.endswith(":ha")
    await state.update_data(has_graphics=has_graphics)
    await state.set_state(IndependentWork.waiting_language)
    await callback.message.answer(tr(language_ui, "language_question"), reply_markup=language_choice_kb("iw_lang", language_ui))
    await callback.answer()


@router.callback_query(IndependentWork.waiting_language, F.data.startswith("iw_lang:"))
async def process_language(callback: CallbackQuery, state: FSMContext):
    language = callback.data.split(":", 1)[1]
    data = await state.get_data()
    telegram_id = callback.from_user.id
    language_ui = await get_user_locale(telegram_id)
    username = callback.from_user.username or "-"
    user = await get_user(telegram_id)
    phone = (user.get("phone") if user else None) or "O'tkazib yuborgan"

    work_info = INDEPENDENT_WORK_TYPES[data["work_type"]]
    pages = data["pages"]

    if work_info["price_per_page"] is None:
        price_som = None
        price_text = tr(language_ui, "price_by_admin")
    else:
        per_page = work_info["price_per_page"]
        if language != "O'zbek":
            per_page += LANGUAGE_SURCHARGE_PER_PAGE
        price_som = per_page * pages
        price_text = tr(language_ui, "ind_price", total=format_som(price_som), unit=format_som(per_page))

    images_label = "Ha" if data["has_images"] else "Yo'q"
    graphics_label = "Ha" if data["has_graphics"] else "Yo'q"

    group_lines = [
        f"👤 Ism: {callback.from_user.full_name}",
        f"🔗 Username: @{username}",
        f"📞 Telefon raqam: {phone}",
        f"📄 Ish turi: {work_info['title']}",
        f"📝 Mavzu: {data['topic']}",
        f"📑 Sahifalar soni: {pages}",
        f"🖼 Ichida rasm: {images_label}",
        f"📊 Grafika/jadval: {graphics_label}",
        f"🌐 Til: {language}",
        f"💰 Narx: {price_text}",
        f"USER_ID: {telegram_id}",
        f"🕒 Sana/vaqt: {tashkent_timestamp()}",
    ]

    localized_type = tr(language_ui, f"ind_type_{data['work_type']}")
    preview = tr(
        language_ui, "independent_preview", title=localized_type, topic=data["topic"],
        pages=pages, language=language, price=price_text,
    )

    await begin_confirmation(
        callback.message, state,
        flow_kind="service",
        telegram_id=telegram_id,
        service_type=f"mustaqil_ish:{data['work_type']}",
        topic=data["topic"],
        summary_text="\n".join(group_lines),
        price_som=price_som,
        group_lines=group_lines,
        preview_text=preview,
    )
    await callback.answer()
