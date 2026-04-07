"""
Client Keyboard Module
======================
Thin delegation layer – all keyboards are built by KeyboardFactory.
Import from keyboards.factory directly in new code.
"""
from keyboards.factory import KeyboardFactory


def get_offer_actions_kb(proj_id: int):
    return KeyboardFactory.offer_actions(proj_id)


def get_offers_list_kb(offers):
    return KeyboardFactory.offers_list(offers)


def get_cancel_payment_kb():
    return KeyboardFactory.cancel_payment()
