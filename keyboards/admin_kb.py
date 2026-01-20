"""
Admin Keyboard Module
=====================
Defines all inline and reply keyboards used in the administrative dashboard.
"""

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

def get_admin_dashboard_kb() -> types.InlineKeyboardMarkup:
    """Generates the main administrative dashboard keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📑 قائمة المشاريع الكاملة", callback_data="view_all_master"))
    builder.row(types.InlineKeyboardButton(text="📊 مشاريع قيد الانتظار", callback_data="view_pending"))
    builder.row(types.InlineKeyboardButton(text="✅ مشاريع مقبولة/جارية", callback_data="view_accepted"))
    builder.row(types.InlineKeyboardButton(text="📜 سجل المشاريع", callback_data="view_history"))
    builder.row(types.InlineKeyboardButton(text="📢 إرسال إعلان", callback_data="admin_broadcast"))
    return builder.as_markup()

def get_back_btn(callback_data: str = "back_to_admin") -> InlineKeyboardBuilder:
    """Returns an InlineKeyboardBuilder seeded with a standard 'Back' button."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ رجوع", callback_data=callback_data))
    return builder

def get_pending_projects_kb(pending_projects):
    builder = get_back_btn()
    for item in pending_projects:
        # Handle dict (new) or tuple (old/fallback)
        if isinstance(item, dict):
            p_id = item['id']
            subject = item.get('subject_name', '')
        else:
            p_id = item[0]
            subject = item[1] if len(item) > 1 else ''
            
        btn_text = f"📂 إدارة #{p_id}"
        if subject:
            btn_text += f": {subject}"
            
        builder.row(types.InlineKeyboardButton(text=btn_text, callback_data=f"manage_{p_id}"))
    return builder.as_markup()

def get_accepted_projects_kb(accepted_projects):
    builder = get_back_btn()
    for item in accepted_projects:
        if isinstance(item, dict):
            p_id = item['id']
            subject = item.get('subject_name', '')
        else:
            p_id = item[0]
            subject = item[1] if len(item) > 1 else ''
            
        btn_text = f"📤 إنهاء #{p_id}"
        if subject:
            btn_text += f": {subject}"
            
        builder.row(types.InlineKeyboardButton(text=btn_text, callback_data=f"manage_accepted_{p_id}")) # Finish
    return builder.as_markup()

def get_manage_project_kb(p_id):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💰 إرسال عرض", callback_data=f"make_offer_{p_id}")) # Send Offer
    builder.row(types.InlineKeyboardButton(text="❌ رفض", callback_data=f"deny_{p_id}")) # Reject
    builder.row(types.InlineKeyboardButton(text="⬅️ رجوع", callback_data="view_pending"))
    return builder.as_markup()

def get_payment_verify_kb(proj_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="✅ تأكيد الدفع", callback_data=f"confirm_pay_{proj_id}"), # Confirm Pay
        types.InlineKeyboardButton(text="❌ رفض الدفع", callback_data=f"reject_pay_{proj_id}") # Reject Pay
    )
    return builder.as_markup()

def get_notes_decision_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="نعم") # Yes
    builder.button(text="لا، أرسل الآن") # No, send now
    return builder.as_markup(resize_keyboard=True)

def get_new_project_alert_kb(p_id):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💰 إرسال عرض", callback_data=f"make_offer_{p_id}"))
    builder.row(types.InlineKeyboardButton(text="❌ رفض", callback_data=f"deny_{p_id}"))
    return builder.as_markup()
