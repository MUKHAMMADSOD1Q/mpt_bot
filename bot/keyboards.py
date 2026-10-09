from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import TARIFFS, SUBSCRIPTIONS, INDEPENDENT_WORK_TYPES, WORK_LANGUAGES, WEBSITE_STYLE_PRICES
from bot.i18n import SUPPORTED_LANGUAGES, tr


def admin_menu_kb(super_admin: bool = False) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🧾 Kutayotgan buyurtmalar")],
        [KeyboardButton(text="👥 Foydalanuvchilar ma'lumoti")],
        [KeyboardButton(text="👤 Foydalanuvchiga xabar"), KeyboardButton(text="📢 Barchaga xabar")],
        [KeyboardButton(text="🛍 Soff.uz'ga yuklash")],
    ]
    if super_admin:
        kb.append([KeyboardButton(text="👥 Adminlarni boshqarish")])
    kb.append([KeyboardButton(text="🔙 Oddiy rejimga qaytish")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def main_menu_kb(language: str = "uz") -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=tr(language, "menu_presentation"))],
        [KeyboardButton(text=tr(language, "menu_independent"))],
        [KeyboardButton(text=tr(language, "menu_business"))],
        [KeyboardButton(text=tr(language, "menu_products"))],
        [KeyboardButton(text=tr(language, "menu_ai"))],
        [KeyboardButton(text=tr(language, "menu_manual_presentation"))],
        [KeyboardButton(text=tr(language, "menu_games"))],
        [KeyboardButton(text=tr(language, "menu_balance"))],
        [KeyboardButton(text=tr(language, "menu_settings"))],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def back_only_kb(language: str = "uz") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=tr(language, "menu_back"))]],
        resize_keyboard=True,
    )


def _add_back_button(builder: InlineKeyboardBuilder, language: str) -> None:
    builder.button(text=tr(language, "menu_back"), callback_data="nav:back")


def contact_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    labels = {
        "uz": ["👑 Bot asoschisi va PreUz bosh direktori: Muhammadsodiq", "👤 Ikkinchi akkaunt: Muhammadsodiq Nigmatov", "🧑‍💼 Admin1"],
        "ru": ["👑 Основатель бота и директор PreUz: Мухаммадсодик", "👤 Второй аккаунт: Мухаммадсодик Нигматов", "🧑‍💼 Администратор 1"],
        "en": ["👑 Bot founder and PreUz CEO: Muhammadsodiq", "👤 Second account: Muhammadsodiq Nigmatov", "🧑‍💼 Admin 1"],
        "tg": ["👑 Асосгузори бот ва роҳбари PreUz: Muhammadsodiq", "👤 Ҳисоби дуюм: Muhammadsodiq Nigmatov", "🧑‍💼 Маъмур 1"],
        "kk": ["👑 Бот негізін қалаушы және PreUz басшысы: Muhammadsodiq", "👤 Екінші аккаунт: Muhammadsodiq Nigmatov", "🧑‍💼 Әкімші 1"],
        "ky": ["👑 Боттун негиздөөчүсү жана PreUz жетекчиси: Muhammadsodiq", "👤 Экинчи аккаунт: Muhammadsodiq Nigmatov", "🧑‍💼 Администратор 1"],
        "tk": ["👑 Boty esaslandyryjy we PreUz ýolbaşçysy: Muhammadsodiq", "👤 Ikinji hasap: Muhammadsodiq Nigmatov", "🧑‍💼 Administrator 1"],
    }
    for text, url in zip(labels.get(language, labels["uz"]), (
        "https://t.me/MUKHAMMADSODlQ", "https://t.me/MUHAMMADS0DlQ", "https://t.me/preuzadmin",
    )):
        builder.button(text=text, url=url)
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def admin_contact_prompt_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    text = {
        "uz": "👤 Admin bilan bog'lanish", "ru": "👤 Связаться с администратором",
        "en": "👤 Contact an admin", "tg": "👤 Тамос бо маъмур",
        "kk": "👤 Әкімшімен байланысу", "ky": "👤 Администратор менен байланышуу",
        "tk": "👤 Administrator bilen habarlaşmak",
    }.get(language, "👤 Admin bilan bog'lanish")
    builder.button(text=text, callback_data="show_admin_contacts")
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def settings_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for action, key in (
        ("guide", "settings_guide"),
        ("contact", "settings_contact"),
        ("about", "settings_about"),
        ("language", "settings_language"),
    ):
        builder.button(text=tr(language, key), callback_data=f"settings:{action}")
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def bot_language_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, label in SUPPORTED_LANGUAGES.items():
        builder.button(text=label, callback_data=f"botlang:{code}")
    _add_back_button(builder, language)
    builder.adjust(2)
    return builder.as_markup()


