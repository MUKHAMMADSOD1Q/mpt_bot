from aiogram import Router

from . import (
    start, presentation_order, independent_work, balance, admin,
    click_payment, card_payment, payment_method, soff_browse,
)


def get_root_router() -> Router:
    root = Router()
    root.include_router(admin.router)
    root.include_router(payment_method.router)
    root.include_router(click_payment.router)
    root.include_router(card_payment.router)
    root.include_router(soff_browse.router)
    root.include_router(start.router)
    root.include_router(presentation_order.router)
    root.include_router(independent_work.router)
    root.include_router(balance.router)
    return root
