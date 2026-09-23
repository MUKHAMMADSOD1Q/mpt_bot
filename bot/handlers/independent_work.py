from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import ADMIN_IDS, MPT_PRICE_SOM, ORDER_GROUP_ID
from bot.database import create_order, deduct_mpt_balance, get_user
from bot.keyboards import admin_order_kb, confirm_order_kb, main_menu_kb
from bot.services.payment_common import ask_payment_method
from bot.services.pricing import format_som
from bot.states import IndependentWork

router = Router()

WORK_TYPES = {
    "referat": ("Referat", 5_000),
    "mustaqil_ish": ("Mustaqil ish", 8_000),
    "kurs_ishi": ("Kurs ishi", 10_000),
    "word_other": ("Boshqa Word ishi", 0),
}


def _choices(items: list[tuple[str, str]]):
    builder = InlineKeyboardBuilder()
    for label, value in items:
        builder.button(text=label, callback_data=value)
    builder.adjust(2)
    return builder.as_markup()


def work_type_kb():
    return _choices([
        ("📘 Referat", "iw:type:referat"),
        ("📚 Mustaqil ish", "iw:type:mustaqil_ish"),
        ("🧾 Kurs ishi", "iw:type:kurs_ishi"),
        ("📝 Boshqa Word ishlari", "iw:type:word_other"),
    ])


def yes_no_kb():
    return _choices([("✅ Ha", "iw:yes"), ("❌ Yo'q", "iw:no")])


def language_kb():
    return _choices([
        ("🇺🇿 O'zbek", "iw:lang:uz"),
        ("🇷🇺 Rus", "iw:lang:ru"),
        ("🇬🇧 English", "iw:lang:en"),
        ("🌐 Boshqa til", "iw:lang:other"),
    ])


@router.message(F.text == "📝 Mustaqil ishlarga buyurtma berish")
async def start_independent_work(message: Message, state: FSMContext):
    await state.set_state(IndependentWork.waiting_type)
    await message.answer(
        "Ish turini tanlang.\n"
        "Referat — 5 000 so'm/sahifa, mustaqil ish — 8 000 so'm/sahifa, "
        "kurs ishi — 10 000 so'm/sahifa.",
        reply_markup=work_type_kb(),
    )


@router.callback_query(IndependentWork.waiting_type, F.data.startswith("iw:type:"))
async def work_type_selected(callback: CallbackQuery, state: FSMContext):
    work_type = callback.data.rsplit(":", 1)[1]
    await state.update_data(work_type=work_type)
    await state.set_state(IndependentWork.waiting_topic)
    await callback.message.answer("Mavzu nomini kiriting:")
    await callback.answer()


