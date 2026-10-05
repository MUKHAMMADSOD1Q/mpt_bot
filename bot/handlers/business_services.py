import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.states import Taklifnoma, UiDesign, WebsiteOrder, ResumeOrder, YoutubeBanner, LogoOrder, QrGenerator
from bot.keyboards import (
    business_services_kb, skip_kb, skip_or_upload_kb, ui_platform_kb, business_size_kb, website_style_kb,
)
from bot.services.pricing import format_som
from bot.services.group_orders import begin_confirmation
from bot.config import (
    TAKLIFNOMA_PRICE, REZYUME_PRICE, YOUTUBE_BANNER_PRICE, QR_GENERATOR_PRICE,
    UI_DESIGN_PRICE_RANGE, LOGO_PRICE_RANGE, WEBSITE_STYLE_PRICES,
)

router = Router()


def _now() -> str:
    return datetime.datetime.now().strftime("%d.%m.%Y %H:%M")


async def _user_header(from_user) -> list[str]:
    """from_user: Message.from_user yoki CallbackQuery.from_user — ikkalasida ham
    bir xil maydonlar (id, username, full_name) bor."""
    from bot.database import get_user
    telegram_id = from_user.id
    user = await get_user(telegram_id)
    phone = (user.get("phone") if user else None) or "O'tkazib yuborgan"
    username = from_user.username or "-"
    return [
        f"👤 Ism: {from_user.full_name}",
        f"🔗 Username: @{username}",
        f"📞 Telefon raqam: {phone}",
    ]


@router.message(F.text == "🏢 Tadbirkorlar uchun")
async def business_menu(message: Message):
    await message.answer(
        "Tadbirkorlar uchun qanday xizmat kerak? Tanlang:",
        reply_markup=business_services_kb(),
    )


# ==================== TAKLIFNOMA ====================

@router.callback_query(F.data == "biz:taklifnoma")
async def taklifnoma_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Taklifnoma.waiting_date)
    await callback.message.answer("To'y kunini (sana) kiriting:")
    await callback.answer()


@router.message(Taklifnoma.waiting_date)
async def taklifnoma_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text.strip())
    await state.set_state(Taklifnoma.waiting_couple_names)
    await message.answer("Kelin va kuyovning to'liq ism-familiyasini kiriting (masalan: oilalarni ham ko'rsating):")


@router.message(Taklifnoma.waiting_couple_names)
async def taklifnoma_names(message: Message, state: FSMContext):
    await state.update_data(couple_names=message.text.strip())
    await state.set_state(Taklifnoma.waiting_venue)
    await message.answer("To'yxona manzilini kiriting:")


@router.message(Taklifnoma.waiting_venue)
async def taklifnoma_venue(message: Message, state: FSMContext):
    await state.update_data(venue=message.text.strip())
    await state.set_state(Taklifnoma.waiting_extra)
    await message.answer(
        "Yana qo'shimcha aytmoqchi bo'lgan narsa bormi? (rang, uslub va h.k.)\n"
        "<i>Ixtiyoriy — o'tkazib yuborishingiz mumkin</i>",
        parse_mode="HTML", reply_markup=skip_kb(),
    )


async def _taklifnoma_finish(message_or_callback, state: FSMContext, telegram_id: int, extra: str):
    data = await state.get_data()
    header = await _user_header(message_or_callback.from_user)
    lines = header + [
        "📄 Xizmat: Taklifnoma",
        f"💍 To'y kuni: {data['date']}",
        f"👰🤵 Kelin-kuyov: {data['couple_names']}",
        f"🏛 To'yxona manzili: {data['venue']}",
        f"➕ Qo'shimcha: {extra or '-'}",
        f"💰 Narx: {format_som(TAKLIFNOMA_PRICE)} so'm",
        f"USER_ID: {telegram_id}",
        f"🕒 Sana/vaqt: {_now()}",
    ]
    target = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
    await begin_confirmation(
        target, state,
        flow_kind="service", telegram_id=telegram_id, service_type="taklifnoma",
        topic="Taklifnoma", summary_text="\n".join(lines), price_som=TAKLIFNOMA_PRICE,
        group_lines=lines,
        preview_text=f"<b>Taklifnoma</b> buyurtmasi — narxi <b>{format_som(TAKLIFNOMA_PRICE)} so'm</b>.\n\nTasdiqlaysizmi?",
    )


