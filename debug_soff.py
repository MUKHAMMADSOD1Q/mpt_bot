"""
Bir martalik debug skripti — soff.uz sahifasidagi haqiqiy ma'lumot tuzilishini
aniqlash uchun. Terminalda ishga tushiring:

    python debug_soff.py

Natijada 2 ta fayl hosil bo'ladi:
    soff_debug.html      — sahifaning to'liq HTML kodi
    soff_debug_next.json — agar __NEXT_DATA__ topilsa, uning tarkibi

Agar soff_debug_next.json fayli hosil bo'lsa va ichida mahsulotlar (nom, narx,
rasm) ko'rinsa — bot/services/soff_client.py avtomatik ishlaydi.

Agar hosil bo'lmasa: brauzeringizda https://soff.uz/seller/879 sahifasini oching,
F12 (Developer Tools) > Network > Fetch/XHR bo'limini oching, sahifani yangilang
yoki "Mahsulotlar" bo'limidagi "Barchasini ko'rish"ni bosing, ro'yxatida paydo
bo'lgan so'rovlardan mahsulotlar JSON qaytaradiganini toping va uning to'liq
URL manzilini (Request URL) menga yuboring — men shu asosda kodni yangilayman.
"""
import asyncio
import json

from bot.services.soff_client import _fetch_html, _extract_next_data, SELLER_PAGE_URL


async def main():
    print(f"Yuklanmoqda: {SELLER_PAGE_URL}")
    html = await _fetch_html(SELLER_PAGE_URL)
    with open("soff_debug.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML saqlandi: soff_debug.html ({len(html)} belgi)")

    data = _extract_next_data(html)
    if data:
        with open("soff_debug_next.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("__NEXT_DATA__ topildi va saqlandi: soff_debug_next.json")
    else:
        print("__NEXT_DATA__ TOPILMADI — ma'lumot JavaScript orqali dinamik yuklanayotgan bo'lishi mumkin.")
        print("Yuqoridagi ko'rsatmaga muvofiq brauzer orqali API manzilini toping.")


if __name__ == "__main__":
    asyncio.run(main())
