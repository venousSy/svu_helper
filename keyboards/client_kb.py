from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_offer_actions_kb(proj_id):
    """Buttons for student to accept or deny an offer."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Accept", callback_data=f"accept_{proj_id}"))
    builder.row(types.InlineKeyboardButton(text="❌ Deny", callback_data=f"deny_{proj_id}"))
    return builder.as_markup()

def get_offers_list_kb(offers):
    """Buttons to view specific offers from a list."""
    builder = InlineKeyboardBuilder()
    for p_id, sub, _ in offers:
        builder.row(types.InlineKeyboardButton(
            text=f"View Offer #{p_id}", 
            callback_data=f"view_offer_{p_id}"
        ))
    return builder.as_markup()
