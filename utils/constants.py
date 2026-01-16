"""
Centralized constants for the SVU Helper Bot.
"""

# --- STATUS CONSTANTS ---
STATUS_PENDING = 'Pending'
STATUS_ACCEPTED = 'Accepted'
STATUS_AWAITING_VERIFICATION = 'Awaiting Verification'
STATUS_FINISHED = 'Finished'
STATUS_OFFERED = 'Offered'
STATUS_REJECTED_PAYMENT = 'Rejected: Payment Issue'
STATUS_DENIED_ADMIN = 'Denied: Admin Rejected'
STATUS_DENIED_STUDENT = 'Denied: Student Cancelled'

# --- MESSAGES ---
MSG_WELCOME = (
    "👋 Welcome! Use the menu below to manage your projects.\n\n"
    "Available commands:\n"
    "/new_project - Submit new project\n"
    "/my_projects - View your projects\n"
    "/my_offers - View pending offers\n"
    "/help - Show help\n"
    "/cancel - Cancel current process"
)

MSG_HELP = (
    "ℹ️ **Available Commands:**\n\n"
    "📚 **Project Submission:**\n"
    "/new_project - Submit new project\n\n"
    "📊 **Project Management:**\n"
    "/my_projects - View your projects\n"
    "/my_offers - View pending offers\n\n"
    "🛠 **Other:**\n"
    "/cancel - Cancel current process\n"
    "/start - Show main menu"
)

MSG_CANCELLED = "🚫 Process cancelled."
MSG_NO_ACTIVE_PROCESS = "❌ No active process to cancel."

# --- MENU BUTTONS ---
BTN_NEW_PROJECT = "📚 New Project"
BTN_MY_PROJECTS = "📂 My Projects"
BTN_MY_OFFERS = "🎁 View My Offers"
