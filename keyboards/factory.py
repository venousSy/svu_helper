"""
Keyboard Factory
================
Single point of truth for all bot keyboards.

All button labels are sourced from utils.constants (which itself reads
from locales/ar.json), keeping the UI text in one locale-aware place.
Handlers should import from this module instead of calling helper
functions in admin_kb / client_kb / common_kb directly.

The individual keyboard-builder modules (admin_kb.py, client_kb.py,
common_kb.py) delegate to this factory so that callers external to the
keyboards package require no changes during the transition.
"""

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from keyboards.callbacks import (
    MenuCallback,
    PageCallback,
    PaymentCallback,
    ProjectCallback,
    TicketCallback,
    MenuAction,
    PageAction,
    PaymentAction,
    ProjectAction,
    TicketAction,
)
from utils.constants import (
    BTN_BACK,
    BTN_CANCEL,
    BTN_MY_OFFERS,
    BTN_MY_PROJECTS,
    BTN_NEW_PROJECT,
    BTN_NO,
    BTN_YES,
)

# ---------------------------------------------------------------------------
# Additional button constants that were previously hard-coded inline
# ---------------------------------------------------------------------------
# Admin dashboard buttons
_BTN_VIEW_ALL = "📑 قائمة المشاريع الكاملة"
_BTN_VIEW_PENDING = "📊 مشاريع قيد الانتظار"
_BTN_VIEW_ACCEPTED = "✅ مشاريع مقبولة/جارية"
_BTN_VIEW_HISTORY = "📜 سجل المشاريع"
_BTN_VIEW_PAYMENTS = "💰 سجل المدفوعات"
_BTN_BROADCAST = "📢 إرسال إعلان"

# Shared action buttons
_BTN_BACK_ICON = "⬅️ رجوع"
_BTN_SEND_OFFER = "💰 إرسال عرض"
_BTN_REJECT = "❌ رفض"
_BTN_CONFIRM_PAYMENT = "✅ تأكيد الدفع"
_BTN_REJECT_PAYMENT = "❌ رفض الدفع"
_BTN_ACCEPT_OFFER = "✅ قبول"
_BTN_DENY_OFFER = "❌ رفض"
_BTN_CANCEL_PAY = "❌ إلغاء"
_BTN_FINISH_PROJECT = "📤 إنهاء"
_BTN_MANAGE_PROJECT = "📂 إدارة"
_BTN_SUPPORT = "📩 الدعم الفني"
_BTN_VIEW_RECEIPT = "📄 عرض الإيصال"


