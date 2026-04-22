"""
Keyboard Factory
================
Single point of truth for all bot keyboards.

All button labels are sourced from utils.constants (which itself reads
from locales/ar.json), keeping the UI text in one locale-aware place.
Handlers should import from this module instead of calling helper
functions in admin_kb / client_kb / common_kb directly.

The individual keyboard-builder modules (admin_kb.py, client_kb.py,
common_kb.py) have been removed — import directly from this module.
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
    BTN_ACCEPT_OFFER,
    BTN_ADMIN_TICKETS,
    BTN_BACK,
    BTN_BACK_ICON,
    BTN_BROADCAST,
    BTN_CANCEL,
    BTN_CANCEL_PAY,
    BTN_CLOSE_TICKET,
    BTN_CLOSED_TICKETS_LOG,
    BTN_CONFIRM_PAYMENT,
    BTN_DENY_OFFER,
    BTN_FINISH_PROJECT,
    BTN_HELP,
    BTN_MANAGE_PROJECT,
    BTN_MY_OFFERS,
    BTN_MY_OPEN_TICKETS,
    BTN_MY_PROJECTS,
    BTN_NEW_PROJECT,
    BTN_NEW_TICKET,
    BTN_NO,
    BTN_NO_SUBJECT,
    BTN_REJECT,
    BTN_REJECT_PAYMENT,
    BTN_REOPEN_TICKET,
    BTN_SEND_OFFER,
    BTN_SEND_REPLY,
    BTN_SUPPORT,
    BTN_VIEW_ACCEPTED,
    BTN_VIEW_ALL,
    BTN_VIEW_HISTORY,
    BTN_VIEW_PAYMENTS,
    BTN_VIEW_PENDING,
    BTN_VIEW_RECEIPT,
    BTN_YES,
)
from utils.formatters import format_datetime


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
            text=BTN_SUPPORT,
            callback_data=MenuCallback(action=MenuAction.support).pack(),
        )
        builder.button(
            text=BTN_HELP,
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
                text=BTN_ACCEPT_OFFER,
                callback_data=ProjectCallback(action=ProjectAction.accept, id=proj_id).pack(),
            ),
            types.InlineKeyboardButton(
                text=BTN_DENY_OFFER,
                callback_data=ProjectCallback(action=ProjectAction.deny, id=proj_id).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_BACK_ICON,
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
            subject = item.get("subject_name", BTN_NO_SUBJECT)
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
                text=BTN_CANCEL_PAY,
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
                text=BTN_VIEW_ALL,
                callback_data=MenuCallback(action=MenuAction.view_all_master).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_VIEW_PENDING,
                callback_data=MenuCallback(action=MenuAction.view_pending).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_VIEW_ACCEPTED,
                callback_data=MenuCallback(action=MenuAction.view_accepted).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_VIEW_HISTORY,
                callback_data=MenuCallback(action=MenuAction.view_history).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_VIEW_PAYMENTS,
                callback_data=MenuCallback(action=MenuAction.view_payments).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_BROADCAST,
                callback_data=MenuCallback(action=MenuAction.admin_broadcast).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_ADMIN_TICKETS,
                callback_data=MenuCallback(action=MenuAction.admin_tickets).pack(),
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
                text=BTN_BACK_ICON, callback_data=callback_data
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
                text=BTN_BACK_ICON,
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
                text=BTN_BACK_ICON,
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
                text=BTN_SEND_OFFER,
                callback_data=ProjectCallback(action=ProjectAction.make_offer, id=p_id).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_REJECT,
                callback_data=ProjectCallback(action=ProjectAction.deny, id=p_id).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_BACK_ICON,
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
                text=BTN_CONFIRM_PAYMENT,
                callback_data=PaymentCallback(action=PaymentAction.confirm, id=payment_id).pack(),
            ),
            types.InlineKeyboardButton(
                text=BTN_REJECT_PAYMENT,
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
                text=BTN_MANAGE_PROJECT,
                callback_data=ProjectCallback(action=ProjectAction.manage, id=p_id).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_SEND_OFFER,
                callback_data=ProjectCallback(action=ProjectAction.make_offer, id=p_id).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_REJECT,
                callback_data=ProjectCallback(action=ProjectAction.deny, id=p_id).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def payment_history(payments: list) -> types.InlineKeyboardMarkup:
        """Links to view receipts for the given list of payments."""
        builder = InlineKeyboardBuilder()
        for pay in payments:
            p_id = pay["id"]
            status = pay.get("status", "pending")
            
            if status == "accepted":
                icon = "✅"
            elif status == "rejected":
                icon = "❌"
            else:
                icon = "⏳"
                
            created_at = pay.get("created_at")
            date_str = format_datetime(created_at, "%d/%m") if created_at else ""
            
            user_name = pay.get("user_full_name") or pay.get("username") or str(pay.get("user_id", ""))
            project_name = pay.get("project_name") or f"Proj #{pay.get('project_id', '')}"
            
            # Shorten names to fit Telegram button limit (~64 bytes)
            user_name = user_name[:15]
            project_name = project_name[:15]
            
            parts = [f"#{p_id}", icon]
            if date_str:
                parts.append(date_str)
            parts.append(user_name)
            parts.append(project_name)
            
            btn_text = " | ".join(parts)
            if len(btn_text) > 64:
                btn_text = btn_text[:61] + "..."

            builder.row(
                types.InlineKeyboardButton(
                    text=btn_text,
                    callback_data=PaymentCallback(
                        action=PaymentAction.view_receipt, id=p_id
                    ).pack(),
                )
            )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_BACK_ICON,
                callback_data=MenuCallback(action=MenuAction.back_to_admin).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def paginated_master_report(
        page: int, total_pages: int
    ) -> types.InlineKeyboardMarkup:
        """Navigation row (Prev / Page X of Y / Next) + Back for the all-projects view."""
        from utils.pagination import build_nav_keyboard
        return build_nav_keyboard(
            action=PageAction.all_projects,
            page=page,
            total_pages=total_pages,
            back_action=MenuAction.back_to_admin,
        )



    # -----------------------------------------------------------------------
    # Ticket keyboards
    # -----------------------------------------------------------------------

    @staticmethod
    def support_menu() -> types.InlineKeyboardMarkup:
        """Support sub-menu: Open New Ticket + Active + Closed Tickets."""
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_NEW_TICKET,
                callback_data=TicketCallback(
                    action=TicketAction.open_new
                ).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_MY_OPEN_TICKETS,
                callback_data=TicketCallback(
                    action=TicketAction.list_active
                ).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_CLOSED_TICKETS_LOG,
                callback_data=TicketCallback(
                    action=TicketAction.list_closed
                ).pack(),
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_BACK_ICON,
                callback_data=MenuCallback(
                    action=MenuAction.close_list
                ).pack(),
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
            created = format_datetime(t.get("created_at", ""))
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
                text=BTN_BACK_ICON,
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
        """Reply + Close/Reopen + Back for a single ticket view."""
        builder = InlineKeyboardBuilder()
        if not is_closed:
            builder.row(
                types.InlineKeyboardButton(
                    text=BTN_SEND_REPLY,
                    callback_data=TicketCallback(
                        action=TicketAction.reply, id=ticket_id
                    ).pack(),
                )
            )
            builder.row(
                types.InlineKeyboardButton(
                    text=BTN_CLOSE_TICKET,
                    callback_data=TicketCallback(
                        action=TicketAction.close, id=ticket_id
                    ).pack(),
                )
            )
        else:
            builder.row(
                types.InlineKeyboardButton(
                    text=BTN_REOPEN_TICKET,
                    callback_data=TicketCallback(
                        action=TicketAction.reopen, id=ticket_id
                    ).pack(),
                )
            )
        # Back goes to appropriate list
        back_action = TicketAction.list_closed if is_closed else TicketAction.list_active
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_BACK_ICON,
                callback_data=TicketCallback(
                    action=back_action
                ).pack(),
            )
        )
        return builder.as_markup()

    @staticmethod
    def closed_tickets_list(
        tickets: list,
    ) -> types.InlineKeyboardMarkup:
        """Inline list of closed tickets for the student."""
        builder = InlineKeyboardBuilder()
        for t in tickets:
            tid = t["ticket_id"]
            created = format_datetime(t.get("created_at", ""))
            msg_count = len(t.get("messages", []))
            btn_text = f"🔒 #{tid}  |  💬 {msg_count}  |  {created}"
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
                text=BTN_BACK_ICON,
                callback_data=MenuCallback(
                    action=MenuAction.support
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
        from utils.pagination import build_nav_keyboard
        builder = InlineKeyboardBuilder()

        # Action buttons below pagination
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_SEND_REPLY,
                callback_data=TicketCallback(
                    action=TicketAction.reply, id=ticket_id
                ).pack(),
            )
        )
        
        return build_nav_keyboard(
            action=PageAction.ticket_messages,
            page=page,
            total_pages=total_pages,
            builder=builder,
            back_callback_data=TicketCallback(action=TicketAction.view, id=ticket_id).pack(),
        )

    @staticmethod
    def inline_cancel_ticket_action() -> types.InlineKeyboardMarkup:
        """Inline cancel button for ticket-related FSM states."""
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(
                text=BTN_CANCEL,
                callback_data=TicketCallback(
                    action=TicketAction.cancel_action
                ).pack(),
            )
        )
        return builder.as_markup()
