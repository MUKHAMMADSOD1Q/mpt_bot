from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.states import OrderPresentation
from bot.keyboards import tariff_kb, confirm_order_kb, skip_kb, main_menu_kb, admin_order_kb
from bot.services.validators import is_valid_topic, is_valid_pages, is_valid_full_name, is_valid_optional_text
from bot.services.pricing import calculate_price, format_som
from bot.config import MIN_PAGES, MAX_PAGES, ORDER_GROUP_ID
from bot.database import create_order, deduct_mpt_balance, get_user
from bot.services.payment_common import ask_payment_method

router = Router()


@router.message(F.text == "📊 Taqdimotga buyurtma berish")
async def start_order(message: Message, state: FSMContext):
    await state.set_state(OrderPresentation.waiting_topic)
    await message.answer(
        "Mavzu nomini kiriting:\n\n"
        "<i>Mavzu nomini imkon qadar aniq va tushunarli kiriting! "
        "Mavzu nomi taqdimotingizga to'g'ridan-to'g'ri ta'sir qilishi mumkin!</i>",
        parse_mode="HTML",
    )


@router.message(OrderPresentation.waiting_topic)
async def process_topic(message: Message, state: FSMContext):
    if not is_valid_topic(message.text):
        await message.answer("Iltimos, mavzu nomini to'g'ri kiriting (kamida 2 ta belgidan iborat, faqat raqam bo'lmasin).")
        return
    await state.update_data(topic=message.text.strip())
    await state.set_state(OrderPresentation.waiting_pages)
    await message.answer(
        "Taqdimotingiz nechta sahifali bo'lsin? Kiriting:\n\n"
        "<i>Kirish va yakuniy sahifalarni ham hisoblab kiriting!</i>",
        parse_mode="HTML",
    )


@router.message(OrderPresentation.waiting_pages)
async def process_pages(message: Message, state: FSMContext):
    ok, value = is_valid_pages(message.text, MIN_PAGES, MAX_PAGES)
    if not ok:
        await message.answer(f"Iltimos, faqat raqam kiriting ({MIN_PAGES}-{MAX_PAGES} oralig'ida).")
        return
    await state.update_data(pages=value)
    await state.set_state(OrderPresentation.waiting_fullname)
    await message.answer("Taqdimot yuzi uchun o'z ism-familiyangizni (otasini ismi ixtiyoriy) kiriting:")


@router.message(OrderPresentation.waiting_fullname)
async def process_fullname(message: Message, state: FSMContext):
    if not is_valid_full_name(message.text):
        await message.answer("Kiritilgan jumla ism emas. Iltimos isminizni kiriting!")
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(OrderPresentation.waiting_institution)
    await message.answer(
        "Taqdimot yuzi uchun ta'lim muassasasi nomini to'liq kiriting:\n"
        "<i>(Bu band ixtiyoriy — o'tkazib yuborishingiz mumkin)</i>",
        parse_mode="HTML",
        reply_markup=skip_kb(),
    )


@router.message(OrderPresentation.waiting_institution)
async def process_institution(message: Message, state: FSMContext):
    if not is_valid_optional_text(message.text):
        await message.answer("Iltimos, muassasa nomini to'g'ri kiriting yoki o'tkazib yuboring.")
        return
    await state.update_data(institution=message.text.strip())
    await ask_direction(message, state)


@router.callback_query(OrderPresentation.waiting_institution, F.data == "skip")
async def skip_institution(callback: CallbackQuery, state: FSMContext):
    await state.update_data(institution="")
    await callback.answer()
    await ask_direction(callback.message, state)


async def ask_direction(message: Message, state: FSMContext):
    await state.set_state(OrderPresentation.waiting_direction)
    await message.answer(
        "Yo'nalish nomi va guruhingizni kiriting:\n"
        "<i>(Bu band ham ixtiyoriy — o'tkazib yuborishingiz mumkin)</i>",
        parse_mode="HTML",
        reply_markup=skip_kb(),
    )


@router.message(OrderPresentation.waiting_direction)
async def process_direction(message: Message, state: FSMContext):
    if not is_valid_optional_text(message.text):
        await message.answer("Iltimos, yo'nalish/guruh nomini to'g'ri kiriting yoki o'tkazib yuboring.")
        return
    await state.update_data(direction=message.text.strip())
    await ask_language(message, state)


@router.callback_query(OrderPresentation.waiting_direction, F.data == "skip")
async def skip_direction(callback: CallbackQuery, state: FSMContext):
    await state.update_data(direction="")
    await callback.answer()
    await ask_language(callback.message, state)


async def ask_language(message: Message, state: FSMContext):
    await state.set_state(OrderPresentation.waiting_language)
    await message.answer(
        "Taqdimot qaysi tilda tayyorlansin?\n"
        "<i>(Ixtiyoriy — kiritmasangiz, standart til tanlanadi: O'zbekcha)</i>",
        parse_mode="HTML",
        reply_markup=skip_kb(),
    )


@router.message(OrderPresentation.waiting_language)
async def process_language(message: Message, state: FSMContext):
    await state.update_data(language=message.text.strip())
    await ask_tariff(message, state)


