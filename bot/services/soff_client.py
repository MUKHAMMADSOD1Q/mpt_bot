"""
soff.uz - sizning sotuvchi sahifangizdagi (https://soff.uz/seller/879) mahsulotlar
ro'yxatini botga olib kelish uchun modul.

MUHIM CHEKLOV: soff.uz sayti Next.js'da qurilgan va sahifa mazmuni ko'p hollarda
JavaScript orqali (client-side) yuklanadi — bu degani, oddiy HTML so'rovi orqali
mahsulotlar ro'yxatini har doim ham to'g'ridan-to'g'ri olib bo'lmasligi mumkin.

Bu modul ikkita usulni sinab ko'radi:
1. Sahifa HTML'i ichidagi maxsus <script id="__NEXT_DATA__"> tegini o'qib,
   undagi tayyor JSON ma'lumotni olish (bu Next.js saytlarda mashhur "server-side
   render" holatida ishlaydigan usul).
2. Agar bu ishlamasa — pastdagi DEBUG bo'limidan foydalanib, siz brauzeringizning
   Developer Tools > Network > Fetch/XHR bo'limida "products" so'zi bilan bog'liq
   so'rovni topib, uning to'liq URL manzilini menga (yoki shu faylga) yuboring —
   men (yoki siz) kodni shu haqiqiy API'ga moslashtiramiz. Bu eng ishonchli yo'l.

Hozircha bu funksiyalar ishlamasa ham bot yiqilmaydi — foydalanuvchiga
"Mahsulotlar ro'yxatini yuklab bo'lmadi" deb ko'rsatiladi va siz bilan birga
haqiqiy API manzilini aniqlab, shu faylni yangilaymiz.
"""

import json
import re
import time
import logging

import aiohttp

from bot.config import SOFF_SELLER_ID

logger = logging.getLogger(__name__)

SELLER_PAGE_URL = f"https://soff.uz/seller/{SOFF_SELLER_ID}"
PRODUCT_URL_TMPL = "https://soff.uz/product/{slug}"  # eski bazadagi havolalardan aniqlangan format
_CACHE: dict = {"ts": 0.0, "items": []}
_CACHE_TTL = 300  # soniya

_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL
)


async def _fetch_html(url: str) -> str:
    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            return await resp.text()


def _extract_next_data(html: str) -> dict | None:
    match = _NEXT_DATA_RE.search(html)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        logger.warning("__NEXT_DATA__ JSON sifatida o'qilmadi")
        return None


def _find_product_list(obj, min_items: int = 3):
    """__NEXT_DATA__ ichidan mahsulotlarga o'xshash ro'yxatni qidiradi (heuristika).
    Har bir element "name"/"title" va "price"/"cost" kabi kalitlarga ega bo'lsa,
    mahsulot ro'yxati deb hisoblanadi."""
    found = []

    def walk(node):
        if isinstance(node, list) and len(node) >= min_items:
            sample = node[0]
            if isinstance(sample, dict):
                keys = {k.lower() for k in sample.keys()}
                if keys & {"name", "title"} and keys & {"price", "cost", "amount"}:
                    found.append(node)
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(obj)
    return found[0] if found else None


async def fetch_seller_products(page: int = 1, search: str | None = None) -> list[dict]:
    """
    Sahifadagi mahsulotlarni qaytaradi. Har bir element (best-effort):
    {"name": str, "price": str/number, "url": str|None, "image": str|None}

    Agar hech narsa topilmasa — bo'sh ro'yxat qaytaradi (xato tashlamaydi),
    shunda bot foydalanuvchiga "hozircha mavjud emas" deb ko'rsata oladi.
    """
    if _CACHE["items"] and time.time() - _CACHE["ts"] < _CACHE_TTL:
        return _filter(_CACHE["items"], search)

    try:
        html = await _fetch_html(SELLER_PAGE_URL)
    except Exception:
        logger.exception("soff.uz sahifasini yuklab bo'lmadi")
        return []

    data = _extract_next_data(html)
    if not data:
        return []

    raw_list = _find_product_list(data)
    if not raw_list:
        return []

    products = []
    for item in raw_list:
        name = item.get("name") or item.get("title") or "Nomsiz mahsulot"
        slug = item.get("slug") or item.get("id")
        url = PRODUCT_URL_TMPL.format(slug=slug) if isinstance(slug, str) and not slug.isdigit() else SELLER_PAGE_URL
        products.append({
            "name": str(name),
            "price": item.get("price") or item.get("cost") or item.get("amount") or "",
            "url": url,
        })
    _CACHE["ts"], _CACHE["items"] = time.time(), products
    return _filter(products, search)


def _filter(products: list[dict], search: str | None) -> list[dict]:
    if not search:
        return products
    q = search.lower()
    return [p for p in products if q in p["name"].lower()]
