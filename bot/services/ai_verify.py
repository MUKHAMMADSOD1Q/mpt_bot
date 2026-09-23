"""
To'lov chekini (skrinshot/PDF) AI orqali tekshirish.

Nega Gemini? — Google AI Studio'da BEPUL API kalit olish mumkin
(https://aistudio.google.com/apikey), rasm va PDF'ni to'g'ridan-to'g'ri
tushunadi (vision), va bepul kvotasi kichik-o'rta hajmdagi botlar uchun
yetarli. Google https://ai.google.dev/gemini-api/docs sahifasida joriy
model nomlari va bepul limitlarni yangilab turadi — shuni tekshirib turing,
chunki model nomlari va limitlar vaqti-vaqti bilan o'zgaradi.

Agar GEMINI_API_KEY sozlanmagan bo'lsa, bu funksiya "AI mavjud emas" deb
javob qaytaradi va chek har doim admin tomonidan qo'lda tekshiriladi —
bot buzilmaydi, faqat avtomatik tekshirish o'chiq turadi.
"""

import base64
import json
import logging

import aiohttp

from bot.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

GEMINI_URL_TMPL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

PROMPT_TEMPLATE = """Sen to'lov chekini (bank/karta orqali pul o'tkazma skrinshoti yoki PDF) tekshiruvchi yordamchisan.
Quyidagi rasm/hujjatdan: to'lov summasini, sana va vaqtni, va agar ko'rinsa qabul qiluvchi karta raqamining oxirgi 4 raqamini top.

Kutilayotgan to'lov ma'lumotlari:
- Kutilgan summa: {expected_amount} so'm
- To'lov bugundan {max_age_hours} soat oldin qilingan bo'lishi kerak (eskirmagan bo'lsin)

FAQAT quyidagi JSON formatida javob ber, boshqa hech narsa yozma:
{{
  "extracted_amount": <topilgan summa, raqam, agar topa olmasang null>,
  "extracted_datetime": "<topilgan sana va vaqt, matn ko'rinishida, topa olmasang null>",
  "looks_like_real_receipt": <true yoki false — bu haqiqatan ham to'lov cheki/skrinshotimi>,
  "amount_matches": <true yoki false — summa kutilganga mos keladimi (kichik farqlarga ruxsat bering)>,
  "verdict": "<'haqiqiy' yoki 'shubhali' yoki 'soxta_yoki_notogri'>",
  "reason": "<qisqa izoh, o'zbek tilida>"
}}
"""


async def verify_receipt(file_bytes: bytes, mime_type: str, expected_amount: float, max_age_hours: int = 48) -> dict:
    if not GEMINI_API_KEY:
        return {"available": False, "verdict": "ai_yoq", "reason": "GEMINI_API_KEY sozlanmagan — admin qo'lda tekshiradi."}

    prompt = PROMPT_TEMPLATE.format(expected_amount=expected_amount, max_age_hours=max_age_hours)
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(file_bytes).decode()}},
            ]
        }]
    }
    url = GEMINI_URL_TMPL.format(model=GEMINI_MODEL, key=GEMINI_API_KEY)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.json()
    except Exception as e:
        logger.exception("Gemini so'rovida xatolik")
        return {"available": True, "verdict": "xatolik", "reason": f"AI so'roviga xatolik: {e}"}

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(text)
        parsed["available"] = True
        return parsed
    except Exception:
        logger.warning("Gemini javobini JSON sifatida o'qib bo'lmadi: %s", data)
        return {"available": True, "verdict": "xatolik", "reason": "AI javobini o'qib bo'lmadi, admin qo'lda tekshirsin."}
