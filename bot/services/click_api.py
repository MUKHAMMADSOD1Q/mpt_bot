"""
CLICK Merchant API bilan ishlash uchun klient.

Bu yerda "Invoice" usuli qo'llanilgan: bot foydalanuvchi telefon raqamiga
to'lov so'rovi (invoice) yuboradi, foydalanuvchi buni o'z Click ilovasida
tasdiqlaydi, bot esa holatni GET so'rov orqali tekshiradi (polling).

MUHIM: bu usulning afzalligi — hech qanday ochiq (public) HTTPS server yoki
webhook talab qilinmaydi, shuning uchun oddiy polling-bot (Railway/Render
worker) uchun eng mos usul.

Agar kelajakda "Prepare/Complete" (real-time webhook) usuliga o'tmoqchi
bo'lsangiz, bunga alohida web-server (FastAPI/aiohttp) va ochiq domen kerak
bo'ladi — README.md faylining "Keyingi qadamlar" bo'limiga qarang.

Rasmiy hujjat: https://docs.click.uz/en/merchant-api-request/
"""

import hashlib
import time
import logging

import aiohttp

from bot.config import (
    CLICK_SERVICE_ID, CLICK_MERCHANT_USER_ID, CLICK_SECRET_KEY,
)

API_BASE = "https://api.click.uz/v2/merchant"
logger = logging.getLogger(__name__)


class ClickAPIError(Exception):
    pass


def _auth_header() -> str:
    timestamp = str(int(time.time()))
    digest = hashlib.sha1((timestamp + CLICK_SECRET_KEY).encode("utf-8")).hexdigest()
    return f"{CLICK_MERCHANT_USER_ID}:{digest}:{timestamp}"


def _headers() -> dict:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Auth": _auth_header(),
    }


async def create_invoice(amount_som: float, phone_number: str, merchant_trans_id: str) -> dict:
    """
    Foydalanuvchi telefon raqamiga to'lov so'rovi (invoice) yaratadi.

    phone_number format: 998901234567 (kod bilan, + belgisisiz)
    merchant_trans_id: sizning tizimingizdagi noyob buyurtma/to'lov identifikatori
                        (masalan "order-15" yoki "topup-<telegram_id>-<timestamp>")

    Qaytaradi: {"error_code": 0, "error_note": "...", "invoice_id": 1234567}
    error_code == 0 bo'lsa — muvaffaqiyatli yaratilgan.
    """
    payload = {
        "service_id": int(CLICK_SERVICE_ID),
        "amount": amount_som,
        "phone_number": phone_number,
        "merchant_trans_id": merchant_trans_id,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE}/invoice/create", json=payload, headers=_headers()) as resp:
            data = await resp.json()
            logger.info("Click invoice/create -> %s", data)
            return data


async def check_invoice_status(invoice_id: int) -> dict:
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE}/invoice/status/{CLICK_SERVICE_ID}/{invoice_id}"
        async with session.get(url, headers=_headers()) as resp:
            data = await resp.json()
            logger.info("Click invoice/status -> %s", data)
            return data


async def check_payment_status_by_mti(merchant_trans_id: str) -> dict:
    """
    merchant_trans_id orqali to'lov holatini tekshiradi — invoice_id'ni saqlab
    yurishning hojati yo'q, shuning uchun bot tomonida qulayroq.

    Qaytaradi (muvaffaqiyatli to'lovda): {"error_code": 0, "payment_id": ..., "merchant_trans_id": "..."}
    Hali to'lanmagan yoki topilmagan bo'lsa error_code manfiy bo'ladi.

    DIQQAT: Click hujjatlarida payment_status kodlarining to'liq jadvali ochiq
    berilmagan. Amalda ko'plab integratsiyalarda payment_status == 2 "to'landi"
    ma'nosini bildiradi, lekin buni albatta o'zingizning test to'lovingiz bilan
    tekshirib ko'ring (merchant.click.uz kabinetida yoki Click texnik yordamidan
    so'rab) va kerak bo'lsa quyidagi PAID_STATUS qiymatini moslashtiring.
    """
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE}/payment/status_by_mti/{CLICK_SERVICE_ID}/{merchant_trans_id}"
        async with session.get(url, headers=_headers()) as resp:
            data = await resp.json()
            logger.info("Click payment/status_by_mti -> %s", data)
            return data


# Amalda ko'p uchraydigan "to'landi" kodi — o'z sinovingizdan so'ng tasdiqlang/o'zgartiring.
PAID_STATUS = 2


def is_paid(status_response: dict) -> bool:
    return (
        status_response.get("error_code") == 0
        and status_response.get("payment_status") == PAID_STATUS
    )
