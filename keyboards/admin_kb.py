"""
Admin Keyboard Module
=====================
Thin delegation layer – all keyboards are built by KeyboardFactory.
Import from keyboards.factory directly in new code.
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.factory import KeyboardFactory


def get_admin_dashboard_kb():
    return KeyboardFactory.admin_dashboard()


def get_back_btn(callback_data: str = None) -> InlineKeyboardBuilder:
    return KeyboardFactory.back(callback_data)


def get_pending_projects_kb(pending_projects):
    return KeyboardFactory.pending_projects(pending_projects)


def get_accepted_projects_kb(accepted_projects):
    return KeyboardFactory.accepted_projects(accepted_projects)


def get_manage_project_kb(p_id):
    return KeyboardFactory.manage_project(p_id)


def get_payment_verify_kb(proj_id):
    return KeyboardFactory.payment_verify(proj_id)


def get_notes_decision_kb():
    return KeyboardFactory.notes_decision()


def get_cancel_kb():
    return KeyboardFactory.cancel()


def get_new_project_alert_kb(p_id):
    return KeyboardFactory.new_project_alert(p_id)


def get_payment_history_kb(payments):
    return KeyboardFactory.payment_history(payments)
