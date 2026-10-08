from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import SOFF_PAGE_SIZE, SOFF_SELLER_PAGE_URL
from bot.i18n import menu_labels
from bot.i18n import tr
from bot.services.user_locale import get_user_locale
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


async def _render_page(page: int, search: str | None = None, language: str = "uz"):
    products = await _load_products(search)
    if not products:
        text = tr(language, "soff_not_found") if search else tr(language, "soff_unavailable")
        builder = InlineKeyboardBuilder()
        builder.button(text=tr(language, "soff_open_seller"), url=SOFF_SELLER_PAGE_URL)
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
        nav.button(text=tr(language, "soff_prev"), callback_data=f"soff:page:{page - 1}")
    nav.button(text=tr(language, "soff_search"), callback_data="soff:search")
    if end < len(products):
        nav.button(text=tr(language, "soff_next"), callback_data=f"soff:page:{page + 1}")
    nav.adjust(3)
    builder.attach(nav)

    title = tr(language, "soff_title") + (tr(language, "soff_search_title", query=search) if search else "")
    text = f"{title} — {page}/{total_pages}\n\n{tr(language, 'soff_instruction')}\n\n" + "\n".join(lines)
    return text, builder.as_markup()


@router.message(F.text.in_(menu_labels("products")))
async def products_entry(message: Message, state: FSMContext):
    await state.clear()
    language = await get_user_locale(message.from_user.id)
    text, kb = await _render_page(1, language=language)
    await message.answer(text, reply_markup=kb, disable_web_page_preview=True)


@router.callback_query(F.data.startswith("soff:page:"))
async def products_page(callback: CallbackQuery, state: FSMContext):
    language = await get_user_locale(callback.from_user.id)
    page = int(callback.data.split(":")[-1])
    data = await state.get_data()
    text, kb = await _render_page(page, search=data.get("soff_search"), language=language)
    await callback.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data == "soff:search")
async def ask_search_query(callback: CallbackQuery, state: FSMContext):
    language = await get_user_locale(callback.from_user.id)
    await state.set_state(SoffSearch.waiting_query)
    await callback.message.answer(tr(language, "soff_search_prompt"))
    await callback.answer()


@router.message(SoffSearch.waiting_query)
async def do_search(message: Message, state: FSMContext):
    language = await get_user_locale(message.from_user.id)
    query = (message.text or "").strip()
    await state.clear()
    await state.update_data(soff_search=query)
    text, kb = await _render_page(1, search=query, language=language)
    await message.answer(text, reply_markup=kb, disable_web_page_preview=True)
