from enum import Enum
from aiogram.filters.callback_data import CallbackData

class MenuAction(str, Enum):
    help = "help"
    new_project = "new_project"
    cancel_pay = "cancel_pay"
    my_projects = "my_projects"
    my_offers = "my_offers"
    support = "support"
    teams = "teams"
    view_all_master = "view_all_master"
    view_pending = "view_pending"
    view_accepted = "view_accepted"
    view_history = "view_history"
    view_payments = "view_payments"
    admin_broadcast = "admin_broadcast"
    admin_tickets = "admin_tickets"
    admin_urgent_cases = "admin_urgent_cases"
    back_to_admin = "back_to_admin"
    close_list = "close_list"
    cancel_flow = "cancel_flow"

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
    admin_tickets_page = "admin_tickets_page"
    find_teams = "find_teams"
    my_teams = "my_teams"
    my_cmp_teams = "my_cmp_teams"
    my_pending_joins = "my_pending_joins"

class TicketAction(str, Enum):
    open_new = "open_new"
    list_active = "list_active"
    list_closed = "list_closed"
    view = "view"
    reply = "reply"
    close = "close"
    reopen = "reopen"
    back = "back"
    cancel_action = "cancel_action"

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

class DateConfirmAction(str, Enum):
    accept = "accept"
    reject = "reject"

class DateConfirmCallback(CallbackData, prefix="dateconf"):
    """Callback for Gemini-parsed date confirmation."""
    action: DateConfirmAction
    date: str  # YYYY-MM-DD

class TeamAction(str, Enum):
    create = "create"
    find = "find"
    select_course = "sel_course"
    select_count = "sel_count"
    join = "join"
    accept_join = "acc_join"
    reject_join = "rej_join"
    my_teams = "my_teams"
    my_completed_teams = "my_cmp_teams"
    my_pending_joins = "my_pend_joins"
    manage = "manage"
    close = "close"
    delete = "delete"
    withdraw = "withdraw"
    back = "back"

class TeamCallback(CallbackData, prefix="team"):
    """Callback for team matchmaking actions."""
    action: TeamAction
    id: int = 0
    data: str = ""

class ProfileCallback(CallbackData, prefix="profile"):
    """Callback for profile-related actions."""
    action: str
    spec: str = ""
