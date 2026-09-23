from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import TARIFFS, SUBSCRIPTIONS


def admin_menu_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🧾 Kutayotgan buyurtmalar")],
        [KeyboardButton(text="👤 Foydalanuvchiga xabar"), KeyboardButton(text="📢 Barchaga xabar")],
        [KeyboardButton(text="🛍 Soff.uz'ga yuklash")],
        [KeyboardButton(text="🔙 Oddiy rejimga qaytish")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def main_menu_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📊 Taqdimotga buyurtma berish")],
        [KeyboardButton(text="📝 Mustaqil ishlarga buyurtma berish")],
        [KeyboardButton(text="🧾 Tadbirkorlar uchun")],
        [KeyboardButton(text="🛍 Tayyor mahsulotlar")],
        [KeyboardButton(text="🎮 O'yin va ko'ngil ochish")],
        [KeyboardButton(text="📘 Foydalanish qo'llanmasi")],
        [KeyboardButton(text="🤖 Sun'iy intellekt yordamida")],
        [KeyboardButton(text="💳 Balans va obuna")],
        [KeyboardButton(text="ℹ️ Admin bilan bog'lanish")],
        [KeyboardButton(text="ℹ️ Biz haqimizda")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def other_services_kb() -> InlineKeyboardMarkup:
    services = [
        "Taklifnoma",
        "UI dizayn",
        "Web-sayt",
        "Rezyume",
        "YouTube banner",
        "Logo",
        "QR-generator",
        "Tadbirkorlar uchun",
    ]
    builder = InlineKeyboardBuilder()
    for s in services:
        builder.button(text=s, callback_data=f"other_service:{s}")
    builder.adjust(2)
    return builder.as_markup()


def games_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎩 Akinator", url="https://en.akinator.com/")
    builder.button(text="🏢 Floor796", url="https://floor796.com/")
    builder.adjust(1)
    return builder.as_markup()


def tariff_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, t in TARIFFS.items():
        label = "Bepul" if key == "bepul" else f"{t['title']} — {t['mpt']} MPT / {t['som']:,} so'm".replace(",", ".")
        builder.button(text=label, callback_data=f"tariff:{key}")
    builder.adjust(1)
    return builder.as_markup()


def confirm_order_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Generate", callback_data="order:confirm")
    builder.button(text="❌ Bekor qilish", callback_data="order:cancel")
    builder.adjust(2)
    return builder.as_markup()


def subscription_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, s in SUBSCRIPTIONS.items():
        builder.button(text=f"{s['title']} — {s['som']:,} so'm".replace(",", "."), callback_data=f"sub:{key}")
    builder.adjust(1)
    return builder.as_markup()


def skip_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ O'tkazib yuborish", callback_data="skip")
    return builder.as_markup()


def mpt_topup_amounts_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for amount in (10, 30, 50, 100):
        builder.button(text=f"{amount} MPT", callback_data=f"buympt:{amount}")
    builder.adjust(2)
    return builder.as_markup()


def click_check_kb(merchant_trans_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 To'lovni tekshirish", callback_data=f"clickcheck:{merchant_trans_id}")
    return builder.as_markup()


def admin_order_kb(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Bajarildi", callback_data=f"admin_done:{order_id}")
    builder.button(text="❌ Rad etish", callback_data=f"admin_reject:{order_id}")
    builder.adjust(2)
    return builder.as_markup()
