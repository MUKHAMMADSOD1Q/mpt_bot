from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import SOFF_PAGE_SIZE
from bot.services.soff_client import fetch_seller_products

router = Router()


class SoffSearch(StatesGroup):
    waiting_query = State()


def _products_page_kb(page: int, has_prev: bool, has_next: bool, product_count: int = 0):
    builder = InlineKeyboardBuilder()
    if has_prev:
        builder.button(text="⬅️ Oldingi", callback_data=f"soff:page:{page - 1}")
    builder.button(text="🔎 Qidirish", callback_data="soff:search")
    if has_next:
        builder.button(text="Keyingi ➡️", callback_data=f"soff:page:{page + 1}")
    if product_count:
        for i in range(min(product_count, 3)):
            builder.button(text=f"{i + 1}", callback_data=f"soff:item:{i}")
    builder.adjust(3)
    return builder.as_markup()


async def _render_page(page: int, search: str | None = None) -> tuple[str, object]:
    all_products = await fetch_seller_products(search=search)

    if not all_products:
        builder = InlineKeyboardBuilder()
        builder.button(text="🛍 Soff.uz do'konini ochish", url="https://soff.uz/seller/879")
        builder.button(text="⚙️ Sotuvchi paneli", url="https://seller.soff.uz/seller/products")
        builder.adjust(1)
        return (
            "Tayyor mahsulotlar ro'yxatini Soff.uz do'konidan oching:",
            builder.as_markup(),
        )

    start = (page - 1) * SOFF_PAGE_SIZE
    end = start + SOFF_PAGE_SIZE
    page_items = all_products[start:end]

    if not page_items:
        return "Bu sahifada mahsulot topilmadi.", None

    lines = []
    for i, p in enumerate(page_items, start=start + 1):
        lines.append(f"{i}. <b>{p['name']}</b> — {p['price']}")
    header = f"🛍 Tayyor mahsulotlar" + (f" (\"{search}\" bo'yicha qidiruv)" if search else "") + f" — {page}-sahifa\n\n"

    builder = InlineKeyboardBuilder()
    for i, product in enumerate(page_items):
        builder.button(
            text=f"📦 {i + 1}. {product['name'][:28]}",
            url=product.get("url") or "https://soff.uz/seller/879",
        )
    if has_prev := start > 0:
        builder.button(text="⬅️ Oldingi", callback_data=f"soff:page:{page - 1}")
    builder.button(text="🔎 Qidirish", callback_data="soff:search")
    if end < len(all_products):
        builder.button(text="Keyingi ➡️", callback_data=f"soff:page:{page + 1}")
    builder.adjust(3)
    # keep at least 3 buttons per row for nav and product quick access
    kb = builder.as_markup()
    return header + "\n".join(lines), kb


@router.message(F.text == "🛍 Tayyor mahsulotlar")
async def products_entry(message: Message, state: FSMContext):
    await state.update_data(soff_search=None)
    text, kb = await _render_page(1)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("soff:page:"))
async def products_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[-1])
    data = await state.get_data()
    text, kb = await _render_page(page, search=data.get("soff_search"))
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("soff:item:"))
async def product_details(callback: CallbackQuery):
    product_index = int(callback.data.split(":")[-1])
    products = await fetch_seller_products()
    if product_index < 0 or product_index >= len(products):
        await callback.answer("Mahsulot topilmadi.", show_alert=True)
        return
    product = products[product_index]
    url = product.get("url") or "https://soff.uz/seller/879"
    await callback.message.answer(
        f"🛍 {product.get('name', 'Mahsulot')}\n\n"
        f"💰 Narx: {product.get('price', '-')}\n\n"
        f"🔗 Sotib olish uchun: {url}",
        disable_web_page_preview=False,
    )
    await callback.answer()


@router.callback_query(F.data == "soff:search")
async def ask_search_query(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SoffSearch.waiting_query)
    await callback.message.answer("Qidirish uchun mahsulot nomidan bir necha so'z yozing:")
    await callback.answer()


@router.message(SoffSearch.waiting_query)
async def do_search(message: Message, state: FSMContext):
    query = message.text.strip()
    await state.update_data(soff_search=query)
    await state.set_state(None)
    text, kb = await _render_page(1, search=query)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)