@router.message(Taklifnoma.waiting_extra)
async def taklifnoma_extra(message: Message, state: FSMContext):
    await _taklifnoma_finish(message, state, message.from_user.id, message.text.strip())


@router.callback_query(Taklifnoma.waiting_extra, F.data == "skip")
async def taklifnoma_skip_extra(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await _taklifnoma_finish(callback, state, callback.from_user.id, "")


# ==================== UI DIZAYN ====================

@router.callback_query(F.data == "biz:ui")
async def ui_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UiDesign.waiting_platform)
    await callback.message.answer("Dizayn nima uchun kerak?", reply_markup=ui_platform_kb())
    await callback.answer()


@router.callback_query(UiDesign.waiting_platform, F.data.startswith("ui_platform:"))
async def ui_platform(callback: CallbackQuery, state: FSMContext):
    labels = {"mobil": "Mobil ilova", "veb": "Veb-sayt", "tgwebapp": "Telegram Web-App"}
    key = callback.data.split(":", 1)[1]
    await state.update_data(platform=labels.get(key, key))
    await state.set_state(UiDesign.waiting_business_type)
    await callback.message.answer("Biznes turingizni kiriting (masalan: kafe, do'kon, IT xizmat va h.k.):")
    await callback.answer()


@router.message(UiDesign.waiting_business_type)
async def ui_business_type(message: Message, state: FSMContext):
    await state.update_data(business_type=message.text.strip())
    await state.set_state(UiDesign.waiting_business_size)
    await message.answer("Biznesingiz hajmi qanday?", reply_markup=business_size_kb())


@router.callback_query(UiDesign.waiting_business_size, F.data.startswith("biz_size:"))
async def ui_business_size(callback: CallbackQuery, state: FSMContext):
    labels = {"kichik": "Kichik", "orta": "O'rta", "katta": "Katta"}
    key = callback.data.split(":", 1)[1]
    await state.update_data(business_size=labels.get(key, key))
    await state.set_state(UiDesign.waiting_extra)
    await callback.message.answer(
        "Qo'shimcha talab yoki tafsilot bormi?\n<i>Ixtiyoriy</i>",
        parse_mode="HTML", reply_markup=skip_kb(),
    )
    await callback.answer()


async def _ui_finish(message_or_callback, state: FSMContext, telegram_id: int, extra: str):
    data = await state.get_data()
    header = await _user_header(message_or_callback.from_user)
    lo, hi = UI_DESIGN_PRICE_RANGE
    lines = header + [
        "📄 Xizmat: UI dizayn",
        f"📱 Maqsad: {data['platform']}",
        f"🏢 Biznes turi: {data['business_type']}",
        f"📏 Biznes hajmi: {data['business_size']}",
        f"➕ Qo'shimcha: {extra or '-'}",
        f"💰 Taxminiy narx: {format_som(lo)} - {format_som(hi)} so'm (aniq narx admin bilan kelishiladi)",
        f"USER_ID: {telegram_id}",
        f"🕒 Sana/vaqt: {_now()}",
    ]
    target = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
    await begin_confirmation(
        target, state,
        flow_kind="service", telegram_id=telegram_id, service_type="ui_dizayn",
        topic="UI dizayn", summary_text="\n".join(lines), price_som=None,
        group_lines=lines,
        preview_text=(
            f"<b>UI dizayn</b> buyurtmasi — taxminiy narx {format_som(lo)}-{format_som(hi)} so'm "
            "(admin bilan yakuniy kelishiladi).\n\nTasdiqlaysizmi?"
        ),
    )


