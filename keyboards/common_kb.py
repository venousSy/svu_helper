from aiogram.utils.keyboard import ReplyKeyboardBuilder
from utils.constants import BTN_NEW_PROJECT, BTN_MY_PROJECTS, BTN_MY_OFFERS

def get_student_main_kb():
    """Main persistent menu for students."""
    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_NEW_PROJECT)
    builder.button(text=BTN_MY_PROJECTS)
    builder.button(text=BTN_MY_OFFERS)
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)
