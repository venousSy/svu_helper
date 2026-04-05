"""
Common Keyboard Module
======================
Reusable UI components like the student main menu.
"""

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.callbacks import MenuCallback

from utils.constants import BTN_MY_OFFERS, BTN_MY_PROJECTS, BTN_NEW_PROJECT


def get_student_main_kb() -> types.InlineKeyboardMarkup:
    """Inline main menu for students."""
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_NEW_PROJECT, callback_data=MenuCallback(action="new_project").pack())
    builder.button(text=BTN_MY_PROJECTS, callback_data=MenuCallback(action="my_projects").pack())
    builder.button(text=BTN_MY_OFFERS, callback_data=MenuCallback(action="my_offers").pack())
    builder.button(text="ℹ️ المساعدة", callback_data=MenuCallback(action="help").pack())
    builder.adjust(1)
    return builder.as_markup()