@router.message(UiDesign.waiting_extra)
async def ui_extra(message: Message, state: FSMContext):
    await _ui_finish(message, state, message.from_user.id, message.text.strip())


@router.callback_query(UiDesign.waiting_extra, F.data == "skip")
async def ui_skip_extra(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await _ui_finish(callback, state, callback.from_user.id, "")


# ==================== WEB-SAYT ====================

@router.callback_query(F.data == "biz:web")
async def web_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WebsiteOrder.waiting_business_type)
    await callback.message.answer("Tadbirkorlik turingizni kiriting (masalan: restoran, savdo, xizmat ko'rsatish):")
    await callback.answer()


@router.message(WebsiteOrder.waiting_business_type)
async def web_business_type(message: Message, state: FSMContext):
    await state.update_data(business_type=message.text.strip())
    await state.set_state(WebsiteOrder.waiting_style)
    await message.answer("Qaysi uslubda sayt kerak?", reply_markup=website_style_kb())


@router.callback_query(WebsiteOrder.waiting_style, F.data.startswith("web_style:"))
async def web_style(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":", 1)[1]
    labels = {"minimalizm": "Minimalizm", "zamonaviy": "Zamonaviy", "hi-tech": "Hi-Tech", "3d": "3D", "boshqa": "Boshqa"}
    await state.update_data(style_key=key, style_label=labels.get(key, key))
    await state.set_state(WebsiteOrder.waiting_extra)
    await callback.message.answer(
        "Qo'shimcha talablaringiz bormi (sahifalar soni, funksiyalar va h.k.)?\n<i>Ixtiyoriy</i>",
        parse_mode="HTML", reply_markup=skip_kb(),
    )
    await callback.answer()


async def _web_finish(message_or_callback, state: FSMContext, telegram_id: int, extra: str):
    data = await state.get_data()
    header = await _user_header(message_or_callback.from_user)
    price_range = WEBSITE_STYLE_PRICES.get(data["style_key"])
    if price_range:
        lo, hi = price_range
        price_text = f"{format_som(lo)} - {format_som(hi)} so'm (aniq narx admin bilan kelishiladi)"
    else:
        price_text = "admin bilan kelishiladi"
    lines = header + [
        "📄 Xizmat: Web-sayt",
        f"🏢 Tadbirkorlik turi: {data['business_type']}",
        f"🎨 Uslub: {data['style_label']}",
        f"➕ Qo'shimcha: {extra or '-'}",
        f"💰 Narx: {price_text}",
        f"USER_ID: {telegram_id}",
        f"🕒 Sana/vaqt: {_now()}",
    ]
    target = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
    await begin_confirmation(
        target, state,
        flow_kind="service", telegram_id=telegram_id, service_type="web_sayt",
        topic="Web-sayt", summary_text="\n".join(lines), price_som=None,
        group_lines=lines,
        preview_text=f"<b>Web-sayt</b> buyurtmasi — narx: {price_text}.\n\nTasdiqlaysizmi?",
    )


@router.message(WebsiteOrder.waiting_extra)
async def web_extra(message: Message, state: FSMContext):
    await _web_finish(message, state, message.from_user.id, message.text.strip())


@router.callback_query(WebsiteOrder.waiting_extra, F.data == "skip")
async def web_skip_extra(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await _web_finish(callback, state, callback.from_user.id, "")


# ==================== REZYUME ====================

@router.callback_query(F.data == "biz:rezyume")
async def resume_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ResumeOrder.waiting_fullname)
    await callback.message.answer("To'liq ism-familiyangizni kiriting:")
    await callback.answer()


@router.message(ResumeOrder.waiting_fullname)
async def resume_fullname(message: Message, state: FSMContext):
    await state.update_data(fullname=message.text.strip())
    await state.set_state(ResumeOrder.waiting_birthdate)
    await message.answer("Tug'ilgan sanangizni kiriting:")


