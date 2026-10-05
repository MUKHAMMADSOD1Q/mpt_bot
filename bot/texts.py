"""Foydalanuvchiga ko'rsatiladigan uzun matnlar. Narxlar config.py dan olinadi —
narxni o'zgartirsangiz, qo'llanma ham avtomatik yangilanadi."""

from bot.config import (
    TARIFFS, SUBSCRIPTIONS, MPT_PRICE_SOM, INDEPENDENT_WORK_TYPES, LANGUAGE_SURCHARGE_PER_PAGE,
    TAKLIFNOMA_PRICE, REZYUME_PRICE, YOUTUBE_BANNER_PRICE, QR_GENERATOR_PRICE,
    UI_DESIGN_PRICE_RANGE, LOGO_PRICE_RANGE, WEBSITE_STYLE_PRICES, CARD_NUMBERS, CONTACT,
)


def _som(v) -> str:
    return f"{int(v):,}".replace(",", ".")


def _mpt(v) -> str:
    return f"{v:g}"


ABOUT_US_HTML = (
    "Biz “PreUz” jamoasi 5+ yildan buyon nafaqat O‘zbekiston balki, MDH mamlakatlari talabalariga ham "
    "xizmat ko‘rsatib kelmoqdamiz. Bu bot hozircha siz uchun taqdimot tayyorlamaydi. U shunchaki sizdan "
    "kerakli ma'lumotlarni oladi va adminlarga yuboradi. Va biz siz taqdim etgan ma'lumotlar asosida "
    "xizmatlarni taqdim etamiz. Bizning barcha xizmatlarimiz faqat elektron shaklda taqdim etiladi, biz "
    "qo'l yozuvi, chizmachilik yoki chop etish bilan shug'ullanmaymiz. Agar siz botni tushunishda "
    "muammolarga duch kelsangiz yoki narxlar bilan bog'liq muammolarga duch kelsangiz, "
    "\"To'g'ridan-to'g'ri administratorlarga buyurtma berish\" tugmasi orqali administratorlardan "
    "buyurtma bering!\n\n"
    "Bot asoschisi va PreUz bosh direktori: <a href=\"https://t.me/MUKHAMMADSODlQ\">Muhammadsodiq</a>\n"
    "Ikkinchi akkaunt: <a href=\"https://t.me/MUHAMMADS0DlQ\">Muhammadsodiq Nigmatov</a>\n"
    "Kanal: <a href=\"https://t.me/preuzb\">Prezintatsiya.uz</a>\n"
    "Ishonch kanali: <a href=\"https://t.me/pre_ishonch\">Ishonch</a>\n"
    "Adminlar: <a href=\"https://t.me/preuzadmin\">Admin1</a>, "
    "<a href=\"https://t.me/MUKHAMMADSODlQ\">Admin2</a>\n"
    "'Soff'dagi biz: <a href=\"https://soff.uz/seller/879\">Prezintatsiya.uz</a>\n"
    "Instagram: <a href=\"https://www.instagram.com/mukhammadsodlq?igsh=MWR4dHRzc3ZjYnV2dw==\">Prezintatsiya.uz</a>\n"
    "Donat uchun: <a href=\"https://tirikchilik.uz/mukhammadsodiq\">Tirikchilik</a>\n"
    "Yoki\n"
    "<code>5614682110523232</code> - Uzcard\n"
    "<code>5614681259868051</code> - Uzcard\n"
    "<code>9860170104108668</code> - Humo\n"
    "<code>9860350141636620</code> - Humo\n"
    "<code>4023060518185649</code> - VISA\n"
    "<code>4916990308071304</code> - VISA\n"
    "<code>4413597603204007</code> - VISA\n"
    "<code>5217395906870052</code> - MasterCard\n"
    "(Sodiqjon Nigmatov)\n"
    "Aloqa raqamlari:\n"
    "+998996665732\n+998901995732\n+998942881488"
)

