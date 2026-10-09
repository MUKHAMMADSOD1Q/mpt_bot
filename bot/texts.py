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


ABOUT_US_HTML_BY_LANGUAGE = {
    "uz": (
    "Biz “PreUz” jamoasi 5+ yildan buyon nafaqat O‘zbekiston balki, MDH mamlakatlari talabalariga ham "
    "xizmat ko‘rsatib kelmoqdamiz. AI taqdimoti uchun bot kerakli ma'lumotlarni va siz tashqi AI'dan "
    "olib yuborgan matnni qabul qiladi, uchta shablondan birida taqdimot tayyorlaydi va admin ko‘rigiga "
    "yuboradi. Fayl admin tasdiqlagandan keyin sizga yetkaziladi. Boshqa xizmatlar adminlar tomonidan "
    "ko‘rib chiqiladi. Barcha xizmatlarimiz faqat elektron shaklda taqdim etiladi; biz "
    "qo'l yozuvi, chizmachilik yoki chop etish bilan shug'ullanmaymiz. Agar siz botni tushunishda "
    "yoki buyurtma bilan bog'liq muammolarga duch kelsangiz, sozlamalardagi admin bilan aloqa bo'limidan "
    "foydalaning.\n\n"
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
    ),
    "ru": (
        "Команда «PreUz» уже более 5 лет помогает студентам не только Узбекистана, но и стран СНГ. "
        "Для AI-презентации бот принимает необходимые данные и текст, полученный вами от внешнего ИИ, "
        "оформляет презентацию в одном из трёх шаблонов и отправляет её администратору на проверку. "
        "После одобрения файл будет отправлен вам. Остальные услуги рассматривают администраторы. "
        "Все услуги предоставляются только в электронном виде; мы не выполняем рукописные работы, "
        "чертежи и печать. Если у вас возникли вопросы по работе бота или заказу, воспользуйтесь "
        "разделом связи с администратором в настройках.\n\n"
        "Основатель бота и генеральный директор PreUz: <a href=\"https://t.me/MUKHAMMADSODlQ\">Мухаммадсодик</a>\n"
        "Второй аккаунт: <a href=\"https://t.me/MUHAMMADS0DlQ\">Мухаммадсодик Нигматов</a>\n"
        "Канал: <a href=\"https://t.me/preuzb\">Prezintatsiya.uz</a>\n"
        "Канал доверия: <a href=\"https://t.me/pre_ishonch\">Ishonch</a>\n"
        "Администраторы: <a href=\"https://t.me/preuzadmin\">Администратор 1</a>, "
        "<a href=\"https://t.me/MUKHAMMADSODlQ\">Администратор 2</a>\n"
        "Мы на Soff: <a href=\"https://soff.uz/seller/879\">Prezintatsiya.uz</a>\n"
        "Instagram: <a href=\"https://www.instagram.com/mukhammadsodlq?igsh=MWR4dHRzc3ZjYnV2dw==\">Prezintatsiya.uz</a>\n"
        "Поддержать донатом: <a href=\"https://tirikchilik.uz/mukhammadsodiq\">Tirikchilik</a>\n"
        "Или переводом на карту:\n"
        "<code>5614682110523232</code> — Uzcard\n"
        "<code>5614681259868051</code> — Uzcard\n"
        "<code>9860170104108668</code> — Humo\n"
        "<code>9860350141636620</code> — Humo\n"
        "<code>4023060518185649</code> — VISA\n"
        "<code>4916990308071304</code> — VISA\n"
        "<code>4413597603204007</code> — VISA\n"
        "<code>5217395906870052</code> — MasterCard\n"
        "(Содикжон Нигматов)\n"
        "Контактные телефоны:\n"
        "+998996665732\n+998901995732\n+998942881488"
    ),
    "en": (
        "The PreUz team has been serving students in Uzbekistan and other CIS countries for over five years. "
        "For AI presentations, the bot collects the required details and text you obtain from an external AI, "
        "formats the presentation using one of three templates, and sends it to an admin for review. "
        "Once approved, the file is delivered to you. Admins review all other services. Services are provided "
        "electronically only; we do not offer handwritten work, drawing, or printing. If you have questions "
        "about the bot or an order, use the contact-an-admin section in Settings.\n\n"
        "Bot founder and PreUz CEO: <a href=\"https://t.me/MUKHAMMADSODlQ\">Muhammadsodiq</a>\n"
        "Second account: <a href=\"https://t.me/MUHAMMADS0DlQ\">Muhammadsodiq Nigmatov</a>\n"
        "Channel: <a href=\"https://t.me/preuzb\">Prezintatsiya.uz</a>\n"
        "Trust channel: <a href=\"https://t.me/pre_ishonch\">Ishonch</a>\n"
        "Admins: <a href=\"https://t.me/preuzadmin\">Admin 1</a>, "
        "<a href=\"https://t.me/MUKHAMMADSODlQ\">Admin 2</a>\n"
        "Find us on Soff: <a href=\"https://soff.uz/seller/879\">Prezintatsiya.uz</a>\n"
        "Instagram: <a href=\"https://www.instagram.com/mukhammadsodlq?igsh=MWR4dHRzc3ZjYnV2dw==\">Prezintatsiya.uz</a>\n"
        "Donate: <a href=\"https://tirikchilik.uz/mukhammadsodiq\">Tirikchilik</a>\n"
        "Or donate by card:\n"
        "<code>5614682110523232</code> — Uzcard\n"
        "<code>5614681259868051</code> — Uzcard\n"
        "<code>9860170104108668</code> — Humo\n"
        "<code>9860350141636620</code> — Humo\n"
        "<code>4023060518185649</code> — VISA\n"
        "<code>4916990308071304</code> — VISA\n"
        "<code>4413597603204007</code> — VISA\n"
        "<code>5217395906870052</code> — MasterCard\n"
        "(Sodiqjon Nigmatov)\n"
        "Contact phone numbers:\n"
        "+998996665732\n+998901995732\n+998942881488"
    ),
    "tg": (
        "Дастаи «PreUz» беш аз 5 сол боз ба донишҷӯёни Ӯзбекистон ва кишварҳои ИДМ хизмат мерасонад. "
        "Барои муаррифии AI бот маълумоти зарурӣ ва матни аз зеҳни сунъии беруна гирифтаи шуморо қабул карда, "
        "муаррифиро дар яке аз се қолаб омода мекунад ва барои санҷиш ба маъмур мефиристад. Пас аз тасдиқи "
        "маъмур файл ба шумо фиристода мешавад. Хизматҳои дигарро маъмурон баррасӣ мекунанд. Ҳамаи хизматҳо "
        "танҳо ба шакли электронӣ пешниҳод мешаванд; мо кори дастнавис, расмкашӣ ва чопро иҷро намекунем. "
        "Агар оид ба бот ё фармоиш савол дошта бошед, аз бахши тамос бо маъмур дар танзимот истифода баред.\n\n"
        "Асосгузори бот ва роҳбари PreUz: <a href=\"https://t.me/MUKHAMMADSODlQ\">Muhammadsodiq</a>\n"
        "Ҳисоби дуюм: <a href=\"https://t.me/MUHAMMADS0DlQ\">Muhammadsodiq Nigmatov</a>\n"
        "Канал: <a href=\"https://t.me/preuzb\">Prezintatsiya.uz</a>\n"
        "Канали боварӣ: <a href=\"https://t.me/pre_ishonch\">Ishonch</a>\n"
        "Маъмурон: <a href=\"https://t.me/preuzadmin\">Маъмур 1</a>, "
        "<a href=\"https://t.me/MUKHAMMADSODlQ\">Маъмур 2</a>\n"
        "Мо дар Soff: <a href=\"https://soff.uz/seller/879\">Prezintatsiya.uz</a>\n"
        "Instagram: <a href=\"https://www.instagram.com/mukhammadsodlq?igsh=MWR4dHRzc3ZjYnV2dw==\">Prezintatsiya.uz</a>\n"
        "Барои хайрия: <a href=\"https://tirikchilik.uz/mukhammadsodiq\">Tirikchilik</a>\n"
        "Ё ба корт:\n"
        "<code>5614682110523232</code> — Uzcard\n"
        "<code>5614681259868051</code> — Uzcard\n"
        "<code>9860170104108668</code> — Humo\n"
        "<code>9860350141636620</code> — Humo\n"
        "<code>4023060518185649</code> — VISA\n"
        "<code>4916990308071304</code> — VISA\n"
        "<code>4413597603204007</code> — VISA\n"
        "<code>5217395906870052</code> — MasterCard\n"
        "(Sodiqjon Nigmatov)\n"
        "Рақамҳои тамос:\n"
        "+998996665732\n+998901995732\n+998942881488"
    ),
    "kk": (
        "«PreUz» командасы Өзбекстан мен ТМД елдерінің студенттеріне 5 жылдан астам уақыттан бері қызмет көрсетіп келеді. "
        "AI-презентация үшін бот қажетті мәліметтерді және сыртқы ЖИ-ден алған мәтініңізді қабылдап, үш үлгінің бірімен "
        "презентация дайындайды да, тексеру үшін әкімшіге жібереді. Әкімші мақұлдағаннан кейін файл сізге жіберіледі. "
        "Басқа қызметтерді әкімшілер қарайды. Барлық қызмет тек электронды түрде ұсынылады; қолжазба, сызба немесе "
        "басып шығару қызметтері көрсетілмейді. Бот немесе тапсырыс туралы сұрақ болса, баптаулардағы әкімшімен байланыс "
        "бөлімін пайдаланыңыз.\n\n"
        "Бот негізін қалаушы және PreUz бас директоры: <a href=\"https://t.me/MUKHAMMADSODlQ\">Muhammadsodiq</a>\n"
        "Екінші аккаунт: <a href=\"https://t.me/MUHAMMADS0DlQ\">Muhammadsodiq Nigmatov</a>\n"
        "Арна: <a href=\"https://t.me/preuzb\">Prezintatsiya.uz</a>\n"
        "Сенім арнасы: <a href=\"https://t.me/pre_ishonch\">Ishonch</a>\n"
        "Әкімшілер: <a href=\"https://t.me/preuzadmin\">Әкімші 1</a>, "
        "<a href=\"https://t.me/MUKHAMMADSODlQ\">Әкімші 2</a>\n"
        "Soff-тағы парақшамыз: <a href=\"https://soff.uz/seller/879\">Prezintatsiya.uz</a>\n"
        "Instagram: <a href=\"https://www.instagram.com/mukhammadsodlq?igsh=MWR4dHRzc3ZjYnV2dw==\">Prezintatsiya.uz</a>\n"
        "Қайырымдылық: <a href=\"https://tirikchilik.uz/mukhammadsodiq\">Tirikchilik</a>\n"
        "Немесе картаға аударыңыз:\n"
        "<code>5614682110523232</code> — Uzcard\n"
        "<code>5614681259868051</code> — Uzcard\n"
        "<code>9860170104108668</code> — Humo\n"
        "<code>9860350141636620</code> — Humo\n"
        "<code>4023060518185649</code> — VISA\n"
        "<code>4916990308071304</code> — VISA\n"
        "<code>4413597603204007</code> — VISA\n"
        "<code>5217395906870052</code> — MasterCard\n"
        "(Sodiqjon Nigmatov)\n"
        "Байланыс телефондары:\n"
        "+998996665732\n+998901995732\n+998942881488"
    ),
    "ky": (
        "«PreUz» командасы Өзбекстандагы жана КМШ өлкөлөрүндөгү студенттерге 5 жылдан ашык убакыттан бери кызмат көрсөтөт. "
        "AI-презентация үчүн бот керектүү маалыматтарды жана тышкы ЖИден алган текстиңизди кабыл алып, үч шаблондун биринде "
        "презентация даярдайт да, текшерүү үчүн администраторго жөнөтөт. Администратор жактыргандан кийин файл сизге келет. "
        "Башка кызматтарды администраторлор карашат. Бардык кызматтар электрондук түрдө гана көрсөтүлөт; кол жазма, сүрөт "
        "тартуу же басып чыгаруу кызматтары жок. Бот же буйрутма боюнча суроолор болсо, жөндөөлөрдөгү администратор менен "
        "байланыш бөлүмүн колдонуңуз.\n\n"
        "Боттун негиздөөчүсү жана PreUz жетекчиси: <a href=\"https://t.me/MUKHAMMADSODlQ\">Muhammadsodiq</a>\n"
        "Экинчи аккаунт: <a href=\"https://t.me/MUHAMMADS0DlQ\">Muhammadsodiq Nigmatov</a>\n"
        "Канал: <a href=\"https://t.me/preuzb\">Prezintatsiya.uz</a>\n"
        "Ишеним каналы: <a href=\"https://t.me/pre_ishonch\">Ishonch</a>\n"
        "Администраторлор: <a href=\"https://t.me/preuzadmin\">Администратор 1</a>, "
        "<a href=\"https://t.me/MUKHAMMADSODlQ\">Администратор 2</a>\n"
        "Soff баракчабыз: <a href=\"https://soff.uz/seller/879\">Prezintatsiya.uz</a>\n"
        "Instagram: <a href=\"https://www.instagram.com/mukhammadsodlq?igsh=MWR4dHRzc3ZjYnV2dw==\">Prezintatsiya.uz</a>\n"
        "Кайрымдуулук: <a href=\"https://tirikchilik.uz/mukhammadsodiq\">Tirikchilik</a>\n"
        "Же картага которуңуз:\n"
        "<code>5614682110523232</code> — Uzcard\n"
        "<code>5614681259868051</code> — Uzcard\n"
        "<code>9860170104108668</code> — Humo\n"
        "<code>9860350141636620</code> — Humo\n"
        "<code>4023060518185649</code> — VISA\n"
        "<code>4916990308071304</code> — VISA\n"
        "<code>4413597603204007</code> — VISA\n"
        "<code>5217395906870052</code> — MasterCard\n"
        "(Sodiqjon Nigmatov)\n"
        "Байланыш телефондору:\n"
        "+998996665732\n+998901995732\n+998942881488"
    ),
    "tk": (
        "«PreUz» topary Özbegistanyň we GDA ýurtlarynyň talyplaryna 5 ýyldan gowrak wagt bäri hyzmat edýär. "
        "AI tanyşdyryşy üçin bot zerur maglumatlary we daşarky emeli aňdan alan tekstiňizi kabul edýär, üç şablonyň "
        "birinde tanyşdyryş taýýarlaýar we barlamak üçin administratoryň garamagyna iberýär. Tassyklanandan soň faýl "
        "size iberilýär. Beýleki hyzmatlary administratorlar gözden geçirýärler. Ähli hyzmatlar diňe elektron görnüşde "
        "berilýär; biz golýazma, surat çekmek ýa-da çap etmek hyzmatlaryny ýerine ýetirmeýäris. Bot ýa-da sargyt barada "
        "soragyňyz bolsa, sazlamalardaky administrator bilen habarlaşmak bölüminden peýdalanyň.\n\n"
        "Boty esaslandyryjy we PreUz baş direktory: <a href=\"https://t.me/MUKHAMMADSODlQ\">Muhammadsodiq</a>\n"
        "Ikinji hasap: <a href=\"https://t.me/MUHAMMADS0DlQ\">Muhammadsodiq Nigmatov</a>\n"
        "Kanal: <a href=\"https://t.me/preuzb\">Prezintatsiya.uz</a>\n"
        "Ynam kanaly: <a href=\"https://t.me/pre_ishonch\">Ishonch</a>\n"
        "Administratorlar: <a href=\"https://t.me/preuzadmin\">Administrator 1</a>, "
        "<a href=\"https://t.me/MUKHAMMADSODlQ\">Administrator 2</a>\n"
        "Soff sahypamyz: <a href=\"https://soff.uz/seller/879\">Prezintatsiya.uz</a>\n"
        "Instagram: <a href=\"https://www.instagram.com/mukhammadsodlq?igsh=MWR4dHRzc3ZjYnV2dw==\">Prezintatsiya.uz</a>\n"
        "Haýyr-sahawat: <a href=\"https://tirikchilik.uz/mukhammadsodiq\">Tirikchilik</a>\n"
        "Ýa-da karta geçirimi:\n"
        "<code>5614682110523232</code> — Uzcard\n"
        "<code>5614681259868051</code> — Uzcard\n"
        "<code>9860170104108668</code> — Humo\n"
        "<code>9860350141636620</code> — Humo\n"
        "<code>4023060518185649</code> — VISA\n"
        "<code>4916990308071304</code> — VISA\n"
        "<code>4413597603204007</code> — VISA\n"
        "<code>5217395906870052</code> — MasterCard\n"
        "(Sodiqjon Nigmatov)\n"
        "Habarlaşmak üçin telefon belgileri:\n"
        "+998996665732\n+998901995732\n+998942881488"
    ),
}

ABOUT_US_HTML = ABOUT_US_HTML_BY_LANGUAGE["uz"]

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

    s.append(
        "🤖 <b>TAQDIMOTNI O'ZINGIZ TAYYORLASH</b>\n\n"
        "• Umumiy sahifalar soniga titul va yakuniy «RAHMAT!» sahifalari ham kiradi; kamida 3 ta sahifa tanlang.\n"
        "• Bot so'ragan matn abzatslari soni umumiy sahifalardan 2 taga kam bo'ladi — titul va yakuniy sahifaga matn yozilmaydi.\n"
        "• Rasmlar ixtiyoriy: istalgancha rasm yuborish va «Rasmlarni tugatish» tugmasi bilan xohlagan payt yakunlash mumkin.\n"
        "• Birinchi sahifada mavzu va talaba ma'lumotlari, oxirida faqat «RAHMAT!» ko'rsatiladi. Fayl admin ko'rigidan keyin yuboriladi."
    )

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