@router.message(IndependentWork.waiting_topic)
async def independent_topic(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("Iltimos, mavzuni to'liqroq kiriting.")
        return
    await state.update_data(topic=message.text.strip())
    await state.set_state(IndependentWork.waiting_pages)
    await message.answer("Sahifalar sonini kiriting:")


@router.message(IndependentWork.waiting_pages)
async def independent_pages(message: Message, state: FSMContext):
    try:
        pages = int((message.text or "").strip())
    except ValueError:
        await message.answer("Iltimos, faqat raqam kiriting.")
        return
    if pages < 1:
        await message.answer("Sahifalar soni kamida 1 bo'lishi kerak.")
        return
    await state.update_data(pages=pages)
    await state.set_state(IndependentWork.waiting_images)
    await message.answer("Ish ichida rasmlar bo'lsinmi?", reply_markup=yes_no_kb())


@router.callback_query(IndependentWork.waiting_images, F.data.in_({"iw:yes", "iw:no"}))
async def independent_images(callback: CallbackQuery, state: FSMContext):
    await state.update_data(images="Ha" if callback.data == "iw:yes" else "Yo'q")
    await state.set_state(IndependentWork.waiting_tables)
    await callback.message.answer("Grafika va jadvallar bo'lsinmi?", reply_markup=yes_no_kb())
    await callback.answer()


@router.callback_query(IndependentWork.waiting_tables, F.data.in_({"iw:yes", "iw:no"}))
async def independent_tables(callback: CallbackQuery, state: FSMContext):
    await state.update_data(tables="Ha" if callback.data == "iw:yes" else "Yo'q")
    await state.set_state(IndependentWork.waiting_language)
    await callback.message.answer("Ish tilini tanlang:", reply_markup=language_kb())
    await callback.answer()


@router.callback_query(IndependentWork.waiting_language, F.data.startswith("iw:lang:"))
async def independent_language(callback: CallbackQuery, state: FSMContext):
    language = {
        "uz": "O'zbek",
        "ru": "Rus",
        "en": "English",
        "other": "Boshqa til",
    }[callback.data.rsplit(":", 1)[1]]
    await state.update_data(language=language)
    await state.set_state(IndependentWork.waiting_extra)
    await callback.message.answer(
        "Qo'shimcha talablarni yozing: deadline, manba talabi, rasm/grafika tafsilotlari va boshqalar.\n"
        "Qo'shimcha talab bo'lmasa, o'tkazib yuboring.",
        reply_markup=_choices([("⏭ O'tkazib yuborish", "iw:skip_extra")]),
    )
    await callback.answer()


@router.message(IndependentWork.waiting_extra)
async def independent_extra(message: Message, state: FSMContext):
    data = await state.get_data()
    extra = (message.text or "").strip() or "-"
    pages = data["pages"]
    title, rate = WORK_TYPES[data["work_type"]]
    extra_language_fee = 1_000 if data["language"] != "O'zbek" else 0
    price_som = (rate + extra_language_fee) * pages
    await state.update_data(extra=extra, price_som=price_som, price_mpt=price_som / MPT_PRICE_SOM)
    data = await state.get_data()
    text = (
        f"📝 <b>{title}</b> buyurtmasi\n\n"
        f"Mavzu: {data['topic']}\nSahifalar: {pages}\n"
        f"Rasm: {data['images']}\nGrafika/jadvallar: {data['tables']}\n"
        f"Til: {data['language']}\nQo'shimcha: {extra}\n\n"
        f"Umumiy narx: <b>{format_som(price_som)} so'm</b>\n"
        f"({data['price_mpt']:.1f} MPT)"
    )
    await state.set_state(IndependentWork.confirm)
    await message.answer(text, parse_mode="HTML", reply_markup=confirm_order_kb())


@router.callback_query(IndependentWork.waiting_extra, F.data == "iw:skip_extra")
async def independent_extra_skipped(callback: CallbackQuery, state: FSMContext):
    await state.update_data(extra="O'tkazib yuborildi")
    data = await state.get_data()
    pages = data["pages"]
    title, rate = WORK_TYPES[data["work_type"]]
    extra_language_fee = 1_000 if data["language"] != "O'zbek" else 0
    price_som = (rate + extra_language_fee) * pages
    await state.update_data(price_som=price_som, price_mpt=price_som / MPT_PRICE_SOM)
    await callback.message.answer(
        f"📝 <b>{title}</b>\nMavzu: {data['topic']}\nSahifalar: {pages}\n"
        f"Umumiy narx: <b>{format_som(price_som)} so'm</b>",
        parse_mode="HTML",
        reply_markup=confirm_order_kb(),
    )
    await state.set_state(IndependentWork.confirm)
    await callback.answer()


@router.callback_query(IndependentWork.confirm, F.data == "order:cancel")
async def cancel_independent(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Buyurtma bekor qilindi.", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(IndependentWork.confirm, F.data == "order:confirm")
async def confirm_independent(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = callback.from_user.id
    price_mpt = data["price_mpt"]
    paid_with_mpt = await deduct_mpt_balance(user_id, price_mpt)
    order_id = await create_order({
        "telegram_id": user_id,
        "topic": data["topic"],
        "pages": data["pages"],
        "tariff": data["work_type"],
        "price_som": data["price_som"],
        "price_mpt": price_mpt,
        "full_name": callback.from_user.full_name,
        "institution": data["extra"],
        "direction": f"Rasm: {data['images']}; Grafik/jadval: {data['tables']}",
        "language": data["language"],
    })
    summary = (
        f"🆕 Yangi buyurtma №{order_id}\n"
        f"USER_ID: {user_id}\n"
        f"Username: @{callback.from_user.username or '-'}\n"
        f"Ish turi: {WORK_TYPES[data['work_type']][0]}\n"
        f"Mavzu: {data['topic']}\nSahifalar: {data['pages']}\n"
        f"Til: {data['language']}\nNarx: {format_som(data['price_som'])} so'm\n"
        f"Holat: {'MPT bilan tolandi' if paid_with_mpt else 'Tolov kutilmoqda'}"
    )
    if paid_with_mpt:
        await bot.send_message(ORDER_GROUP_ID, summary, reply_markup=admin_order_kb(order_id))
        await callback.message.answer(
            f"✅ Buyurtma №{order_id} qabul qilindi. Ish hajmiga qarab 1–5 soat ichida tayyorlanadi.",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
    else:
        await callback.message.answer(
            f"Buyurtma №{order_id} saqlandi. To'lov usulini tanlang:",
            reply_markup=None,
        )
        await ask_payment_method(callback.message, state, "order", data["price_som"], str(order_id))
        await bot.send_message(ORDER_GROUP_ID, summary, reply_markup=admin_order_kb(order_id))
    await callback.answer()