MPT_INFO = (
    "ℹ️ <b>MPT nima?</b> MPT — botimizning ichki coini. <b>1 MPT = {mpt} so'm</b>. "
    "MPT bilan taqdimot buyurtmalari uchun to'lov qilinadi. Sotib olingan MPT balansingizda saqlanadi "
    "va muddati tugamaydi."
).format(mpt=MPT_PRICE_SOM)

SUB_INFO = (
    "ℹ️ <b>Oylik ta'rif (obuna)</b> — belgilangan muddat davomida tanlangan ta'riflardagi taqdimotlar "
    "uchun har safar alohida to'lamaysiz: obuna doirasida MPT yoki so'm yechilmaydi. "
    "Obuna qancha uzoq bo'lsa, shuncha ko'p ta'rif ochiladi."
)


def build_guide() -> str:
    s = []
    s.append(
        "📖 <b>FOYDALANISH QO'LLANMASI</b>\n\n"
        "Bu bot talabalar va tadbirkorlar uchun: siz kerakli ma'lumotlarni kiritasiz, to'lovni amalga "
        "oshirasiz, adminlar esa ishni tayyorlab, shu chatga yuboradi. Ish ko'lamiga qarab "
        "<b>1 soatdan 5 soatgacha</b> vaqt ketadi."
    )

    s.append(
        "🪙 <b>MPT VA SO'M ALMASHINUVI</b>\n\n"
        f"MPT — botning ichki coini. <b>1 MPT = {_som(MPT_PRICE_SOM)} so'm.</b>\n"
        "• MPT ni «💳 Balans va obuna» bo'limida Click yoki karta orqali sotib olasiz.\n"
        "• MPT balansingizda saqlanadi, buyurtma bergach kerakli miqdori avtomatik yechiladi.\n"
        "• Balans yetmasa, buyurtmani to'g'ridan-to'g'ri so'mda (Click yoki karta) to'lashingiz mumkin.\n\n"
        f"Misol: 100 MPT = {_som(100 * MPT_PRICE_SOM)} so'm; 1.000 so'm = {_mpt(1000 / MPT_PRICE_SOM)} MPT."
    )

    lines = ["🎓 <b>TAQDIMOT NARXLARI</b> (1 sahifa uchun)\n"]
    for key, t in TARIFFS.items():
        if key == "bepul":
            lines.append("• <b>Bepul</b> — 0 so'm")
        else:
            lines.append(
                f"• <b>{t['title']}</b> — {_mpt(t['mpt'])} MPT = {_som(t['som'])} so'm "
                f"(10 sahifa: {_som(t['som'] * 10)} so'm)"
            )
    lines.append(
        f"\n🌐 <b>Til:</b> o'zbek tilidan boshqa istalgan tildagi taqdimot narxi tan narxidan "
        f"<b>{_som(LANGUAGE_SURCHARGE_PER_PAGE)} so'm</b> (sahifasiga) qimmat. Bu qoida «Bepul» ta'rifga ta'sir qilmaydi.\n"
        "🧮 Buyurtma bermasdan narxni bilmoqchi bo'lsangiz «Taqdimotga buyurtma berish» → «PreCal» dan foydalaning."
    )
    s.append("\n".join(lines))

    lines = ["📅 <b>OYLIK VA YILLIK TA'RIFLAR (OBUNA)</b>\n"]
    for key, sub in SUBSCRIPTIONS.items():
        names = ", ".join(TARIFFS[k]["title"] for k in sub["unlocks"] if k != "bepul")
        lines.append(f"• <b>{sub['title']}</b> ({sub['days']} kun) — {_som(sub['som'])} so'm. Ochiladi: {names}")
    lines.append("\nObuna faol bo'lsa, unga kiruvchi ta'riflardagi taqdimotlar uchun MPT yoki so'm yechilmaydi.")
    s.append("\n".join(lines))

    lines = ["📝 <b>MUSTAQIL ISHLAR</b> (1 sahifa uchun)\n"]
    for info in INDEPENDENT_WORK_TYPES.values():
        price = f"{_som(info['price_per_page'])} so'm" if info["price_per_page"] else "admin bilan kelishiladi"
        lines.append(f"• {info['title']} — {price}")
    lines.append(f"\nO'zbek tilidan boshqa tilda bajarilsa, har sahifaga +{_som(LANGUAGE_SURCHARGE_PER_PAGE)} so'm qo'shiladi.")
    s.append("\n".join(lines))

    ui_lo, ui_hi = UI_DESIGN_PRICE_RANGE
    lg_lo, lg_hi = LOGO_PRICE_RANGE
    web_lo = min(v[0] for v in WEBSITE_STYLE_PRICES.values() if v)
    web_hi = max(v[1] for v in WEBSITE_STYLE_PRICES.values() if v)
    s.append(
        "🏢 <b>TADBIRKORLAR UCHUN</b>\n\n"
        f"• Taklifnoma — {_som(TAKLIFNOMA_PRICE)} so'm\n"
        f"• Rezyume — {_som(REZYUME_PRICE)} so'm\n"
        f"• YouTube banner — {_som(YOUTUBE_BANNER_PRICE)} so'm\n"
        f"• QR-generator — {_som(QR_GENERATOR_PRICE)} so'm\n"
        f"• Logo — {_som(lg_lo)} dan {_som(lg_hi)} so'mgacha (murakkabligiga qarab)\n"
        f"• UI dizayn — {_som(ui_lo)} dan {_som(ui_hi)} so'mgacha (biznes hajmiga qarab)\n"
        f"• Web-sayt — {_som(web_lo)} dan {_som(web_hi)} so'mgacha (uslubga qarab)\n\n"
        "Narxi oraliqda berilgan xizmatlarda aniq narxni admin siz bilan kelishadi va to'lov so'rovini yuboradi."
    )

    s.append(
        "🧾 <b>BUYURTMA VA TO'LOV TARTIBI</b>\n\n"
        "1️⃣ Xizmatni tanlab, savollarga javob berasiz.\n"
        "2️⃣ Ma'lumotlar <b>ikki marta</b> tasdiqlanadi (adashib buyurtma bermaslik uchun).\n"
        "3️⃣ To'lov usulini tanlaysiz:\n"
        "   • <b>Click</b> — havola orqali (Click ilovasi o'rnatilgan bo'lsa ilovada, aks holda brauzerda ochiladi). "
        "To'lovdan so'ng «Tekshirish» tugmasini bosasiz.\n"
        "   • <b>Karta</b> — karta raqami ko'rsatiladi (bosib nusxalash mumkin), to'lov uchun 5 daqiqa beriladi. "
        "Keyin to'lov chekini (rasm yoki PDF) yuborasiz. Vaqt tugasa, yana 5 daqiqa qo'shish yoki bekor qilish mumkin. "
        "Chekni adminlar tekshirib tasdiqlaydi.\n"
        "4️⃣ To'lov tasdiqlangach, ish tayyor bo'lishi bilan fayl shu chatga yuboriladi.\n\n"
        "⚠️ Soxta yoki eskirgan chek yuborilsa, to'lov rad etiladi."
    )

    s.append(
        "📞 <b>ALOQA</b>\n\n"
        f"Savol-javob: {CONTACT['support']}\n"
        f"Bot asoschisi: {CONTACT['founder_dev']}\n"
        "Telefon: " + ", ".join(CONTACT["phones"]) + "\n\n"
        "🤝 <b>BIZ HAQIMIZDA</b>\n\n" + ABOUT_US_HTML
    )
    return "\n\n———\n\n".join(s)


def chunk_text(text: str, limit: int = 3800) -> list[str]:
    """Telegram 4096 belgi limitiga tushmaslik uchun matnni bo'laklarga ajratadi (bo'sh qator bo'yicha)."""
    parts, buf = [], ""
    for block in text.split("\n\n"):
        if buf and len(buf) + len(block) + 2 > limit:
            parts.append(buf)
            buf = ""
        buf = f"{buf}\n\n{block}" if buf else block
    if buf:
        parts.append(buf)
    return parts