@router.callback_query(OrderPresentation.waiting_language, F.data == "skip")
async def skip_language(callback: CallbackQuery, state: FSMContext):
    await state.update_data(language="O'zbekcha")
    await callback.answer()
    await ask_tariff(callback.message, state)


async def ask_tariff(message: Message, state: FSMContext):
    await state.set_state(OrderPresentation.waiting_tariff)
    await message.answer("Ta'rif turini tanlang:", reply_markup=tariff_kb())


@router.callback_query(OrderPresentation.waiting_tariff, F.data.startswith("tariff:"))
async def process_tariff(callback: CallbackQuery, state: FSMContext):
    tariff_key = callback.data.split(":", 1)[1]
    data = await state.get_data()
    pricing = calculate_price(tariff_key, data["pages"])
    await state.update_data(tariff=tariff_key, **pricing)

    text = (
        f"Siz, <b>{pricing['tariff_title']}</b> tarif rejasida, "
        f"“{data['topic']}” mavzusida {data['pages']}ta sahifali taqdimot tayyorlamoqchisiz.\n\n"
        f"Buyurtmaning umumiy narxi — <b>{format_som(pricing['price_som'])} so'm</b> "
        f"({pricing['price_mpt']:.1f} MPT).\n\n"
        "Buyurtmani tasdiqlashni istasangiz <b>Generate</b> tugmasini bosing, "
        "bekor qilish uchun <b>Bekor qilish</b> tugmasini bosing."
    )
    await state.set_state(OrderPresentation.confirm)
    await callback.message.answer(text, parse_mode="HTML", reply_markup=confirm_order_kb())
    await callback.answer()


@router.callback_query(OrderPresentation.confirm, F.data == "order:cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Buyurtma bekor qilindi.", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(OrderPresentation.confirm, F.data == "order:confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = callback.from_user.id

    # Agar tarif pullik bo'lsa, MPT balansidan yechishga urinib ko'ramiz.
    # Agar MPT yetarli bo'lmasa, buyurtma "admin tasdig'i kutilmoqda" holatida qoladi
    # va foydalanuvchiga to'lov/balans to'ldirish yo'llari taklif qilinadi.
    mpt_needed = data["price_mpt"]
    paid_with_mpt = False
    if mpt_needed > 0:
        paid_with_mpt = await deduct_mpt_balance(user_id, mpt_needed)

    order_id = await create_order({
        "telegram_id": user_id,
        "topic": data["topic"],
        "pages": data["pages"],
        "tariff": data["tariff"],
        "price_som": data["price_som"],
        "price_mpt": data["price_mpt"],
        "full_name": data["full_name"],
        "institution": data.get("institution"),
        "direction": data.get("direction"),
        "language": data.get("language"),
    })

    if mpt_needed == 0 or paid_with_mpt:
        await callback.message.answer(
            f"✅ Buyurtmangiz (№{order_id}) qabul qilindi! Tez orada tayyor taqdimotingiz yuboriladi.",
            reply_markup=main_menu_kb(),
        )
        await bot.send_message(
            ORDER_GROUP_ID,
            _order_admin_text(order_id, data, callback.from_user, paid=True),
            reply_markup=admin_order_kb(order_id),
        )
        await state.clear()
    else:
        user = await get_user(user_id)
        balance = user["mpt_balance"] if user else 0
        await callback.message.answer(
            f"⚠️ Buyurtmangiz (№{order_id}) qayd etildi, lekin balansingizda yetarli MPT yo'q "
            f"(kerak: {mpt_needed:.1f} MPT, mavjud: {balance:.1f} MPT).\n\n"
            "To'lovni Click yoki karta orqali amalga oshirishingiz mumkin:",
        )
        # DIQQAT: state.clear() chaqirilmaydi — ask_payment_method uchun state ochiq qoladi
        await ask_payment_method(callback.message, state, purpose="order", amount_som=data["price_som"], payload=str(order_id))
        await bot.send_message(
            ORDER_GROUP_ID,
            _order_admin_text(order_id, data, callback.from_user, paid=False),
            reply_markup=admin_order_kb(order_id),
        )

    await callback.answer()


def _order_admin_text(order_id: int, data: dict, user, paid: bool) -> str:
    status = "✅ MPT bilan to'landi" if paid else "❌ To'lov kutilmoqda"
    phone = data.get("phone") or "O'tkazib yuborgan"
    return (
        f"🆕 Yangi buyurtma №{order_id}\n"
        f"Foydalanuvchi: @{user.username or '-'} (id: {user.id})\n"
        f"USER_ID: {user.id}\n"
        f"Telefon: {phone}\n"
        f"Mavzu: {data['topic']}\n"
        f"Sahifalar: {data['pages']}\n"
        f"Tarif: {data['tariff_title']}\n"
        f"Narx: {format_som(data['price_som'])} so'm / {data['price_mpt']:.1f} MPT\n"
        f"Ism: {data['full_name']}\n"
        f"Muassasa: {data.get('institution') or '-'}\n"
        f"Yo'nalish: {data.get('direction') or '-'}\n"
        f"Til: {data.get('language') or '-'}\n"
        f"Holat: {status}"
    )
