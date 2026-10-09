from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

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
from bot.i18n import menu_labels, tr
from bot.services.user_locale import localized_main_menu, get_user_locale

router = Router()


async def _show_previous(message: Message, state: FSMContext, previous, prompt: str, keyboard=None):
    await state.set_state(previous)
    await message.answer(prompt, reply_markup=keyboard)


@router.message(F.text.in_(menu_labels("back")))
async def go_back(message: Message, state: FSMContext):
    await _go_back_action(message, state, message.from_user.id)


@router.callback_query(F.data == "nav:back")
async def go_back_from_options(callback: CallbackQuery, state: FSMContext):
    if isinstance(callback.message, Message):
        await _go_back_action(callback.message, state, callback.from_user.id)
    await callback.answer()


async def _go_back_action(message: Message, state: FSMContext, user_id: int):
    language = await get_user_locale(user_id)
    current = await state.get_state()
    data = await state.get_data()

    if current == PreCal.waiting_pages.state:
        await _show_previous(message, state, PreCal.waiting_tariff,
                             tr(language, "tariff_prompt"), precal_tariff_kb(language))
    elif current == PreCal.waiting_tariff.state:
        await state.clear()
        await message.answer(tr(language, "return_presentation"), reply_markup=await localized_main_menu(user_id))
    elif current in (PreCal.waiting_language.state, PreCal.waiting_approval.state):
        await _show_previous(message, state, PreCal.waiting_pages, tr(language, "pages_enter"))
    elif current == OrderPresentation.waiting_pages.state:
        prompt_key = "manual_topic_prompt" if data.get("manual_mode") else "topic_prompt"
        await _show_previous(message, state, OrderPresentation.waiting_topic, tr(language, prompt_key))
    elif current == OrderPresentation.waiting_topic.state:
        await state.clear()
        return_key = "return_menu" if data.get("ai_only_free") else "return_presentation"
        await message.answer(
            tr(language, return_key),
            reply_markup=await localized_main_menu(user_id),
        )
    elif current == OrderPresentation.waiting_fullname.state:
        previous = OrderPresentation.waiting_topic if data.get("precal") else OrderPresentation.waiting_pages
        if data.get("precal"):
            prompt_key = "manual_topic_prompt" if data.get("manual_mode") else "topic_prompt"
        else:
            prompt_key = "manual_pages_prompt" if data.get("manual_mode") else "pages_prompt"
        prompt = tr(language, prompt_key)
        await _show_previous(message, state, previous, prompt)
    elif current == OrderPresentation.waiting_institution.state:
        await _show_previous(message, state, OrderPresentation.waiting_fullname,
                             tr(language, "manual_fullname_prompt" if data.get("manual_mode") else "fullname_prompt"))
    elif current == OrderPresentation.waiting_direction.state:
        await _show_previous(message, state, OrderPresentation.waiting_institution,
                             tr(language, "manual_institution_prompt" if data.get("manual_mode") else "institution_prompt"),
                             skip_kb(language))
    elif current == OrderPresentation.waiting_language.state:
        await _show_previous(message, state, OrderPresentation.waiting_direction,
                             tr(language, "manual_direction_prompt" if data.get("manual_mode") else "direction_prompt"),
                             skip_kb(language))
    elif current == OrderPresentation.waiting_tariff.state:
        await _show_previous(message, state, OrderPresentation.waiting_language,
                             tr(language, "manual_language_prompt" if data.get("manual_mode") else "output_language_prompt"),
                             language_choice_kb("pres_lang", language))
    elif current == OrderConfirm.confirm1.state:
        if data.get("flow_kind") == "presentation":
            await _show_previous(message, state, OrderPresentation.waiting_tariff,
                                 tr(language, "tariff_prompt"), tariff_kb(language))
        else:
            service_type = data.get("service_type", "")
            if service_type.startswith("mustaqil_ish:"):
                await _show_previous(message, state, IndependentWork.waiting_language,
                                     tr(language, "language_question"), language_choice_kb("iw_lang", language))
                return
            last_steps = {
                "taklifnoma": (Taklifnoma.waiting_extra, tr(language, "optional_design_notes"), skip_kb(language)),
                "ui_dizayn": (UiDesign.waiting_extra, tr(language, "extra_optional"), skip_kb(language)),
                "web_sayt": (WebsiteOrder.waiting_extra, tr(language, "website_extra"), skip_kb(language)),
                "rezyume": (ResumeOrder.waiting_extra, tr(language, "resume_extra"), skip_kb(language)),
                "youtube_banner": (YoutubeBanner.waiting_image, tr(language, "sample_image"), skip_or_upload_kb(language)),
                "logo": (LogoOrder.waiting_about, tr(language, "business_about"), None),
                "qr_generator": (QrGenerator.waiting_link, tr(language, "qr_link"), None),
            }
            if service_type in last_steps:
                await _show_previous(message, state, *last_steps[service_type])
            else:
                await state.clear()
                await message.answer(tr(language, "return_services"), reply_markup=business_services_kb(language))
    elif current == OrderConfirm.confirm2.state:
        await _show_previous(message, state, OrderConfirm.confirm1,
                             tr(language, "confirm_again"), confirm1_kb(language))
    elif current == IndependentWork.waiting_topic.state:
        await _show_previous(message, state, IndependentWork.waiting_type,
                             tr(language, "ind_type"), independent_work_type_kb(language))
    elif current == IndependentWork.waiting_type.state:
        await state.clear()
        await message.answer(tr(language, "return_menu"), reply_markup=await localized_main_menu(user_id))
    elif current == IndependentWork.waiting_pages.state:
        await _show_previous(message, state, IndependentWork.waiting_topic, tr(language, "topic_enter"))
    elif current == IndependentWork.waiting_images.state:
        await _show_previous(message, state, IndependentWork.waiting_pages,
                             tr(language, "pages_enter"))
    elif current == IndependentWork.waiting_graphics.state:
        await _show_previous(message, state, IndependentWork.waiting_images,
                             tr(language, "images_question"), yes_no_kb("iw_img", language))
    elif current == IndependentWork.waiting_language.state:
        await _show_previous(message, state, IndependentWork.waiting_graphics,
                             tr(language, "graphics_question"), yes_no_kb("iw_graf", language))
    elif current == ClickPayment.waiting_app_choice.state:
        await _show_previous(message, state, None, tr(language, "payment_method_prompt"), payment_method_kb(language))
    elif current == ClickPayment.waiting_phone.state:
        await _show_previous(message, state, ClickPayment.waiting_app_choice,
                             tr(language, "click_intro"), click_app_choice_kb(language))
    elif current == CardPayment.waiting_phone.state:
        await _show_previous(message, state, None, tr(language, "payment_method_prompt"), payment_method_kb(language))
    elif current == ClickPayment.playing_game.state:
        merchant_trans_id = data.get("game_merchant_trans_id")
        from bot.database import get_click_payment
        from bot.services.click_api import build_checkout_url
        payment = await get_click_payment(merchant_trans_id) if merchant_trans_id else None
        await state.clear()
        if payment:
            await message.answer(tr(language, "return_payment"), reply_markup=await localized_main_menu(user_id))
            await message.answer(
                tr(language, "continue_payment"),
                reply_markup=click_wait_kb(merchant_trans_id, build_checkout_url(payment["amount_som"], merchant_trans_id), language),
            )
        else:
            await message.answer(tr(language, "return_menu"), reply_markup=await localized_main_menu(user_id))
    elif current == CardPayment.waiting_receipt.state:
        await _show_previous(message, state, CardPayment.waiting_phone,
                             tr(language, "card_phone_prompt"))
    elif current in (Taklifnoma.waiting_couple_names.state, Taklifnoma.waiting_venue.state,
                     Taklifnoma.waiting_extra.state):
        previous = {
            Taklifnoma.waiting_couple_names.state: (Taklifnoma.waiting_date, tr(language, "wedding_date"), None),
            Taklifnoma.waiting_venue.state: (Taklifnoma.waiting_couple_names, tr(language, "wedding_names"), None),
            Taklifnoma.waiting_extra.state: (Taklifnoma.waiting_venue, tr(language, "wedding_venue"), None),
        }[current]
        await _show_previous(message, state, *previous)
    elif current in (UiDesign.waiting_business_type.state, UiDesign.waiting_business_size.state,
                     UiDesign.waiting_extra.state):
        previous = {
            UiDesign.waiting_business_type.state: (UiDesign.waiting_platform, tr(language, "design_purpose"), ui_platform_kb(language)),
            UiDesign.waiting_business_size.state: (UiDesign.waiting_business_type, tr(language, "business_type_example"), None),
            UiDesign.waiting_extra.state: (UiDesign.waiting_business_size, tr(language, "business_size"), business_size_kb(language)),
        }[current]
        await _show_previous(message, state, *previous)
    elif current in (WebsiteOrder.waiting_style.state, WebsiteOrder.waiting_extra.state):
        previous = {
            WebsiteOrder.waiting_style.state: (WebsiteOrder.waiting_business_type, tr(language, "website_business_example"), None),
            WebsiteOrder.waiting_extra.state: (WebsiteOrder.waiting_style, tr(language, "website_style"), website_style_kb(language)),
        }[current]
        await _show_previous(message, state, *previous)
    elif current in (ResumeOrder.waiting_birthdate.state, ResumeOrder.waiting_contact.state,
                     ResumeOrder.waiting_education.state, ResumeOrder.waiting_experience.state,
                     ResumeOrder.waiting_skills.state, ResumeOrder.waiting_languages.state,
                     ResumeOrder.waiting_extra.state):
        previous = {
            ResumeOrder.waiting_birthdate.state: (ResumeOrder.waiting_fullname, tr(language, "fullname_enter")),
            ResumeOrder.waiting_contact.state: (ResumeOrder.waiting_birthdate, tr(language, "birthdate_enter")),
            ResumeOrder.waiting_education.state: (ResumeOrder.waiting_contact, tr(language, "resume_contact")),
            ResumeOrder.waiting_experience.state: (ResumeOrder.waiting_education, tr(language, "resume_education")),
            ResumeOrder.waiting_skills.state: (ResumeOrder.waiting_experience, tr(language, "resume_experience")),
            ResumeOrder.waiting_languages.state: (ResumeOrder.waiting_skills, tr(language, "resume_skills")),
            ResumeOrder.waiting_extra.state: (ResumeOrder.waiting_languages, tr(language, "resume_languages")),
        }[current]
        await _show_previous(message, state, *previous)
    elif current in (YoutubeBanner.waiting_contacts.state, YoutubeBanner.waiting_image.state):
        previous = {
            YoutubeBanner.waiting_contacts.state: (YoutubeBanner.waiting_channel_name, tr(language, "youtube_channel")),
            YoutubeBanner.waiting_image.state: (YoutubeBanner.waiting_contacts, tr(language, "youtube_contacts")),
        }[current]
        await _show_previous(message, state, *previous)
    elif current in (LogoOrder.waiting_name.state, LogoOrder.waiting_image.state,
                     LogoOrder.waiting_direction.state, LogoOrder.waiting_about.state):
        previous = {
            LogoOrder.waiting_name.state: (LogoOrder.waiting_colors, tr(language, "logo_colors")),
            LogoOrder.waiting_image.state: (LogoOrder.waiting_name, tr(language, "logo_name")),
            LogoOrder.waiting_direction.state: (LogoOrder.waiting_image, tr(language, "sample_image"), skip_or_upload_kb(language)),
            LogoOrder.waiting_about.state: (LogoOrder.waiting_direction, tr(language, "business_direction")),
        }[current]
        await _show_previous(message, state, *previous)
    elif current in (QrGenerator.waiting_link.state, YoutubeBanner.waiting_channel_name.state,
                     LogoOrder.waiting_colors.state, Taklifnoma.waiting_date.state,
                     UiDesign.waiting_platform.state, WebsiteOrder.waiting_business_type.state,
                     ResumeOrder.waiting_fullname.state):
        await state.clear()
        await message.answer(tr(language, "return_services"), reply_markup=business_services_kb(language))
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
            tr(language, "return_products"),
            reply_markup=await localized_main_menu(user_id),
        )
    else:
        await state.clear()
        user = await get_user(user_id)
        markup = (
            admin_menu_kb(super_admin=user_id == OWNER_ID)
            if user and user.get("is_admin_mode") else await localized_main_menu(user_id)
        )
        await message.answer(tr(language, "return_menu"), reply_markup=markup)