def manual_photo_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(language, "finish_photos"), callback_data="manual:finish_photos")
    builder.button(text=tr(language, "skip_photos"), callback_data="manual:skip_photos")
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def manual_review_kb(presentation_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr("uz", "manual_approve"), callback_data=f"manual:approve:{presentation_id}")
    builder.button(text=tr("uz", "manual_reject"), callback_data=f"manual:reject:{presentation_id}")
    builder.adjust(1)
    return builder.as_markup()


def games_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🧞 Akinator", url="https://en.akinator.com/")
    builder.button(text="🌆 Floor796", url="https://floor796.com/")
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def presentation_entry_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(language, "presentation_order"), callback_data="pres:order")
    builder.button(text=tr(language, "precal_button"), callback_data="pres:precal")
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def precal_tariff_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, t in TARIFFS.items():
        label = tr(language, f"tariff_{key}") + ("" if key == "bepul" else f" — {t['som']:,} UZS/page".replace(",", "."))
        builder.button(text=label, callback_data=f"precal_t:{key}")
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def precal_approve_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(language, "precal_ok"), callback_data="precal_ok")
    builder.button(text=tr(language, "precal_cheaper"), callback_data="precal_cheaper")
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def business_services_kb(language: str = "uz") -> InlineKeyboardMarkup:
    items = [
        (tr(language, "biz_invitation"), "biz:taklifnoma"),
        (tr(language, "biz_ui"), "biz:ui"),
        (tr(language, "biz_website"), "biz:web"),
        (tr(language, "biz_resume"), "biz:rezyume"),
        (tr(language, "biz_youtube"), "biz:youtube"),
        (tr(language, "biz_logo"), "biz:logo"),
        (tr(language, "biz_qr"), "biz:qr"),
    ]
    builder = InlineKeyboardBuilder()
    for text, cb in items:
        builder.button(text=text, callback_data=cb)
    _add_back_button(builder, language)
    builder.adjust(2)
    return builder.as_markup()


def independent_work_type_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, info in INDEPENDENT_WORK_TYPES.items():
        builder.button(text=tr(language, f"ind_type_{key}"), callback_data=f"iw_type:{key}")
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def yes_no_kb(prefix: str, language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(language, "yes"), callback_data=f"{prefix}:ha")
    builder.button(text=tr(language, "no"), callback_data=f"{prefix}:yoq")
    _add_back_button(builder, language)
    builder.adjust(2)
    return builder.as_markup()


def language_choice_kb(prefix: str, _ui_language: str = "uz") -> InlineKeyboardMarkup:
    language_flags = {
        "O'zbek": "🇺🇿",
        "Русский": "🇷🇺",
        "English": "🇬🇧",
        "Тоҷикӣ": "🇹🇯",
        "Қазақша": "🇰🇿",
        "Кыргызча": "🇰🇬",
        "Türkmençe": "🇹🇲",
    }
    builder = InlineKeyboardBuilder()
    for lang in WORK_LANGUAGES:
        builder.button(text=f"{language_flags[lang]} {lang}", callback_data=f"{prefix}:{lang}")
    _add_back_button(builder, _ui_language)
    builder.adjust(2)
    return builder.as_markup()


def ui_platform_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, cb in [("ui_mobile", "ui_platform:mobil"), ("ui_web", "ui_platform:veb"),
                    ("ui_tgwebapp", "ui_platform:tgwebapp")]:
        builder.button(text=tr(language, key), callback_data=cb)
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def business_size_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, cb in [("size_small", "biz_size:kichik"), ("size_medium", "biz_size:orta"), ("size_large", "biz_size:katta")]:
        builder.button(text=tr(language, key), callback_data=cb)
    _add_back_button(builder, language)
    builder.adjust(3)
    return builder.as_markup()


