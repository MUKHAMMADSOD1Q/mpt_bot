"""
Taqdimot/referat matn kontentini AI orqali generatsiya qilish.

Nega DeepSeek? — 2026-yil holatiga ko'ra token narxi bo'yicha bozordagi eng
arzon "production darajasidagi" modellardan biri (deepseek-chat, ~$0.14/$0.28
har 1M token uchun kirish/chiqish narxi — bu 1000ta taqdimot uchun ham juda
kichik xarajat bo'ladi). API OpenAI formatiga mos (https://api-docs.deepseek.com),
shuning uchun kodni keyinchalik boshqa OpenAI-mos providerga (masalan Gemini,
yoki hatto keyinchalik Claude) almashtirish oson.

GEMINI_API_KEY sozlangan bo'lsa-yu DEEPSEEK_API_KEY sozlanmagan bo'lsa,
boshlang'ich bosqichda Gemini'ning BEPUL tarifidan matn uchun ham
foydalanishingiz mumkin — buni xohlasangiz ayting, shu faylga
generate_via_gemini() funksiyasini qo'shib beraman.

Narxlar va limitlar tez-tez o'zgaradi — https://api-docs.deepseek.com/quick_start/pricing
sahifasidan joriy narxni albatta tekshirib turing.
"""

import logging
import aiohttp

from bot.config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL

logger = logging.getLogger(__name__)

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


async def generate_slide_text(topic: str, slide_number: int, total_slides: int) -> str:
    """Bitta slayd uchun qisqa, mazmunli matn qaytaradi.
    DEEPSEEK_API_KEY sozlanmagan bo'lsa, oddiy namuna matn qaytaradi (bot ishlayveradi)."""
    if not DEEPSEEK_API_KEY:
        return f"{topic} — {slide_number}-band ({slide_number}/{total_slides})"

    prompt = (
        f"\"{topic}\" mavzusidagi taqdimotning {slide_number}-slaydi (jami {total_slides} slayd) uchun "
        "o'zbek tilida, 3-5 ta qisqa va aniq band (bullet point) yoz. Sarlavha yozma, faqat bandlarni yoz. "
        "Har bir band bitta qatorda, ortiqcha izohsiz."
    )
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception:
        logger.exception("DeepSeek so'rovida xatolik")
        return f"{topic} — {slide_number}-band"
