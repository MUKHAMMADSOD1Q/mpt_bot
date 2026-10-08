from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import SOFF_PAGE_SIZE, SOFF_SELLER_PAGE_URL
from bot.i18n import menu_labels
from bot.database import list_ready_products
from bot.services.soff_client import fetch_seller_products

router = Router()


class SoffSearch(StatesGroup):
    waiting_query = State()


async def _load_products(search: str | None) -> list[dict]:
    """Avval soff.uz dan jonli ro'yxat; bo'lmasa eski bazadan import qilingan zaxira ro'yxat."""
    items = await fetch_seller_products(search=search)
    if items:
        return items
    fallback = await list_ready_products()
    items = [{"name": p["productname"], "price": "", "url": p["product_url"]} for p in fallback]
    if search:
        q = search.lower()
        items = [i for i in items if q in i["name"].lower()]
    return items


async def _render_page(page: int, search: str | None = None):
    products = await _load_products(search)
    if not products:
        text = "Mahsulot topilmadi." if search else "Hozircha mahsulotlar ro'yxatini yuklab bo'lmadi. Birozdan so'ng urinib ko'ring."
        builder = InlineKeyboardBuilder()
        builder.button(text="🌐 Sotuvchi sahifasini ochish", url=SOFF_SELLER_PAGE_URL)
        return text, builder.as_markup()

    start = (page - 1) * SOFF_PAGE_SIZE
    end = start + SOFF_PAGE_SIZE
    items = products[start:end]
    total_pages = (len(products) + SOFF_PAGE_SIZE - 1) // SOFF_PAGE_SIZE

    builder = InlineKeyboardBuilder()
    lines = []
    for i, p in enumerate(items, start=start + 1):
        price = f" — {p['price']}" if p.get("price") else ""
        lines.append(f"{i}. {p['name']}{price}")
        builder.button(text=f"{i}. {p['name'][:45]}", url=p["url"])
    builder.adjust(1)

    nav = InlineKeyboardBuilder()
    if start > 0:
        nav.button(text="⬅️ Oldingi", callback_data=f"soff:page:{page - 1}")
    nav.button(text="🔎 Qidirish", callback_data="soff:search")
    if end < len(products):
        nav.button(text="Keyingi ➡️", callback_data=f"soff:page:{page + 1}")
    nav.adjust(3)
    builder.attach(nav)

    title = "🛍 Tayyor mahsulotlar" + (f" (“{search}” bo'yicha)" if search else "")
    text = f"{title} — {page}/{total_pages}-sahifa\n\nMahsulot ustiga bosing — soff.uz da sotib olish sahifasi ochiladi:\n\n" + "\n".join(lines)
    return text, builder.as_markup()


@router.message(F.text.in_(menu_labels("products")))
async def products_entry(message: Message, state: FSMContext):
    await state.clear()
    text, kb = await _render_page(1)
    await message.answer(text, reply_markup=kb, disable_web_page_preview=True)


@router.callback_query(F.data.startswith("soff:page:"))
async def products_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[-1])
    data = await state.get_data()
    text, kb = await _render_page(page, search=data.get("soff_search"))
    await callback.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data == "soff:search")
async def ask_search_query(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SoffSearch.waiting_query)
    await callback.message.answer("Qidirish uchun mahsulot nomidan bir necha so'z yozing:")
    await callback.answer()


@router.message(SoffSearch.waiting_query)
async def do_search(message: Message, state: FSMContext):
    query = (message.text or "").strip()
    await state.clear()
    await state.update_data(soff_search=query)
    text, kb = await _render_page(1, search=query)
    await message.answer(text, reply_markup=kb, disable_web_page_preview=True)
