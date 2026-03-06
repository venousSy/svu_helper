"""
Client Keyboard Module
======================
Constructs inline keyboards for student interactions, such as viewing offers.
"""

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


from keyboards.callbacks import MenuCallback, ProjectCallback

def get_offer_actions_kb(proj_id: int) -> types.InlineKeyboardMarkup:
    """Buttons for student to accept or deny an offer."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="✅ قبول",
            callback_data=ProjectCallback(action="accept", id=proj_id).pack(),
        )
    )  # Accept
    builder.row(
        types.InlineKeyboardButton(
            text="❌ رفض",
            callback_data=ProjectCallback(action="deny", id=proj_id).pack(),
        )
    )  # Deny
    return builder.as_markup()


def get_offers_list_kb(offers):
    """Buttons to view specific offers from a list."""
    builder = InlineKeyboardBuilder()
    for item in offers:
        p_id = item["id"]

        builder.row(
            types.InlineKeyboardButton(
                text=f"عرض العرض #{p_id}",  # View Offer
                callback_data=ProjectCallback(action="view_offer", id=p_id).pack(),
            )
        )
    return builder.as_markup()


def get_cancel_payment_kb() -> types.InlineKeyboardMarkup:
    """Button to cancel the payment upload process."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="❌ إلغاء", 
            callback_data=MenuCallback(action="cancel_pay").pack()
        )
    )
    return builder.as_markup()
