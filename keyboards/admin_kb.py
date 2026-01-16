from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

def get_admin_dashboard_kb() -> types.InlineKeyboardMarkup:
    """Generates the main administrative dashboard keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📑 Master Project List", callback_data="view_all_master"))
    builder.row(types.InlineKeyboardButton(text="📊 Pending Projects", callback_data="view_pending"))
    builder.row(types.InlineKeyboardButton(text="✅ Accepted/Ongoing", callback_data="view_accepted"))
    builder.row(types.InlineKeyboardButton(text="📜 Project History", callback_data="view_history"))
    builder.row(types.InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast"))
    return builder.as_markup()

def get_back_btn(callback_data: str = "back_to_admin") -> InlineKeyboardBuilder:
    """Returns an InlineKeyboardBuilder seeded with a standard 'Back' button."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Back", callback_data=callback_data))
    return builder

def get_pending_projects_kb(pending_projects):
    builder = get_back_btn()
    for p_id, subject, _ in pending_projects:
        builder.row(types.InlineKeyboardButton(text=f"📂 Manage #{p_id}", callback_data=f"manage_{p_id}"))
    return builder.as_markup()

def get_accepted_projects_kb(accepted_projects):
    builder = get_back_btn()
    for p_id, _ in accepted_projects:
        builder.row(types.InlineKeyboardButton(text=f"📤 Finish #{p_id}", callback_data=f"manage_accepted_{p_id}"))
    return builder.as_markup()

def get_manage_project_kb(p_id):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💰 Send Offer", callback_data=f"make_offer_{p_id}"))
    builder.row(types.InlineKeyboardButton(text="❌ Reject", callback_data=f"deny_{p_id}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Back", callback_data="view_pending"))
    return builder.as_markup()

def get_payment_verify_kb(proj_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="✅ Confirm Pay", callback_data=f"confirm_pay_{proj_id}"),
        types.InlineKeyboardButton(text="❌ Reject Pay", callback_data=f"reject_pay_{proj_id}")
    )
    return builder.as_markup()

def get_notes_decision_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Yes")
    builder.button(text="No, send now")
    return builder.as_markup(resize_keyboard=True)

def get_new_project_alert_kb(p_id):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💰 Send Offer", callback_data=f"make_offer_{p_id}"))
    builder.row(types.InlineKeyboardButton(text="❌ Reject", callback_data=f"deny_{p_id}"))
    return builder.as_markup()
