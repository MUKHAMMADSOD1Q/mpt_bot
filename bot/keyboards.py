from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import TARIFFS, SUBSCRIPTIONS, INDEPENDENT_WORK_TYPES, WORK_LANGUAGES, WEBSITE_STYLE_PRICES


def admin_menu_kb(super_admin: bool = False) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🧾 Kutayotgan buyurtmalar")],
        [KeyboardButton(text="👥 Foydalanuvchilar ma'lumoti")],
        [KeyboardButton(text="👤 Foydalanuvchiga xabar"), KeyboardButton(text="📢 Barchaga xabar")],
        [KeyboardButton(text="🛍 Soff.uz'ga yuklash")],
    ]
    if super_admin:
        kb.append([KeyboardButton(text="👥 Adminlarni boshqarish")])
    kb.extend([
        [KeyboardButton(text="⬅️ Ortga")],
        [KeyboardButton(text="🔙 Oddiy rejimga qaytish")],
    ])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def main_menu_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📊 Taqdimotga buyurtma berish")],
        [KeyboardButton(text="📝 Mustaqil ishlarga buyurtma berish")],
        [KeyboardButton(text="🏢 Tadbirkorlar uchun")],
        [KeyboardButton(text="🛍 Tayyor mahsulotlar")],
        [KeyboardButton(text="🤖 Sun'iy intellekt yordamida")],
        [KeyboardButton(text="🎮 O'yin va ko'ngil ochish")],
        [KeyboardButton(text="💳 Balans va obuna")],
        [KeyboardButton(text="📖 Foydalanish qo'llanmasi")],
        [KeyboardButton(text="ℹ️ Admin bilan bog'lanish")],
        [KeyboardButton(text="⬅️ Ortga")],
        [KeyboardButton(text="🤝 Biz haqimizda")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def contact_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👑 Bot asoschisi va PreUz bosh direktori: Muhammadsodiq", url="https://t.me/MUKHAMMADSODlQ")
    builder.button(text="👤 Ikkinchi akkaunt: Muhammadsodiq Nigmatov", url="https://t.me/MUHAMMADS0DlQ")
    builder.button(text="🧑\u200d💼 Admin1", url="https://t.me/preuzadmin")
    builder.adjust(1)
    return builder.as_markup()


def games_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🧞 Akinator", url="https://en.akinator.com/")
    builder.button(text="🌆 Floor796", url="https://floor796.com/")
    builder.adjust(1)
    return builder.as_markup()


def presentation_entry_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Buyurtma berish", callback_data="pres:order")
    builder.button(text="🧮 PreCal — narxni hisoblash", callback_data="pres:precal")
    builder.adjust(1)
    return builder.as_markup()


def precal_tariff_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, t in TARIFFS.items():
        label = "Bepul" if key == "bepul" else f"{t['title']} — {t['som']:,} so'm/sahifa".replace(",", ".")
        builder.button(text=label, callback_data=f"precal_t:{key}")
    builder.adjust(1)
    return builder.as_markup()


def precal_approve_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ma'qul, buyurtma beraman", callback_data="precal_ok")
    builder.button(text="💸 Arzonroq ta'riflarni ko'rsat", callback_data="precal_cheaper")
    builder.adjust(1)
    return builder.as_markup()


def business_services_kb() -> InlineKeyboardMarkup:
    items = [
        ("💌 Taklifnoma", "biz:taklifnoma"),
        ("🎨 UI dizayn", "biz:ui"),
        ("🌐 Web-sayt", "biz:web"),
        ("📄 Rezyume", "biz:rezyume"),
        ("📺 YouTube banner", "biz:youtube"),
        ("🖼 Logo", "biz:logo"),
        ("🔗 QR-generator", "biz:qr"),
    ]
    builder = InlineKeyboardBuilder()
    for text, cb in items:
        builder.button(text=text, callback_data=cb)
    builder.adjust(2)
    return builder.as_markup()


def independent_work_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, info in INDEPENDENT_WORK_TYPES.items():
        builder.button(text=info["title"], callback_data=f"iw_type:{key}")
    builder.adjust(1)
    return builder.as_markup()


def yes_no_kb(prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha", callback_data=f"{prefix}:ha")
    builder.button(text="❌ Yo'q", callback_data=f"{prefix}:yoq")
    builder.adjust(2)
    return builder.as_markup()


def language_choice_kb(prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for lang in WORK_LANGUAGES:
        builder.button(text=lang, callback_data=f"{prefix}:{lang}")
    builder.adjust(2)
    return builder.as_markup()


def ui_platform_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, cb in [("📱 Mobil ilova", "ui_platform:mobil"), ("💻 Veb-sayt", "ui_platform:veb"),
                       ("🤖 Telegram Web-App", "ui_platform:tgwebapp")]:
        builder.button(text=label, callback_data=cb)
    builder.adjust(1)
    return builder.as_markup()


def business_size_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, cb in [("🟢 Kichik", "biz_size:kichik"), ("🟡 O'rta", "biz_size:orta"), ("🔴 Katta", "biz_size:katta")]:
        builder.button(text=label, callback_data=cb)
    builder.adjust(3)
    return builder.as_markup()


def website_style_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    labels = {"minimalizm": "Minimalizm", "zamonaviy": "Zamonaviy", "hi-tech": "Hi-Tech", "3d": "3D", "boshqa": "Boshqa"}
    for key in WEBSITE_STYLE_PRICES:
        builder.button(text=labels.get(key, key), callback_data=f"web_style:{key}")
    builder.adjust(2)
    return builder.as_markup()


def skip_or_upload_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Rasmsiz davom etish", callback_data="skip")
    return builder.as_markup()


def tariff_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, t in TARIFFS.items():
        label = "Bepul" if key == "bepul" else f"{t['title']} — {t['mpt']} MPT / {t['som']:,} so'm".replace(",", ".")
        builder.button(text=label, callback_data=f"tariff:{key}")
    builder.adjust(1)
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
    for amount in (100, 250, 500, 1000):
        builder.button(text=f"{amount} MPT", callback_data=f"buympt:{amount}")
    builder.adjust(2)
    return builder.as_markup()


def click_check_kb(merchant_trans_id: str, pay_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 To'lash (Click)", url=pay_url)
    builder.button(text="🔄 To'lovni tekshirish", callback_data=f"clickcheck:{merchant_trans_id}")
    builder.adjust(1)
    return builder.as_markup()


def click_app_choice_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, bor", callback_data="clickapp:yes")
    builder.button(text="❌ Yo'q, link yuboring", callback_data="clickapp:no")
    builder.adjust(1)
    return builder.as_markup()


def click_phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamimni ulashish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def click_wait_kb(merchant_trans_id: str, pay_url: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if pay_url:
        builder.button(text="🔗 Click orqali to'lash", url=pay_url)
    builder.button(text="🔄 To'lovni tekshirish", callback_data=f"clickcheck:{merchant_trans_id}")
    builder.button(text="🎮 Kutish vaqtida o'yin", callback_data=f"clickgame:start:{merchant_trans_id}")
    builder.adjust(1)
    return builder.as_markup()


def click_game_answers_kb(options: list[int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for option in options:
        builder.button(text=str(option), callback_data=f"clickgame:answer:{option}")
    builder.adjust(2)
    return builder.as_markup()


def click_game_done_kb(merchant_trans_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 To'lovni tekshirish", callback_data=f"clickcheck:{merchant_trans_id}")
    builder.button(text="👨‍💼 Admin bilan aloqa", url="https://t.me/preuzadmin")
    builder.adjust(1)
    return builder.as_markup()


def card_timeout_kb(payment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Yana 5 daqiqa", callback_data=f"cardextend:{payment_id}")
    builder.button(text="❌ Bekor qilish", callback_data=f"cardgiveup:{payment_id}")
    builder.adjust(2)
    return builder.as_markup()


def card_cancel_kb(payment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data=f"cardgiveup:{payment_id}")
    return builder.as_markup()


def setprice_kb(service_order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Narx belgilash", callback_data=f"svc_setprice:{service_order_id}")
    return builder.as_markup()