def website_style_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    labels = {"minimalizm": "style_minimal", "zamonaviy": "style_modern", "hi-tech": "style_hitech", "3d": "style_3d", "boshqa": "style_other"}
    for key in WEBSITE_STYLE_PRICES:
        builder.button(text=tr(language, labels.get(key, key)), callback_data=f"web_style:{key}")
    _add_back_button(builder, language)
    builder.adjust(2)
    return builder.as_markup()


def skip_or_upload_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(language, "skip_upload"), callback_data="skip")
    _add_back_button(builder, language)
    return builder.as_markup()


def tariff_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, t in TARIFFS.items():
        label = tr(language, f"tariff_{key}") + ("" if key == "bepul" else f" — {t['mpt']} MPT / {t['som']:,} UZS".replace(",", "."))
        builder.button(text=label, callback_data=f"tariff:{key}")
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def free_tariff_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(language, "free_tariff"), callback_data="tariff:bepul")
    _add_back_button(builder, language)
    return builder.as_markup()


def subscription_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, s in SUBSCRIPTIONS.items():
        builder.button(text=f"{tr(language, f'subscription_{key}')} — {s['som']:,} UZS".replace(",", "."), callback_data=f"sub:{key}")
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def skip_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(language, "skip_step"), callback_data="skip")
    _add_back_button(builder, language)
    return builder.as_markup()


def mpt_topup_amounts_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for amount in (100, 250, 500, 1000):
        builder.button(text=f"{amount} MPT", callback_data=f"buympt:{amount}")
    _add_back_button(builder, language)
    builder.adjust(2)
    return builder.as_markup()


def click_check_kb(merchant_trans_id: str, pay_url: str, language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(language, "click_pay"), url=pay_url)
    builder.button(text=tr(language, "check_payment"), callback_data=f"clickcheck:{merchant_trans_id}")
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def click_app_choice_kb(language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(language, "click_app_yes"), callback_data="clickapp:yes")
    builder.button(text=tr(language, "click_app_no"), callback_data="clickapp:no")
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def click_phone_kb(language: str = "uz") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=tr(language, "share_phone"), request_contact=True)],
            [KeyboardButton(text=tr(language, "menu_back"))],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def click_wait_kb(merchant_trans_id: str, pay_url: str | None = None, language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if pay_url:
        builder.button(text=tr(language, "pay_click_link"), url=pay_url)
    builder.button(text=tr(language, "check_payment"), callback_data=f"clickcheck:{merchant_trans_id}")
    builder.button(text=tr(language, "payment_game"), callback_data=f"clickgame:start:{merchant_trans_id}")
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def click_game_answers_kb(options: list[int], language: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for option in options:
        builder.button(text=str(option), callback_data=f"clickgame:answer:{option}")
    _add_back_button(builder, language)
    builder.adjust(2)
    return builder.as_markup()


def click_game_done_kb(merchant_trans_id: str, language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(language, "check_payment"), callback_data=f"clickcheck:{merchant_trans_id}")
    builder.button(text=tr(language, "contact_admin"), url="https://t.me/preuzadmin")
    _add_back_button(builder, language)
    builder.adjust(1)
    return builder.as_markup()


def card_timeout_kb(payment_id: int, language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(language, "add_five_minutes"), callback_data=f"cardextend:{payment_id}")
    builder.button(text=tr(language, "cancel_payment"), callback_data=f"cardgiveup:{payment_id}")
    _add_back_button(builder, language)
    builder.adjust(2)
    return builder.as_markup()


def card_cancel_kb(payment_id: int, language: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(language, "cancel_payment"), callback_data=f"cardgiveup:{payment_id}")
    _add_back_button(builder, language)
    return builder.as_markup()


def setprice_kb(service_order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Narx belgilash", callback_data=f"svc_setprice:{service_order_id}")
    return builder.as_markup()
