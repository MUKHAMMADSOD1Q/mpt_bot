from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import OWNER_ID
from bot.keyboards import (
    admin_menu_kb, business_services_kb, business_size_kb, click_app_choice_kb, click_wait_kb, independent_work_type_kb,
    language_choice_kb, precal_tariff_kb,
    skip_kb, skip_or_upload_kb, tariff_kb, ui_platform_kb,
    website_style_kb, yes_no_kb,
)
from bot.services.group_orders import confirm1_kb
from bot.services.payment_common import payment_method_kb
from bot.states import (
    AdminBroadcast, AdminSetPrice, CardPayment, ClickPayment, IndependentWork,
    LogoOrder, OrderConfirm, OrderPresentation, PreCal, QrGenerator, ResumeOrder,
    Taklifnoma, UiDesign, WebsiteOrder, YoutubeBanner,
)
from bot.handlers.soff_browse import SoffSearch
from bot.database import get_user
from bot.i18n import menu_labels
from bot.services.user_locale import localized_main_menu

router = Router()


async def _show_previous(message: Message, state: FSMContext, previous, prompt: str, keyboard=None):
    await state.set_state(previous)
    await message.answer(prompt, reply_markup=keyboard)


@router.message(F.text.in_(menu_labels("back")))
async def go_back(message: Message, state: FSMContext):
    current = await state.get_state()
    data = await state.get_data()

    if current == PreCal.waiting_pages.state:
        await _show_previous(message, state, PreCal.waiting_tariff,
                             "Qaysi ta'rifda hisoblaymiz?", precal_tariff_kb())
    elif current == PreCal.waiting_tariff.state:
        await state.clear()
        await message.answer("Taqdimot bo'limiga qaytdingiz.", reply_markup=await localized_main_menu(message.from_user.id))
    elif current in (PreCal.waiting_language.state, PreCal.waiting_approval.state):
        await _show_previous(message, state, PreCal.waiting_pages, "Taqdimot nechta sahifali bo'lsin?")
    elif current == OrderPresentation.waiting_pages.state:
        await _show_previous(message, state, OrderPresentation.waiting_topic, "Mavzu nomini kiriting:")
    elif current == OrderPresentation.waiting_topic.state:
        await state.clear()
        await message.answer("Taqdimot bo'limiga qaytdingiz.", reply_markup=await localized_main_menu(message.from_user.id))
    elif current == OrderPresentation.waiting_fullname.state:
        previous = OrderPresentation.waiting_topic if data.get("precal") else OrderPresentation.waiting_pages
        prompt = "Taqdimot mavzusini kiriting:" if data.get("precal") else "Taqdimotingiz nechta sahifali bo'lsin?"
        await _show_previous(message, state, previous, prompt)
    elif current == OrderPresentation.waiting_institution.state:
        await _show_previous(message, state, OrderPresentation.waiting_fullname,
                             "Ism-familiyangizni kiriting:")
    elif current == OrderPresentation.waiting_direction.state:
        await _show_previous(message, state, OrderPresentation.waiting_institution,
                             "Ta'lim muassasasi nomini kiriting (ixtiyoriy):", skip_kb())
    elif current == OrderPresentation.waiting_language.state:
        await _show_previous(message, state, OrderPresentation.waiting_direction,
                             "Yo'nalish nomi va guruhingizni kiriting (ixtiyoriy):", skip_kb())
    elif current == OrderPresentation.waiting_tariff.state:
        await _show_previous(message, state, OrderPresentation.waiting_language,
                             "Taqdimot qaysi tilda tayyorlansin?", language_choice_kb("pres_lang"))
    elif current == OrderConfirm.confirm1.state:
        if data.get("flow_kind") == "presentation":
            await _show_previous(message, state, OrderPresentation.waiting_tariff,
                                 "Ta'rif turini tanlang:", tariff_kb())
        else:
            service_type = data.get("service_type", "")
            if service_type.startswith("mustaqil_ish:"):
                await _show_previous(message, state, IndependentWork.waiting_language,
                                     "Ish qaysi tilda bajarilsin?", language_choice_kb("iw_lang"))
                return
            last_steps = {
                "taklifnoma": (Taklifnoma.waiting_extra, "Qo'shimcha talablaringiz bormi?", skip_kb()),
                "ui_dizayn": (UiDesign.waiting_extra, "Qo'shimcha talablaringiz bormi?", skip_kb()),
                "web_sayt": (WebsiteOrder.waiting_extra, "Qo'shimcha talablaringiz bormi?", skip_kb()),
                "rezyume": (ResumeOrder.waiting_extra, "Qo'shimcha ma'lumot bormi?", skip_kb()),
                "youtube_banner": (YoutubeBanner.waiting_image, "Namuna rasmini yuboring yoki o'tkazib yuboring:", skip_or_upload_kb()),
                "logo": (LogoOrder.waiting_about, "Logo haqida qisqacha ma'lumot bering:", None),
                "qr_generator": (QrGenerator.waiting_link, "QR-kod uchun havolani yuboring:", None),
            }
            if service_type in last_steps:
                await _show_previous(message, state, *last_steps[service_type])
            else:
                await state.clear()
                await message.answer("Xizmat tanlash bo'limiga qaytdingiz.", reply_markup=business_services_kb())
    elif current == OrderConfirm.confirm2.state:
        await _show_previous(message, state, OrderConfirm.confirm1,
                             "Buyurtma ma'lumotlarini yana bir bor tasdiqlaysizmi?", confirm1_kb())
    elif current == IndependentWork.waiting_topic.state:
        await _show_previous(message, state, IndependentWork.waiting_type,
                             "Ish turini tanlang:", independent_work_type_kb())
    elif current == IndependentWork.waiting_type.state:
        await state.clear()
        await message.answer("Bosh menyuga qaytdingiz.", reply_markup=await localized_main_menu(message.from_user.id))
    elif current == IndependentWork.waiting_pages.state:
        await _show_previous(message, state, IndependentWork.waiting_topic, "Mavzu nomini kiriting:")
    elif current == IndependentWork.waiting_images.state:
        await _show_previous(message, state, IndependentWork.waiting_pages,
                             "Nechta sahifali bo'lishi kerak?")
    elif current == IndependentWork.waiting_graphics.state:
        await _show_previous(message, state, IndependentWork.waiting_images,
                             "Ish ichida rasm bo'lsinmi?", yes_no_kb("iw_img"))
    elif current == IndependentWork.waiting_language.state:
        await _show_previous(message, state, IndependentWork.waiting_graphics,
                             "Grafika va jadvallar kerakmi?", yes_no_kb("iw_graf"))
    elif current == ClickPayment.waiting_app_choice.state:
        await _show_previous(message, state, None, "To'lov usulini tanlang:", payment_method_kb())
    elif current == ClickPayment.waiting_phone.state:
        await _show_previous(message, state, ClickPayment.waiting_app_choice,
                             "ClickSuperApp ilovasi qurilmangizda bormi?", click_app_choice_kb())
    elif current == CardPayment.waiting_phone.state:
        await _show_previous(message, state, None, "To'lov usulini tanlang:", payment_method_kb())
    elif current == ClickPayment.playing_game.state:
        merchant_trans_id = data.get("game_merchant_trans_id")
        from bot.database import get_click_payment
        from bot.services.click_api import build_checkout_url
        payment = await get_click_payment(merchant_trans_id) if merchant_trans_id else None
        await state.clear()
        if payment:
            await message.answer("To'lov jarayoniga qaytdingiz.", reply_markup=await localized_main_menu(message.from_user.id))
            await message.answer(
                "To'lovni davom ettiring yoki holatini tekshiring.",
                reply_markup=click_wait_kb(merchant_trans_id, build_checkout_url(payment["amount_som"], merchant_trans_id)),
            )
        else:
            await message.answer("Bosh menyuga qaytdingiz.", reply_markup=await localized_main_menu(message.from_user.id))
    elif current == CardPayment.waiting_receipt.state:
        await _show_previous(message, state, CardPayment.waiting_phone,
                             "Telefon raqamingizni qayta kiriting:")
    elif current in (Taklifnoma.waiting_couple_names.state, Taklifnoma.waiting_venue.state,
                     Taklifnoma.waiting_extra.state):
        previous = {
            Taklifnoma.waiting_couple_names.state: (Taklifnoma.waiting_date, "To'y kunini kiriting:", None),
            Taklifnoma.waiting_venue.state: (Taklifnoma.waiting_couple_names, "Kelin-kuyov ism-familiyasini kiriting:", None),
            Taklifnoma.waiting_extra.state: (Taklifnoma.waiting_venue, "To'yxona manzilini kiriting:", None),
        }[current]
        await _show_previous(message, state, *previous)
    elif current in (UiDesign.waiting_business_type.state, UiDesign.waiting_business_size.state,
                     UiDesign.waiting_extra.state):
        previous = {
            UiDesign.waiting_business_type.state: (UiDesign.waiting_platform, "Dizayn nima uchun kerak?", ui_platform_kb()),
            UiDesign.waiting_business_size.state: (UiDesign.waiting_business_type, "Biznes turingizni kiriting:", None),
            UiDesign.waiting_extra.state: (UiDesign.waiting_business_size, "Biznesingiz hajmi qanday?", business_size_kb()),
        }[current]
        await _show_previous(message, state, *previous)
    elif current in (WebsiteOrder.waiting_style.state, WebsiteOrder.waiting_extra.state):
        previous = {
            WebsiteOrder.waiting_style.state: (WebsiteOrder.waiting_business_type, "Tadbirkorlik turingizni kiriting:", None),
            WebsiteOrder.waiting_extra.state: (WebsiteOrder.waiting_style, "Qaysi uslubda sayt kerak?", website_style_kb()),
        }[current]
        await _show_previous(message, state, *previous)
    elif current in (ResumeOrder.waiting_birthdate.state, ResumeOrder.waiting_contact.state,
                     ResumeOrder.waiting_education.state, ResumeOrder.waiting_experience.state,
                     ResumeOrder.waiting_skills.state, ResumeOrder.waiting_languages.state,
                     ResumeOrder.waiting_extra.state):
        previous = {
            ResumeOrder.waiting_birthdate.state: (ResumeOrder.waiting_fullname, "Ism-familiyangizni kiriting:"),
            ResumeOrder.waiting_contact.state: (ResumeOrder.waiting_birthdate, "Tug'ilgan sanangizni kiriting:"),
            ResumeOrder.waiting_education.state: (ResumeOrder.waiting_contact, "Aloqa ma'lumotlarini kiriting:"),
            ResumeOrder.waiting_experience.state: (ResumeOrder.waiting_education, "Ta'lim ma'lumotlarini kiriting:"),
            ResumeOrder.waiting_skills.state: (ResumeOrder.waiting_experience, "Ish tajribangizni kiriting:"),
            ResumeOrder.waiting_languages.state: (ResumeOrder.waiting_skills, "Ko'nikmalaringizni kiriting:"),
            ResumeOrder.waiting_extra.state: (ResumeOrder.waiting_languages, "Qaysi tillarni bilasiz?"),
        }[current]
        await _show_previous(message, state, *previous)
    elif current in (YoutubeBanner.waiting_contacts.state, YoutubeBanner.waiting_image.state):
        previous = {
            YoutubeBanner.waiting_contacts.state: (YoutubeBanner.waiting_channel_name, "YouTube kanal nomini kiriting:"),
            YoutubeBanner.waiting_image.state: (YoutubeBanner.waiting_contacts, "Aloqa ma'lumotlarini kiriting:"),
        }[current]
        await _show_previous(message, state, *previous)
    elif current in (LogoOrder.waiting_name.state, LogoOrder.waiting_image.state,
                     LogoOrder.waiting_direction.state, LogoOrder.waiting_about.state):
        previous = {
            LogoOrder.waiting_name.state: (LogoOrder.waiting_colors, "Logo ranglarini kiriting:"),
            LogoOrder.waiting_image.state: (LogoOrder.waiting_name, "Logo nomi yoki matnini kiriting:"),
            LogoOrder.waiting_direction.state: (LogoOrder.waiting_image, "Namuna rasmini yuboring yoki o'tkazib yuboring:", skip_or_upload_kb()),
            LogoOrder.waiting_about.state: (LogoOrder.waiting_direction, "Logo yo'nalishini tanlang:"),
        }[current]
        await _show_previous(message, state, *previous)
    elif current in (QrGenerator.waiting_link.state, YoutubeBanner.waiting_channel_name.state,
                     LogoOrder.waiting_colors.state, Taklifnoma.waiting_date.state,
                     UiDesign.waiting_platform.state, WebsiteOrder.waiting_business_type.state,
                     ResumeOrder.waiting_fullname.state):
        await state.clear()
        await message.answer("Xizmatlar tanloviga qaytdingiz.", reply_markup=business_services_kb())
    elif current == AdminBroadcast.waiting_single_message.state:
        await _show_previous(message, state, AdminBroadcast.waiting_target_id,
                             "Foydalanuvchining Telegram ID raqamini kiriting:")
    elif current in (AdminBroadcast.waiting_target_id.state, AdminBroadcast.waiting_broadcast_message.state,
                     AdminSetPrice.waiting_amount.state):
        await state.clear()
        await message.answer("Admin menyusiga qaytdingiz.")
    elif current == SoffSearch.waiting_query.state:
        await state.clear()
        await message.answer(
            "Tayyor mahsulotlar ro'yxatiga qaytdingiz.",
            reply_markup=await localized_main_menu(message.from_user.id),
        )
    else:
        await state.clear()
        user = await get_user(message.from_user.id)
        markup = (
            admin_menu_kb(super_admin=message.from_user.id == OWNER_ID)
            if user and user.get("is_admin_mode") else await localized_main_menu(message.from_user.id)
        )
        await message.answer("Menyuga qaytdingiz.", reply_markup=markup)