class KeyboardFactory:
    """Centralised builder for every keyboard used in the bot."""

    # -----------------------------------------------------------------------
    # Student keyboards
    # -----------------------------------------------------------------------

    @staticmethod
    def student_main() -> types.InlineKeyboardMarkup:
        """Inline main menu for students."""
        builder = InlineKeyboardBuilder()
        builder.button(
            text=BTN_NEW_PROJECT,
            callback_data=MenuCallback(action=MenuAction.new_project).pack(),
        )
        builder.button(
            text=BTN_MY_PROJECTS,
            callback_data=MenuCallback(action=MenuAction.my_projects).pack(),
        )
        builder.button(
            text=BTN_MY_OFFERS,
            callback_data=MenuCallback(action=MenuAction.my_offers).pack(),
        )
        builder.button(
            text=_BTN_SUPPORT,
            callback_data=MenuCallback(action=MenuAction.support).pack(),
        )
        builder.button(
            text="ℹ️ المساعدة",
            callback_data=MenuCallback(action=MenuAction.help).pack(),
        )
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def offer_actions(proj_id: int) -> types.InlineKeyboardMarkup:
        """Accept / Deny buttons shown to students on a pending offer."""
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_ACCEPT_OFFER,
                callback_data=ProjectCallback(action=ProjectAction.accept, id=proj_id).pack(),
            ),
            types.InlineKeyboardButton(
                text=_BTN_DENY_OFFER,
                callback_data=ProjectCallback(action=ProjectAction.deny, id=proj_id).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_BACK_ICON,
                callback_data=MenuCallback(action=MenuAction.my_offers).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def offers_list(offers: list) -> types.InlineKeyboardMarkup:
        """Inline list of all pending offers for easy navigation."""
        builder = InlineKeyboardBuilder()
        for item in offers:
            p_id = item["id"]
            subject = item.get("subject_name", "بدون مادة")
            tutor = item.get("tutor_name", "")
            
            parts = [f"#{p_id}"]
            if tutor:
                parts.append(tutor)
            if subject:
                parts.append(subject)
            btn_text = " | ".join(parts)
            
            builder.row(
                types.InlineKeyboardButton(
                    text=btn_text,
                    callback_data=ProjectCallback(action=ProjectAction.view_offer, id=p_id).pack(),
                )
            )
        return builder.as_markup()

    @staticmethod
    def cancel_payment() -> types.InlineKeyboardMarkup:
        """Cancel button shown during payment upload flow."""
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_CANCEL_PAY,
                callback_data=MenuCallback(action=MenuAction.cancel_pay).pack(),
            )
        )
        return builder.as_markup()

    # -----------------------------------------------------------------------
    # Admin keyboards
    # -----------------------------------------------------------------------

    @staticmethod
    def admin_dashboard() -> types.InlineKeyboardMarkup:
        """Main administrative control panel keyboard."""
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_VIEW_ALL,
                callback_data=MenuCallback(action=MenuAction.view_all_master).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_VIEW_PENDING,
                callback_data=MenuCallback(action=MenuAction.view_pending).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_VIEW_ACCEPTED,
                callback_data=MenuCallback(action=MenuAction.view_accepted).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_VIEW_HISTORY,
                callback_data=MenuCallback(action=MenuAction.view_history).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_VIEW_PAYMENTS,
                callback_data=MenuCallback(action=MenuAction.view_payments).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_BROADCAST,
                callback_data=MenuCallback(action=MenuAction.admin_broadcast).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def back(callback_data: str = None) -> InlineKeyboardBuilder:
        """Returns an InlineKeyboardBuilder seeded with a 'Back' button."""
        if callback_data is None:
            callback_data = MenuCallback(action=MenuAction.back_to_admin).pack()
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_BACK_ICON, callback_data=callback_data
            )
        )
        return builder

    @staticmethod
    def pending_projects(pending_projects: list) -> types.InlineKeyboardMarkup:
        """List of pending projects, each with a manage deep-link."""
        builder = InlineKeyboardBuilder()
        for item in pending_projects:
            p_id = item["id"]
            subject = item.get("subject_name", "")
            username = item.get("username") or item.get("user_full_name", "")
            date = item.get("deadline", "")
            
            parts = [f"#{p_id}"]
            if username:
                parts.append(username)
            if date:
                parts.append(date)
            if subject:
                parts.append(subject)
            btn_text = " | ".join(parts)
            
            builder.row(
                types.InlineKeyboardButton(
                    text=btn_text,
                    callback_data=ProjectCallback(action=ProjectAction.manage, id=p_id).pack(),
                )
            )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_BACK_ICON,
                callback_data=MenuCallback(action=MenuAction.back_to_admin).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def accepted_projects(accepted_projects: list) -> types.InlineKeyboardMarkup:
        """List of ongoing/accepted projects, each with a finish deep-link."""
        builder = InlineKeyboardBuilder()
        for item in accepted_projects:
            p_id = item["id"]
            subject = item.get("subject_name", "")
            username = item.get("username") or item.get("user_full_name", "")
            date = item.get("deadline", "")
            
            parts = [f"#{p_id}"]
            if username:
                parts.append(username)
            if date:
                parts.append(date)
            if subject:
                parts.append(subject)
            btn_text = " | ".join(parts)
            
            builder.row(
                types.InlineKeyboardButton(
                    text=btn_text,
                    callback_data=ProjectCallback(
                        action=ProjectAction.manage_accepted, id=p_id
                    ).pack(),
                )
            )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_BACK_ICON,
                callback_data=MenuCallback(action=MenuAction.back_to_admin).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def manage_project(p_id: int) -> types.InlineKeyboardMarkup:
        """Send Offer / Reject buttons for a specific pending project."""
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_SEND_OFFER,
                callback_data=ProjectCallback(action=ProjectAction.make_offer, id=p_id).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_REJECT,
                callback_data=ProjectCallback(action=ProjectAction.deny, id=p_id).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_BACK_ICON,
                callback_data=MenuCallback(action=MenuAction.view_pending).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def payment_verify(payment_id: int) -> types.InlineKeyboardMarkup:
        """Confirm / Reject payment buttons sent alongside a receipt."""
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_CONFIRM_PAYMENT,
                callback_data=PaymentCallback(action=PaymentAction.confirm, id=payment_id).pack(),
            ),
            types.InlineKeyboardButton(
                text=_BTN_REJECT_PAYMENT,
                callback_data=PaymentCallback(action=PaymentAction.reject, id=payment_id).pack(),
            ),
        )
        return builder.as_markup()

    @staticmethod
    def notes_decision() -> types.ReplyKeyboardMarkup:
        """Yes / No reply keyboard used when admin is asked about notes."""
        builder = ReplyKeyboardBuilder()
        builder.button(text=BTN_YES)
        builder.button(text=BTN_NO)
        builder.adjust(2)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def cancel() -> types.ReplyKeyboardMarkup:
        """Single-button cancel reply keyboard used during FSM flows."""
        builder = ReplyKeyboardBuilder()
        builder.button(text=BTN_CANCEL)
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def new_project_alert(p_id: int) -> types.InlineKeyboardMarkup:
        """Send Offer / Reject shortcuts in the admin new-project notification."""
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_SEND_OFFER,
                callback_data=ProjectCallback(action=ProjectAction.make_offer, id=p_id).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_REJECT,
                callback_data=ProjectCallback(action=ProjectAction.deny, id=p_id).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def payment_history(payments: list) -> types.InlineKeyboardMarkup:
        """Links to view receipts for the 10 most-recent payments."""
        builder = InlineKeyboardBuilder()
        for pay in payments[:10]:
            p_id = pay["id"]
            builder.row(
                types.InlineKeyboardButton(
                    text=f"{_BTN_VIEW_RECEIPT} #{p_id}",
                    callback_data=PaymentCallback(
                        action=PaymentAction.view_receipt, id=p_id
                    ).pack(),
                )
            )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_BACK_ICON,
                callback_data=MenuCallback(action=MenuAction.back_to_admin).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def paginated_master_report(
        page: int, total_pages: int
    ) -> types.InlineKeyboardMarkup:
        """Navigation row (Prev / Page X of Y / Next) + Back for the all-projects view."""
        builder = InlineKeyboardBuilder()
        nav_buttons: list[types.InlineKeyboardButton] = []

        if page > 0:
            nav_buttons.append(
                types.InlineKeyboardButton(
                    text="⬅️ السابق",
                    callback_data=PageCallback(action=PageAction.all_projects, page=page - 1).pack(),
                )
            )

        nav_buttons.append(
            types.InlineKeyboardButton(
                text=f"📄 {page + 1}/{total_pages}",
                callback_data="noop",  # counter-only, not functional
            )
        )

        if page < total_pages - 1:
            nav_buttons.append(
                types.InlineKeyboardButton(
                    text="التالي ➡️",
                    callback_data=PageCallback(action=PageAction.all_projects, page=page + 1).pack(),
                )
            )

        builder.row(*nav_buttons)
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_BACK_ICON,
                callback_data=MenuCallback(action=MenuAction.back_to_admin).pack(),
            )
        )
        return builder.as_markup()

    # -----------------------------------------------------------------------
    # Ticket keyboards
    # -----------------------------------------------------------------------

    @staticmethod
    def support_menu() -> types.InlineKeyboardMarkup:
        """Support sub-menu: Open New Ticket + My Active Tickets."""
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(
                text="🆕 فتح تذكرة جديدة",
                callback_data=TicketCallback(
                    action=TicketAction.open_new
                ).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text="📋 تذاكري المفتوحة",
                callback_data=TicketCallback(
                    action=TicketAction.list_active
                ).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_BACK_ICON,
                callback_data="menu:start",
            )
        )
        return builder.as_markup()

    @staticmethod
    def active_tickets_list(
        tickets: list,
    ) -> types.InlineKeyboardMarkup:
        """Inline list of open tickets for the student."""
        builder = InlineKeyboardBuilder()
        for t in tickets:
            tid = t["ticket_id"]
            created = t.get("created_at", "")
            if hasattr(created, "strftime"):
                created = created.strftime("%m/%d %H:%M")
            else:
                created = str(created)[:16]
            msg_count = len(t.get("messages", []))
            btn_text = f"🎫 #{tid}  |  💬 {msg_count}  |  {created}"
            builder.row(
                types.InlineKeyboardButton(
                    text=btn_text,
                    callback_data=TicketCallback(
                        action=TicketAction.view, id=tid
                    ).pack(),
                )
            )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_BACK_ICON,
                callback_data=MenuCallback(
                    action=MenuAction.support
                ).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def ticket_detail(
        ticket_id: int,
        *,
        is_closed: bool = False,
    ) -> types.InlineKeyboardMarkup:
        """Reply + Close + Back for a single ticket view."""
        builder = InlineKeyboardBuilder()
        if not is_closed:
            builder.row(
                types.InlineKeyboardButton(
                    text="✏️ إرسال رد",
                    callback_data=TicketCallback(
                        action=TicketAction.reply, id=ticket_id
                    ).pack(),
                )
            )
            builder.row(
                types.InlineKeyboardButton(
                    text="🔒 إغلاق التذكرة",
                    callback_data=TicketCallback(
                        action=TicketAction.close, id=ticket_id
                    ).pack(),
                )
            )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_BACK_ICON,
                callback_data=TicketCallback(
                    action=TicketAction.list_active
                ).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def ticket_message_pagination(
        ticket_id: int,
        page: int,
        total_pages: int,
    ) -> types.InlineKeyboardMarkup:
        """Pagination for ticket conversation history."""
        builder = InlineKeyboardBuilder()
        nav_buttons: list[types.InlineKeyboardButton] = []

        if page > 0:
            nav_buttons.append(
                types.InlineKeyboardButton(
                    text="⬅️ السابق",
                    callback_data=PageCallback(
                        action=PageAction.ticket_messages, page=page - 1
                    ).pack(),
                )
            )

        nav_buttons.append(
            types.InlineKeyboardButton(
                text=f"📄 {page + 1}/{total_pages}",
                callback_data="noop",
            )
        )

        if page < total_pages - 1:
            nav_buttons.append(
                types.InlineKeyboardButton(
                    text="التالي ➡️",
                    callback_data=PageCallback(
                        action=PageAction.ticket_messages, page=page + 1
                    ).pack(),
                )
            )

        builder.row(*nav_buttons)

        # Action buttons below pagination
        builder.row(
            types.InlineKeyboardButton(
                text="✏️ إرسال رد",
                callback_data=TicketCallback(
                    action=TicketAction.reply, id=ticket_id
                ).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=_BTN_BACK_ICON,
                callback_data=TicketCallback(
                    action=TicketAction.view, id=ticket_id
                ).pack(),
            )
        )
        return builder.as_markup()
