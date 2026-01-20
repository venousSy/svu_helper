"""
Client Keyboard Module
======================
Constructs inline keyboards for student interactions, such as viewing offers.
"""

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_offer_actions_kb(proj_id: int) -> types.InlineKeyboardMarkup:
    """Buttons for student to accept or deny an offer."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ قبول", callback_data=f"accept_{proj_id}")) # Accept
    builder.row(types.InlineKeyboardButton(text="❌ رفض", callback_data=f"deny_{proj_id}")) # Deny
    return builder.as_markup()

def get_offers_list_kb(offers):
    """Buttons to view specific offers from a list."""
    builder = InlineKeyboardBuilder()
    for item in offers:
        if isinstance(item, dict):
            p_id = item['id']
        else:
            p_id = item[0]

        builder.row(types.InlineKeyboardButton(
            text=f"عرض العرض #{p_id}", # View Offer
            callback_data=f"view_offer_{p_id}"
        ))
    return builder.as_markup()
