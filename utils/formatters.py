"""
Formatters
==========
All list-returning formatters produce a (text, total_pages) tuple so every
caller can attach the standard pagination keyboard.  Single-item formatters
(e.g. format_admin_notification) are unchanged.
"""
from __future__ import annotations

from utils.constants import (
    MSG_NO_OFFERS,
    MSG_NO_PROJECTS,
    STATUS_ACCEPTED,
    STATUS_AWAITING_VERIFICATION,
    STATUS_DENIED_ADMIN,
    STATUS_DENIED_STUDENT,
    STATUS_FINISHED,
    STATUS_PENDING,
)
from utils.pagination import paginate, PAGE_SIZE

_SEP = "━━━━━━━━━━━━━"


# ---------------------------------------------------------------------------
# Escaping helper
# ---------------------------------------------------------------------------

def escape_md(text) -> str:
    """Escapes Markdown special characters to prevent parsing errors."""
    if not text:
        return ""
    text = str(text)
    text = text.replace("\\", "\\\\")
    for char in ["_", "*", "`", "["]:
        text = text.replace(char, f"\\{char}")
    return text


# ---------------------------------------------------------------------------
# Admin – project list (pending / ongoing)
# ---------------------------------------------------------------------------

def format_project_list(
    projects: list,
    title: str = "📂 قائمة المشاريع",
    page: int = 0,
    page_size: int = PAGE_SIZE,
) -> tuple[str, int]:
    """Standard paginated list for Pending or Ongoing projects.

    Returns (text, total_pages).
    """
    if not projects:
        return "لا توجد مشاريع. ✅", 1

    slice_, total_pages, page = paginate(projects, page, page_size)
    total = len(projects)

    header = f"**{title}**\n{_SEP}\nإجمالي: {total} | صفحة {page + 1}/{total_pages}\n"
    lines = [header]

    for project in slice_:
        p_id = project["id"]
        subject = project["subject_name"]

        user_info = ""
        if "user_full_name" in project and project["user_full_name"]:
            name = escape_md(project["user_full_name"])
            u_id = project.get("user_id")
            username = (
                f" (@{escape_md(project['username'])})"
                if project.get("username")
                else ""
            )
            if u_id:
                user_info = f"\n   👤 [{name}](tg://user?id={u_id}){username}"
            else:
                user_info = f"\n   👤 {name}{username}"

        extra_info = ""
        if "tutor_name" in project and project["tutor_name"]:
            extra_info += f"\n   👨‍🏫 المدرس: {escape_md(project['tutor_name'])}"
        if "deadline" in project and project["deadline"]:
            extra_info += f" | 📅 الموعد: {escape_md(project['deadline'])}"

        user_info += extra_info
        lines.append(f"• #{p_id}: {escape_md(subject)}{user_info}\n")

    return "".join(lines).strip(), total_pages


# ---------------------------------------------------------------------------
# Admin – project history
# ---------------------------------------------------------------------------

def format_project_history(
    projects: list,
    page: int = 0,
    page_size: int = PAGE_SIZE,
) -> tuple[str, int]:
    """History list with icons based on status.

    Returns (text, total_pages).
    """
    if not projects:
        return "السجل فارغ. 📭", 1

    slice_, total_pages, page = paginate(projects, page, page_size)
    total = len(projects)

    header = f"📜 **سجل المشاريع:**\n{_SEP}\nإجمالي: {total} | صفحة {page + 1}/{total_pages}\n"
    lines = [header]

    for project in slice_:
        p_id = project["id"]
        subject = project["subject_name"]
        status = project["status"]
        icon = "🏁" if status == STATUS_FINISHED else "❌"
        lines.append(f"{icon} #{p_id} | {escape_md(subject)} ({status})\n")

    return "".join(lines).strip(), total_pages


# ---------------------------------------------------------------------------
# Admin – master report (all categories flattened)
# ---------------------------------------------------------------------------

def format_master_report(
    categorized_data: dict,
    page: int = 0,
    page_size: int = PAGE_SIZE,
) -> tuple[str, int]:
    """Paginated all-projects report.

    Returns (text, total_pages).
    """
    meta = {
        "New / Pending":     {"icon": "🆕", "label": "طلب جديد"},
        "Offered / Waiting": {"icon": "📨", "label": "عرض مرسل"},
        "Ongoing":           {"icon": "🚀", "label": "جارٍ"},
        "History":           {"icon": "📜", "label": "أرشيف"},
    }

    flat: list[tuple[dict, dict]] = []
    for key, projects in categorized_data.items():
        cfg = meta.get(key, {"icon": "🔹", "label": key})
        for item in projects:
            flat.append((cfg, item))

    total = len(flat)
    if total == 0:
        return f"📑 **تقارير المشاريع الشاملة**\n{_SEP}\n_لا توجد مشاريع حالياً._", 1

    slice_, total_pages, page = paginate(flat, page, page_size)

    header = (
        f"📑 **تقارير المشاريع الشاملة**\n{_SEP}\n"
        f"إجمالي: {total} | صفحة {page + 1}/{total_pages}\n"
    )
    lines: list[str] = [header]

    for cfg, item in slice_:
        p_id = item["id"]
        sub  = escape_md(item.get("subject_name", "—"))
        u_id = item.get("user_id")
        name = escape_md(item.get("user_full_name") or "مجهول")
        username = escape_md(item.get("username") or "")
        user_link = f"[{name}](tg://user?id={u_id})" if u_id else name
        if username:
            user_link += f" (@{username})"

        if "tutor_name" in item and item["tutor_name"]:
            extra = f"المدرس: {escape_md(item['tutor_name'])}"
        elif "status" in item:
            extra = f"الحالة: {item['status']}"
        else:
            extra = ""

        lines.append(
            f"{cfg['icon']} **#{p_id}** [{cfg['label']}]: {sub}\n"
            f"   👤 {user_link}\n"
            + (f"   ℹ️ {extra}\n" if extra else "")
        )

    return "".join(lines).strip(), total_pages


