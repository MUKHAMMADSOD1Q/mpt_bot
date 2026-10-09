from aiogram import Router

from . import (
    navigation, admin, files_group, confirm_flow, payment_method, click_payment, card_payment,
    presentation_order, independent_work, business_services, soff_browse, balance, start,
    manual_presentation,
)


def get_root_router() -> Router:
    root = Router()
    # Commands and menu handlers must precede FSM catch-all handlers.
    root.include_router(start.router)
    root.include_router(admin.router)
    root.include_router(manual_presentation.router)
    root.include_router(navigation.router)
    root.include_router(files_group.router)
    root.include_router(confirm_flow.router)
    root.include_router(payment_method.router)
    root.include_router(click_payment.router)
    root.include_router(card_payment.router)
    root.include_router(presentation_order.router)
    root.include_router(independent_work.router)
    root.include_router(business_services.router)
    root.include_router(soff_browse.router)
    root.include_router(balance.router)
    return root