@router.message(ResumeOrder.waiting_birthdate)
async def resume_birthdate(message: Message, state: FSMContext):
    await state.update_data(birthdate=message.text.strip())
    await state.set_state(ResumeOrder.waiting_contact)
    await message.answer("Aloqa uchun telefon raqam va (agar bo'lsa) email kiriting:")


@router.message(ResumeOrder.waiting_contact)
async def resume_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text.strip())
    await state.set_state(ResumeOrder.waiting_education)
    await message.answer("Ta'lim ma'lumotingizni kiriting (o'quv joyi, yo'nalish, yillar):")


@router.message(ResumeOrder.waiting_education)
async def resume_education(message: Message, state: FSMContext):
    await state.update_data(education=message.text.strip())
    await state.set_state(ResumeOrder.waiting_experience)
    await message.answer("Ish tajribangizni kiriting (joy, lavozim, muddat):")


@router.message(ResumeOrder.waiting_experience)
async def resume_experience(message: Message, state: FSMContext):
    await state.update_data(experience=message.text.strip())
    await state.set_state(ResumeOrder.waiting_skills)
    await message.answer("Ko'nikmalaringizni kiriting:")


@router.message(ResumeOrder.waiting_skills)
async def resume_skills(message: Message, state: FSMContext):
    await state.update_data(skills=message.text.strip())
    await state.set_state(ResumeOrder.waiting_languages)
    await message.answer("Qaysi tillarni bilasiz (va darajasi)?")


@router.message(ResumeOrder.waiting_languages)
async def resume_languages(message: Message, state: FSMContext):
    await state.update_data(languages=message.text.strip())
    await state.set_state(ResumeOrder.waiting_extra)
    await message.answer(
        "Qo'shimcha (sertifikatlar, maqsad qilingan lavozim va h.k.)?\n<i>Ixtiyoriy</i>",
        parse_mode="HTML", reply_markup=skip_kb(),
    )


async def _resume_finish(message_or_callback, state: FSMContext, telegram_id: int, extra: str):
    data = await state.get_data()
    header = await _user_header(message_or_callback.from_user)
    lines = header + [
        "📄 Xizmat: Rezyume",
        f"👤 F.I.Sh: {data['fullname']}",
        f"🎂 Tug'ilgan sana: {data['birthdate']}",
        f"📞 Aloqa: {data['contact']}",
        f"🎓 Ta'lim: {data['education']}",
        f"💼 Ish tajribasi: {data['experience']}",
        f"🛠 Ko'nikmalar: {data['skills']}",
        f"🌐 Tillar: {data['languages']}",
        f"➕ Qo'shimcha: {extra or '-'}",
        f"💰 Narx: {format_som(REZYUME_PRICE)} so'm",
        f"USER_ID: {telegram_id}",
        f"🕒 Sana/vaqt: {_now()}",
    ]
    target = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
    await begin_confirmation(
        target, state,
        flow_kind="service", telegram_id=telegram_id, service_type="rezyume",
        topic="Rezyume", summary_text="\n".join(lines), price_som=REZYUME_PRICE,
        group_lines=lines,
        preview_text=f"<b>Rezyume</b> buyurtmasi — narxi <b>{format_som(REZYUME_PRICE)} so'm</b>.\n\nTasdiqlaysizmi?",
    )


@router.message(ResumeOrder.waiting_extra)
async def resume_extra(message: Message, state: FSMContext):
    await _resume_finish(message, state, message.from_user.id, message.text.strip())


