"""
Centralized constants for the SVU Helper Bot.
Now uses external JSON for internationalization (i18n).
"""
from utils.i18n import load_messages

# Load messages globally (at import time)
_msgs = load_messages("ar")

# --- STATUS CONSTANTS ---
STATUS_PENDING = _msgs["status"]["pending"]
STATUS_ACCEPTED = _msgs["status"]["accepted"]
STATUS_AWAITING_VERIFICATION = _msgs["status"]["awaiting_verification"]
STATUS_FINISHED = _msgs["status"]["finished"]
STATUS_OFFERED = _msgs["status"]["offered"]
STATUS_REJECTED_PAYMENT = _msgs["status"]["rejected_payment"]
STATUS_DENIED_ADMIN = _msgs["status"]["denied_admin"]
STATUS_DENIED_STUDENT = _msgs["status"]["denied_student"]

# --- MESSAGES ---
MSG_WELCOME = _msgs["messages"]["welcome"]
MSG_HELP = _msgs["messages"]["help"]
MSG_CANCELLED = _msgs["messages"]["cancelled"]
MSG_NO_ACTIVE_PROCESS = _msgs["messages"]["no_active_process"]

# --- ADMIN DASHBOARD ---
MSG_ADMIN_DASHBOARD = _msgs["messages"]["admin_dashboard"]
MSG_BROADCAST_PROMPT = _msgs["messages"]["broadcast_prompt"]
MSG_BROADCAST_SUCCESS = _msgs["messages"]["broadcast_success"]
MSG_PROJECT_DETAILS_HEADER = _msgs["messages"]["project_details_header"]
MSG_ASK_PRICE = _msgs["messages"]["ask_price"]
MSG_ASK_DELIVERY = _msgs["messages"]["ask_delivery"]
MSG_ASK_NOTES = _msgs["messages"]["ask_notes"]
MSG_ASK_NOTES_TEXT = _msgs["messages"]["ask_notes_text"]
MSG_NO_NOTES = _msgs["messages"]["no_notes"]
MSG_OFFER_SENT = _msgs["messages"]["offer_sent"]
MSG_UPLOAD_FINISHED_WORK = _msgs["messages"]["upload_finished_work"]
MSG_WORK_FINISHED_ALERT = _msgs["messages"]["work_finished_alert"]
MSG_FINISHED_CONFIRM = _msgs["messages"]["finished_confirm"]
MSG_PAYMENT_CONFIRMED_CLIENT = _msgs["messages"]["payment_confirmed_client"]
MSG_PAYMENT_CONFIRMED_ADMIN = _msgs["messages"]["payment_confirmed_admin"]
MSG_PAYMENT_REJECTED_CLIENT = _msgs["messages"]["payment_rejected_client"]
MSG_PAYMENT_REJECTED_ADMIN = _msgs["messages"]["payment_rejected_admin"]
MSG_PROJECT_DENIED_CLIENT = _msgs["messages"]["project_denied_client"]
MSG_PROJECT_DENIED_STUDENT_TO_ADMIN = _msgs["messages"]["project_denied_student_to_admin"]
MSG_PROJECT_CLOSED = _msgs["messages"]["project_closed"]

# --- MENU BUTTONS ---
BTN_NEW_PROJECT = _msgs["buttons"]["new_project"]
BTN_MY_PROJECTS = _msgs["buttons"]["my_projects"]
BTN_MY_OFFERS = _msgs["buttons"]["my_offers"]
BTN_BACK = _msgs["buttons"]["back"]
BTN_YES = _msgs["buttons"]["yes"]
BTN_NO = _msgs["buttons"]["no"]
BTN_CANCEL = _msgs["buttons"]["cancel"]

# --- CLIENT PROMPTS ---
MSG_ASK_SUBJECT = _msgs["client_prompts"]["ask_subject"]
MSG_ASK_TUTOR = _msgs["client_prompts"]["ask_tutor"]
MSG_ASK_DEADLINE = _msgs["client_prompts"]["ask_deadline"]
MSG_ASK_DETAILS = _msgs["client_prompts"]["ask_details"]
MSG_NO_DESC = _msgs["client_prompts"]["no_desc"]
MSG_PROJECT_SUBMITTED = _msgs["client_prompts"]["project_submitted"]
MSG_OFFER_ACCEPTED = _msgs["client_prompts"]["offer_accepted"]
MSG_RECEIPT_RECEIVED = _msgs["client_prompts"]["receipt_received"]
MSG_OFFER_DETAILS = _msgs["client_prompts"]["offer_details"]
MSG_NO_PROJECTS = _msgs["client_prompts"]["no_projects"]
MSG_NO_OFFERS = _msgs["client_prompts"]["no_offers"]
