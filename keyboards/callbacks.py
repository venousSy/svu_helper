from aiogram.filters.callback_data import CallbackData

class ProjectCallback(CallbackData, prefix="proj"):
    action: str
    id: int

class PaymentCallback(CallbackData, prefix="pay"):
    action: str
    id: int

class MenuCallback(CallbackData, prefix="menu"):
    action: str

class PageCallback(CallbackData, prefix="page"):
    """Pagination callback for paged admin views."""
    action: str   # e.g. "all_projects"
    page: int     # 0-indexed page number
