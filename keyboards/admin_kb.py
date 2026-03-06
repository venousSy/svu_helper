"""
Admin Keyboard Module
=====================
Defines all inline and reply keyboards used in the administrative dashboard.
"""

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from utils.constants import BTN_CANCEL, BTN_NO, BTN_YES


from keyboards.callbacks import MenuCallback, ProjectCallback, PaymentCallback

def get_admin_dashboard_kb() -> types.InlineKeyboardMarkup:
    """Generates the main administrative dashboard keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="📑 قائمة المشاريع الكاملة", 
            callback_data=MenuCallback(action="view_all_master").pack()
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="📊 مشاريع قيد الانتظار", 
            callback_data=MenuCallback(action="view_pending").pack()
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="✅ مشاريع مقبولة/جارية", 
            callback_data=MenuCallback(action="view_accepted").pack()
        )
    )
    builder.row(
        types.InlineKeyboardButton(text="📜 سجل المشاريع", 
            callback_data=MenuCallback(action="view_history").pack()
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="💰 سجل المدفوعات", 
            callback_data=MenuCallback(action="view_payments").pack()
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="📢 إرسال إعلان", 
            callback_data=MenuCallback(action="admin_broadcast").pack()
        )
    )
    return builder.as_markup()


def get_back_btn(callback_data: str = None) -> InlineKeyboardBuilder:
    """Returns an InlineKeyboardBuilder seeded with a standard 'Back' button."""
    # Build default callback if none provided
    if callback_data is None:
        callback_data = MenuCallback(action="back_to_admin").pack()
        
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ رجوع", callback_data=callback_data))
    return builder


def get_pending_projects_kb(pending_projects):
    builder = get_back_btn()
    for item in pending_projects:
        p_id = item["id"]
        subject = item.get("subject_name", "")

        btn_text = f"📂 إدارة #{p_id}"
        if subject:
            btn_text += f": {subject}"

        builder.row(
            types.InlineKeyboardButton(
                text=btn_text, 
                callback_data=ProjectCallback(action="manage", id=p_id).pack()
            )
        )
    return builder.as_markup()


def get_accepted_projects_kb(accepted_projects):
    builder = get_back_btn()
    for item in accepted_projects:
        p_id = item["id"]
        subject = item.get("subject_name", "")

        btn_text = f"📤 إنهاء #{p_id}"
        if subject:
            btn_text += f": {subject}"

        builder.row(
            types.InlineKeyboardButton(
                text=btn_text, 
                callback_data=ProjectCallback(action="manage_accepted", id=p_id).pack()
            )
        )  # Finish
    return builder.as_markup()


def get_manage_project_kb(p_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="💰 إرسال عرض", 
            callback_data=ProjectCallback(action="make_offer", id=p_id).pack()
        )
    )  # Send Offer
    builder.row(
        types.InlineKeyboardButton(text="❌ رفض", 
            callback_data=ProjectCallback(action="deny", id=p_id).pack()
        )
    )  # Reject
    builder.row(
        types.InlineKeyboardButton(text="⬅️ رجوع", 
            callback_data=MenuCallback(action="view_pending").pack()
        )
    )
    return builder.as_markup()


def get_payment_verify_kb(proj_id):
    # Note: Calling argument is usually 'payment_id' in caller, but 'proj_id' here.
    # We'll treat it as ID in PaymentCallback.
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="✅ تأكيد الدفع", 
            callback_data=PaymentCallback(action="confirm", id=proj_id).pack()
        ),  # Confirm Pay
        types.InlineKeyboardButton(
            text="❌ رفض الدفع", 
            callback_data=PaymentCallback(action="reject", id=proj_id).pack()
        ),  # Reject Pay
    )
    return builder.as_markup()


def get_notes_decision_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_YES)
    builder.button(text=BTN_NO)
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_CANCEL)
    return builder.as_markup(resize_keyboard=True)


def get_new_project_alert_kb(p_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="💰 إرسال عرض", 
            callback_data=ProjectCallback(action="make_offer", id=p_id).pack()
        )
    )
    builder.row(
        types.InlineKeyboardButton(text="❌ رفض", 
            callback_data=ProjectCallback(action="deny", id=p_id).pack()
        )
    )
    return builder.as_markup()


def get_payment_history_kb(payments):
    """Generates buttons for each payment to view its receipt."""
    builder = get_back_btn()

    # Show last 10 payments to avoid button clutter
    recent_payments = payments[:10]

    for pay in recent_payments:
        p_id = pay["id"]
        builder.row(
            types.InlineKeyboardButton(
                text=f"📄 عرض الإيصال #{p_id}", 
                callback_data=PaymentCallback(action="view_receipt", id=p_id).pack()
            )
        )

    return builder.as_markup()
