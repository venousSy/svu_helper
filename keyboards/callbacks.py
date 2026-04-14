from enum import Enum
from aiogram.filters.callback_data import CallbackData

class MenuAction(str, Enum):
    help = "help"
    new_project = "new_project"
    cancel_pay = "cancel_pay"
    my_projects = "my_projects"
    my_offers = "my_offers"
    support = "support"
    view_all_master = "view_all_master"
    view_pending = "view_pending"
    view_accepted = "view_accepted"
    view_history = "view_history"
    view_payments = "view_payments"
    admin_broadcast = "admin_broadcast"
    back_to_admin = "back_to_admin"
    close_list = "close_list"

class ProjectAction(str, Enum):
    accept = "accept"
    view_offer = "view_offer"
    manage = "manage"
    make_offer = "make_offer"
    manage_accepted = "manage_accepted"
    deny = "deny"

class PaymentAction(str, Enum):
    view_receipt = "view_receipt"
    confirm = "confirm"
    reject = "reject"

class PageAction(str, Enum):
    my_projects = "my_projects"
    my_offers = "my_offers"
    all_projects = "all_projects"
    pending = "pending"
    accepted = "accepted"
    history = "history"
    payments = "payments"
    ticket_messages = "ticket_messages"

class TicketAction(str, Enum):
    open_new = "open_new"
    list_active = "list_active"
    view = "view"
    reply = "reply"
    close = "close"
    back = "back"

class ProjectCallback(CallbackData, prefix="proj"):
    action: ProjectAction
    id: int

class PaymentCallback(CallbackData, prefix="pay"):
    action: PaymentAction
    id: int

class MenuCallback(CallbackData, prefix="menu"):
    action: MenuAction

class PageCallback(CallbackData, prefix="page"):
    """Pagination callback for paged admin views."""
    action: PageAction
    page: int

class TicketCallback(CallbackData, prefix="tkt"):
    """Callback for ticket-related actions."""
    action: TicketAction
    id: int = 0   # ticket_id (0 = N/A for menu-level actions)

