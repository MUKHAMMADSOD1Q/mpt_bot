from aiogram.fsm.state import State, StatesGroup


class OrderPresentation(StatesGroup):
    waiting_topic = State()
    waiting_pages = State()
    waiting_fullname = State()
    waiting_institution = State()
    waiting_direction = State()
    waiting_language = State()
    waiting_tariff = State()


class ManualPresentation(StatesGroup):
    waiting_essay = State()
    waiting_photos = State()


class PreCal(StatesGroup):
    waiting_tariff = State()
    waiting_pages = State()
    waiting_language = State()
    waiting_approval = State()


class IndependentWork(StatesGroup):
    waiting_type = State()
    waiting_topic = State()
    waiting_pages = State()
    waiting_images = State()
    waiting_graphics = State()
    waiting_language = State()


class Taklifnoma(StatesGroup):
    waiting_date = State()
    waiting_couple_names = State()
    waiting_venue = State()
    waiting_extra = State()


class UiDesign(StatesGroup):
    waiting_platform = State()
    waiting_business_type = State()
    waiting_business_size = State()
    waiting_extra = State()


class WebsiteOrder(StatesGroup):
    waiting_business_type = State()
    waiting_style = State()
    waiting_extra = State()


class ResumeOrder(StatesGroup):
    waiting_fullname = State()
    waiting_birthdate = State()
    waiting_contact = State()
    waiting_education = State()
    waiting_experience = State()
    waiting_skills = State()
    waiting_languages = State()
    waiting_extra = State()


class YoutubeBanner(StatesGroup):
    waiting_channel_name = State()
    waiting_contacts = State()
    waiting_image = State()


class LogoOrder(StatesGroup):
    waiting_colors = State()
    waiting_name = State()
    waiting_image = State()
    waiting_direction = State()
    waiting_about = State()


class QrGenerator(StatesGroup):
    waiting_link = State()


# Har qanday buyurtma (taqdimot yoki xizmat) uchun umumiy ikki bosqichli tasdiqlash
class OrderConfirm(StatesGroup):
    confirm1 = State()
    confirm2 = State()


class ClickPayment(StatesGroup):
    waiting_app_choice = State()
    waiting_phone = State()
    playing_game = State()


class CardPayment(StatesGroup):
    waiting_phone = State()
    waiting_receipt = State()


class AdminBroadcast(StatesGroup):
    waiting_target_id = State()
    waiting_single_message = State()
    waiting_broadcast_message = State()


class AdminSetPrice(StatesGroup):
    waiting_amount = State()