@router.callback_query(ResumeOrder.waiting_extra, F.data == "skip")
async def resume_skip_extra(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await _resume_finish(callback, state, callback.from_user.id, "")


# ==================== YOUTUBE BANNER ====================

@router.callback_query(F.data == "biz:youtube")
async def youtube_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(YoutubeBanner.waiting_channel_name)
    await callback.message.answer("YouTube kanalingiz nomini kiriting:")
    await callback.answer()


@router.message(YoutubeBanner.waiting_channel_name)
async def youtube_channel(message: Message, state: FSMContext):
    await state.update_data(channel_name=message.text.strip())
    await state.set_state(YoutubeBanner.waiting_contacts)
    await message.answer(
        "Bannerda nimalar ko'rinishini xohlaysiz? (telefon, Telegram, Instagram va h.k. nicknamelar):"
    )


@router.message(YoutubeBanner.waiting_contacts)
async def youtube_contacts(message: Message, state: FSMContext):
    await state.update_data(contacts=message.text.strip())
    await state.set_state(YoutubeBanner.waiting_image)
    await message.answer(
        "Agar banner uchun tayyor rasm bo'lsa yuboring (bo'lmasa o'tkazib yuboring).\n"
        "<i>Eslatma: rasm YouTube banner o'lchamidan farq qilsa, banner markaziga "
        "joylashtiriladi, qolgan qismi oq fonda qoladi.</i>",
        parse_mode="HTML", reply_markup=skip_or_upload_kb(),
    )


async def _youtube_finish(message_or_callback, state: FSMContext, telegram_id: int, has_image: bool):
    data = await state.get_data()
    header = await _user_header(message_or_callback.from_user)
    image_label = "Ha" if has_image else "Yo'q"
    lines = header + [
        "📄 Xizmat: YouTube banner",
        f"📺 Kanal nomi: {data['channel_name']}",
        f"🔗 Bannerda ko'rinishi kerak: {data['contacts']}",
        f"🖼 Tayyor rasm yuborildimi: {image_label}",
        f"💰 Narx: {format_som(YOUTUBE_BANNER_PRICE)} so'm",
        f"USER_ID: {telegram_id}",
        f"🕒 Sana/vaqt: {_now()}",
    ]
    target = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
    await begin_confirmation(
        target, state,
        flow_kind="service", telegram_id=telegram_id, service_type="youtube_banner",
        topic="YouTube banner", summary_text="\n".join(lines), price_som=YOUTUBE_BANNER_PRICE,
        group_lines=lines,
        preview_text=f"<b>YouTube banner</b> — narxi <b>{format_som(YOUTUBE_BANNER_PRICE)} so'm</b>.\n\nTasdiqlaysizmi?",
    )


@router.message(YoutubeBanner.waiting_image, F.photo)
async def youtube_image(message: Message, state: FSMContext):
    await state.update_data(image_file_id=message.photo[-1].file_id)
    await _youtube_finish(message, state, message.from_user.id, True)


@router.callback_query(YoutubeBanner.waiting_image, F.data == "skip")
async def youtube_skip_image(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await _youtube_finish(callback, state, callback.from_user.id, False)


# ==================== LOGO ====================

@router.callback_query(F.data == "biz:logo")
async def logo_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(LogoOrder.waiting_colors)
    await callback.message.answer("Logo uchun qanday rang(lar) xohlaysiz?")
    await callback.answer()


@router.message(LogoOrder.waiting_colors)
async def logo_colors(message: Message, state: FSMContext):
    await state.update_data(colors=message.text.strip())
    await state.set_state(LogoOrder.waiting_name)
    await message.answer("Logoda qatnashadigan nom (brend nomi) qanday bo'lsin?")


@router.message(LogoOrder.waiting_name)
async def logo_name(message: Message, state: FSMContext):
    await state.update_data(brand_name=message.text.strip())
    await state.set_state(LogoOrder.waiting_image)
    await message.answer(
        "Agar ilhom uchun namunaviy rasm bo'lsa yuboring (ixtiyoriy):",
        reply_markup=skip_or_upload_kb(),
    )


@router.message(LogoOrder.waiting_image, F.photo)
async def logo_image(message: Message, state: FSMContext):
    await state.update_data(image_file_id=message.photo[-1].file_id)
    await state.set_state(LogoOrder.waiting_direction)
    await message.answer("Biznes yo'nalishingizni kiriting:")


@router.callback_query(LogoOrder.waiting_image, F.data == "skip")
async def logo_skip_image(callback: CallbackQuery, state: FSMContext):
    await state.set_state(LogoOrder.waiting_direction)
    await callback.message.answer("Biznes yo'nalishingizni kiriting:")
    await callback.answer()


@router.message(LogoOrder.waiting_direction)
async def logo_direction(message: Message, state: FSMContext):
    await state.update_data(direction=message.text.strip())
    await state.set_state(LogoOrder.waiting_about)
    await message.answer("Biznesingiz haqida qisqacha ma'lumot bering:")


@router.message(LogoOrder.waiting_about)
async def logo_about(message: Message, state: FSMContext):
    data_extra = message.text.strip()
    data = await state.get_data()
    from bot.database import get_user
    telegram_id = message.from_user.id
    user = await get_user(telegram_id)
    phone = (user.get("phone") if user else None) or "O'tkazib yuborgan"
    username = message.from_user.username or "-"
    lo, hi = LOGO_PRICE_RANGE
    sample_image_label = "Ha" if data.get('image_file_id') else "Yo'q"
    lines = [
        f"👤 Ism: {message.from_user.full_name}",
        f"🔗 Username: @{username}",
        f"📞 Telefon raqam: {phone}",
        "📄 Xizmat: Logo",
        f"🎨 Rang(lar): {data['colors']}",
        f"🏷 Brend nomi: {data['brand_name']}",
        f"🖼 Namunaviy rasm: {sample_image_label}",
        f"🏢 Yo'nalish: {data['direction']}",
        f"ℹ️ Biznes haqida: {data_extra}",
        f"💰 Taxminiy narx: {format_som(lo)} - {format_som(hi)} so'm (aniq narx admin bilan kelishiladi)",
        f"USER_ID: {telegram_id}",
        f"🕒 Sana/vaqt: {_now()}",
    ]
    await begin_confirmation(
        message, state,
        flow_kind="service", telegram_id=telegram_id, service_type="logo",
        topic="Logo", summary_text="\n".join(lines), price_som=None,
        group_lines=lines,
        preview_text=(
            f"<b>Logo</b> buyurtmasi — taxminiy narx {format_som(lo)}-{format_som(hi)} so'm "
            "(admin bilan yakuniy kelishiladi).\n\nTasdiqlaysizmi?"
        ),
    )


# ==================== QR-GENERATOR ====================

@router.callback_query(F.data == "biz:qr")
async def qr_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(QrGenerator.waiting_link)
    await callback.message.answer("QR-kodga aylantirish uchun linkni yuboring:")
    await callback.answer()


@router.message(QrGenerator.waiting_link)
async def qr_link(message: Message, state: FSMContext):
    link = message.text.strip()
    if not (link.startswith("http://") or link.startswith("https://")):
        await message.answer("Iltimos, to'g'ri link yuboring (http:// yoki https:// bilan boshlanishi kerak).")
        return
    telegram_id = message.from_user.id
    from bot.database import get_user
    user = await get_user(telegram_id)
    phone = (user.get("phone") if user else None) or "O'tkazib yuborgan"
    username = message.from_user.username or "-"
    lines = [
        f"👤 Ism: {message.from_user.full_name}",
        f"🔗 Username: @{username}",
        f"📞 Telefon raqam: {phone}",
        "📄 Xizmat: QR-generator",
        f"🔗 Link: {link}",
        f"💰 Narx: {format_som(QR_GENERATOR_PRICE)} so'm",
        f"USER_ID: {telegram_id}",
        f"🕒 Sana/vaqt: {_now()}",
    ]
    await begin_confirmation(
        message, state,
        flow_kind="service", telegram_id=telegram_id, service_type="qr_generator",
        topic="QR-generator", summary_text="\n".join(lines), price_som=QR_GENERATOR_PRICE,
        group_lines=lines,
        preview_text=f"<b>QR-generator</b> — narxi <b>{format_som(QR_GENERATOR_PRICE)} so'm</b>.\n\nTasdiqlaysizmi?",
    )
