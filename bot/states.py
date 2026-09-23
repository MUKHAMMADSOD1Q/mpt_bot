from aiogram.fsm.state import State, StatesGroup


class OrderPresentation(StatesGroup):
    waiting_topic = State()
    waiting_pages = State()
    waiting_fullname = State()
    waiting_institution = State()
    waiting_direction = State()
    waiting_language = State()
    waiting_tariff = State()
    confirm = State()


class ClickPayment(StatesGroup):
    waiting_phone = State()


class CardPayment(StatesGroup):
    waiting_phone = State()
    waiting_receipt = State()


class IndependentWork(StatesGroup):
    waiting_type = State()
    waiting_topic = State()
    waiting_pages = State()
    waiting_images = State()
    waiting_tables = State()
    waiting_language = State()
    waiting_extra = State()
    confirm = State()


class ServiceOrder(StatesGroup):
    waiting_service = State()
    waiting_topic = State()
    waiting_pages = State()
    waiting_detail = State()
    waiting_language = State()
    waiting_extra = State()
    confirm = State()


class AdminBroadcast(StatesGroup):
    waiting_target_id = State()
    waiting_single_message = State()
    waiting_broadcast_message = State()
