from aiogram.filters.callback_data import CallbackData

class ProjectCallback(CallbackData, prefix="proj"):
    action: str
    id: int

class PaymentCallback(CallbackData, prefix="pay"):
    action: str
    id: int

class MenuCallback(CallbackData, prefix="menu"):
    action: str