# ---------------------------------------------------------------------------
# Admin – payment list
# ---------------------------------------------------------------------------

def format_payment_list(
    payments: list,
    page: int = 0,
    page_size: int = PAGE_SIZE,
) -> tuple[str, int]:
    """Paginated payment history log.

    Returns (text, total_pages).
    """
    if not payments:
        return "سجل المدفوعات فارغ. 📭", 1

    slice_, total_pages, page = paginate(payments, page, page_size)
    total = len(payments)

    header = f"💰 **سجل المدفوعات**\n{_SEP}\nإجمالي: {total} | صفحة {page + 1}/{total_pages}\n"
    lines = [header]

    for pay in slice_:
        p_id    = pay["id"]
        proj_id = pay["project_id"]
        u_id    = pay["user_id"]
        status  = pay["status"]

        if status == "accepted":
            icon = "✅"
        elif status == "rejected":
            icon = "❌"
        else:
            icon = "⏳"

        lines.append(
            f"{icon} **D#{p_id}** | 🆔 Proj: #{proj_id}\n"
            f"   👤 User: [{u_id}](tg://user?id={u_id})\n"
            f"   🏷 Status: {status}\n\n"
        )

    return "".join(lines).strip(), total_pages


# ---------------------------------------------------------------------------
# Student – own projects
# ---------------------------------------------------------------------------

def format_student_projects(
    projects: list,
    page: int = 0,
    page_size: int = PAGE_SIZE,
) -> tuple[str, int]:
    """Paginated student project list.

    Returns (text, total_pages).
    """
    if not projects:
        return MSG_NO_PROJECTS, 1

    slice_, total_pages, page = paginate(projects, page, page_size)
    total = len(projects)

    header = (
        f"📋 **حالة مشاريعك:**\n{_SEP}\n"
        f"إجمالي: {total} | صفحة {page + 1}/{total_pages}\n\n"
    )
    lines = [header]

    for project in slice_:
        p_id    = project["id"]
        subject = project["subject_name"]
        status  = project["status"]

        if status == STATUS_PENDING:
            emoji = "⏳"
        elif status in [STATUS_ACCEPTED, STATUS_AWAITING_VERIFICATION]:
            emoji = "🚀"
        elif status == STATUS_FINISHED:
            emoji = "✅"
        elif status in [STATUS_DENIED_ADMIN, STATUS_DENIED_STUDENT]:
            emoji = "❌"
        else:
            emoji = "ℹ️"

        lines.append(f"• #{p_id} | {escape_md(subject)}\n   ┗ الحالة: {emoji} {status}\n\n")

    return "".join(lines).strip(), total_pages


# ---------------------------------------------------------------------------
# Student – pending offers
# ---------------------------------------------------------------------------

def format_offer_list(
    offers: list,
    page: int = 0,
    page_size: int = PAGE_SIZE,
) -> tuple[str, int]:
    """Paginated list of pending offers for the student.

    Returns (text, total_pages).
    """
    if not offers:
        return MSG_NO_OFFERS, 1

    slice_, total_pages, page = paginate(offers, page, page_size)
    total = len(offers)

    header = (
        f"🎁 **العروض المعلقة**\n{_SEP}\n"
        f"إجمالي: {total} | صفحة {page + 1}/{total_pages}\n"
    )
    lines = [header]

    for offer in slice_:
        p_id  = offer["id"]
        sub   = escape_md(offer["subject_name"])
        tutor = escape_md(offer["tutor_name"])
        lines.append(f"📍 **المشروع #{p_id}**: {sub}\n└ _المدرس: {tutor}_\n\n")

    lines.append("💡 اضغط على الزر أدناه لعرض التفاصيل والرد.")
    return "".join(lines).strip(), total_pages


# ---------------------------------------------------------------------------
# Admin – single-project notification (unchanged, no pagination needed)
# ---------------------------------------------------------------------------

def format_admin_notification(
    p_id, subject, deadline, details, user_name="Unknown", username=None
) -> str:
    """Formats the alert sent to the admin when a new project arrives."""
    user_display = escape_md(user_name)
    if username:
        user_display += f" (@{escape_md(username)})"

    return (
        f"🔔 **مشروع جديد #{p_id}**\n"
        f"{_SEP}\n"
        f"👤 **المستخدم:** {user_display}\n"
        f"📚 **المادة:** {escape_md(subject)}\n"
        f"📅 **الموعد:** {escape_md(deadline)}\n"
        f"📝 **التفاصيل:** {escape_md(details)}"
    )
