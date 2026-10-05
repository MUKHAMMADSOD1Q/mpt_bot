import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.states import IndependentWork
from bot.keyboards import independent_work_type_kb, yes_no_kb, language_choice_kb
from bot.services.validators import is_valid_topic, is_valid_pages
from bot.services.pricing import format_som
from bot.services.group_orders import begin_confirmation
from bot.config import MIN_PAGES, MAX_PAGES, INDEPENDENT_WORK_TYPES, LANGUAGE_SURCHARGE_PER_PAGE
from bot.database import get_user

router = Router()


@router.message(F.text == "📝 Mustaqil ishlarga buyurtma berish")
async def start_independent_work(message: Message, state: FSMContext):
    await state.set_state(IndependentWork.waiting_type)
    await message.answer("Ish turini tanlang:", reply_markup=independent_work_type_kb())


@router.callback_query(IndependentWork.waiting_type, F.data.startswith("iw_type:"))
async def choose_type(callback: CallbackQuery, state: FSMContext):
    work_type = callback.data.split(":", 1)[1]
    await state.update_data(work_type=work_type)
    await state.set_state(IndependentWork.waiting_topic)
    await callback.message.answer("Mavzu nomini kiriting:")
    await callback.answer()


@router.message(IndependentWork.waiting_topic)
async def process_topic(message: Message, state: FSMContext):
    if not is_valid_topic(message.text):
        await message.answer("Iltimos, mavzu nomini to'g'ri kiriting.")
        return
    await state.update_data(topic=message.text.strip())
    await state.set_state(IndependentWork.waiting_pages)
    await message.answer("Nechta sahifali bo'lishi kerak?")


@router.message(IndependentWork.waiting_pages)
async def process_pages(message: Message, state: FSMContext):
    ok, value = is_valid_pages(message.text, MIN_PAGES, MAX_PAGES)
    if not ok:
        await message.answer(f"Iltimos, faqat raqam kiriting ({MIN_PAGES}-{MAX_PAGES} oralig'ida).")
        return
    await state.update_data(pages=value)
    await state.set_state(IndependentWork.waiting_images)
    await message.answer("Ish ichida rasm bo'lsinmi?", reply_markup=yes_no_kb("iw_img"))


@router.callback_query(IndependentWork.waiting_images, F.data.startswith("iw_img:"))
async def process_images(callback: CallbackQuery, state: FSMContext):
    has_images = callback.data.endswith(":ha")
    await state.update_data(has_images=has_images)
    await state.set_state(IndependentWork.waiting_graphics)
    await callback.message.answer("Grafika va jadvallar kerakmi?", reply_markup=yes_no_kb("iw_graf"))
    await callback.answer()


@router.callback_query(IndependentWork.waiting_graphics, F.data.startswith("iw_graf:"))
async def process_graphics(callback: CallbackQuery, state: FSMContext):
    has_graphics = callback.data.endswith(":ha")
    await state.update_data(has_graphics=has_graphics)
    await state.set_state(IndependentWork.waiting_language)
    await callback.message.answer("Ish qaysi tilda bajarilsin?", reply_markup=language_choice_kb("iw_lang"))
    await callback.answer()


@router.callback_query(IndependentWork.waiting_language, F.data.startswith("iw_lang:"))
async def process_language(callback: CallbackQuery, state: FSMContext):
    language = callback.data.split(":", 1)[1]
    data = await state.get_data()
    telegram_id = callback.from_user.id
    username = callback.from_user.username or "-"
    user = await get_user(telegram_id)
    phone = (user.get("phone") if user else None) or "O'tkazib yuborgan"

    work_info = INDEPENDENT_WORK_TYPES[data["work_type"]]
    pages = data["pages"]

    if work_info["price_per_page"] is None:
        price_som = None
        price_text = "admin bilan kelishiladi"
    else:
        per_page = work_info["price_per_page"]
        if language != "O'zbek":
            per_page += LANGUAGE_SURCHARGE_PER_PAGE
        price_som = per_page * pages
        price_text = f"{format_som(price_som)} so'm ({format_som(per_page)} so'm/sahifa)"

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
        f"🕒 Sana/vaqt: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}",
    ]

    preview = (
        f"<b>{work_info['title']}</b> — “{data['topic']}”, {pages} sahifa.\n"
        f"Til: {language}. Narx: <b>{price_text}</b>.\n\nTasdiqlaysizmi?"
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
