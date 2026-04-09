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


def escape_md(text):
    """Escapes Markdown special characters to prevent parsing errors."""
    if not text:
        return ""
    text = str(text)
    # Escape backslash first to prevent double escaping
    text = text.replace("\\", "\\\\")
    for char in ["_", "*", "`", "["]:
        text = text.replace(char, f"\\{char}")
    return text


def format_project_list(projects, title="📂 قائمة المشاريع"):
    """Standard list for Pending or Ongoing projects."""
    if not projects:
        return "لا توجد مشاريع. ✅"

    text = f"**{title}**\n━━━━━━━━━━━━━━━━━━\n"
    for project in projects:
        p_id = project["id"]
        subject = project["subject_name"]

        # Add user info if available
        user_info = ""
        if "user_full_name" in project and project["user_full_name"]:
            name = escape_md(project["user_full_name"])
            u_id = project.get("user_id")
            username = (
                f" (@{escape_md(project['username'])})"
                if project.get("username")
                else ""
            )

            # Link user if u_id is present
            if u_id:
                user_info = f"\n   👤 [{name}](tg://user?id={u_id}){username}"
            else:
                user_info = f"\n   👤 {name}{username}"

        # Add Tutor and Deadline if available
        extra_info = ""
        if "tutor_name" in project and project["tutor_name"]:
            tutor = escape_md(project["tutor_name"])
            extra_info += f"\n   👨‍🏫 المدرس: {tutor}"

        if "deadline" in project and project["deadline"]:
            deadline = escape_md(project["deadline"])
            extra_info += f" | 📅 الموعد: {deadline}"

        user_info += extra_info

        text += f"• #{p_id}: {escape_md(subject)}{user_info}\n"
    return text.strip()


# ... (rest of file) ...


def format_admin_notification(
    p_id, subject, deadline, details, user_name="Unknown", username=None
):
    """Formats the alert sent to the admin when a new project arrives."""
    user_display = f"{escape_md(user_name)}"
    if username:
        user_display += f" (@{escape_md(username)})"

    return (
        f"🔔 **مشروع جديد #{p_id}**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 **المستخدم:** {user_display}\n"
        f"📚 **المادة:** {escape_md(subject)}\n"
        f"📅 **الموعد:** {escape_md(deadline)}\n"
        f"📝 **التفاصيل:** {escape_md(details)}"
    )


def format_project_history(projects):
    """History list with icons based on status."""
    if not projects:
        return "السجل فارغ. 📭"

    text = "📜 **سجل المشاريع:**\n━━━━━━━━━━━━━━━━━━\n"
    for project in projects:
        p_id = project["id"]
        subject = project["subject_name"]
        status = project["status"]

        icon = "🏁" if status == STATUS_FINISHED else "❌"
        text += f"{icon} #{p_id} | {escape_md(subject)} ({status})\n"
    return text.strip()


def format_master_report(
    categorized_data: dict, page: int = 0, page_size: int = 5
) -> tuple[str, int]:
    """
    Returns (message_text, total_pages) for a paginated all-projects report.

    Flattens all categories into a single list, slices the requested page,
    and produces a compact Markdown block well within Telegram's 4096-char limit.
    """
    # Mapping keys to their visual representation
    meta = {
        "New / Pending":     {"icon": "🆕", "label": "طلب جديد"},
        "Offered / Waiting": {"icon": "📨", "label": "عرض مرسل"},
        "Ongoing":           {"icon": "🚀", "label": "جارٍ"},
        "History":           {"icon": "📜", "label": "أرشيف"},
    }

    # Build a flat list of (category_label, item) tuples
    flat: list[tuple[str, dict]] = []
    for key, projects in categorized_data.items():
        cfg = meta.get(key, {"icon": "🔹", "label": key})
        for item in projects:
            flat.append((cfg, item))

    total = len(flat)
    if total == 0:
        return "📑 **تقارير المشاريع الشاملة**\n━━━━━━━━━━━━━\n_لا توجد مشاريع حالياً._", 1

    total_pages = max(1, -(-total // page_size))   # ceiling division
    page = max(0, min(page, total_pages - 1))

    start = page * page_size
    slice_ = flat[start : start + page_size]

    header = (
        f"📑 **تقارير المشاريع الشاملة**\n"
        f"━━━━━━━━━━━━━\n"
        f"إجمالي: {total} | صفحة {page + 1}/{total_pages}\n"
    )

    lines: list[str] = [header]
    for cfg, item in slice_:
        p_id = item["id"]
        sub  = escape_md(item.get("subject_name", "—"))

        u_id    = item.get("user_id")
        name    = escape_md(item.get("user_full_name") or "مجهول")
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



def format_student_projects(projects):
    """
    Formats the project list specifically for the student view.
    Includes status-specific emojis for better UX.
    """
    if not projects:
        return MSG_NO_PROJECTS

    response = "📋 **حالة مشاريعك:**\n━━━━━━━━━━━━━━━━━━\n\n"
    for project in projects:
        p_id = project["id"]
        subject = project["subject_name"]
        status = project["status"]

        # Map statuses to emojis
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

        response += (
            f"• #{p_id} | {escape_md(subject)}\n   ┗ الحالة: {emoji} {status}\n\n"
        )

    return response.strip()


def format_offer_list(offers: list) -> str:
    """Formats a list of pending offers for the student."""
    if not offers:
        return MSG_NO_OFFERS

    text = "🎁 **العروض المعلقة**\n" + "━" * 15 + "\n"
    for offer in offers:
        p_id = offer["id"]
        sub = escape_md(offer["subject_name"])
        tutor = escape_md(offer["tutor_name"])

        text += f"📍 **المشروع #{p_id}**: {sub}\n└ _المدرس: {tutor}_\n\n"

    text += "💡 اضغط على الزر أدناه لعرض التفاصيل والرد."
    return text


def format_payment_list(payments: list) -> str:
    """Formats the raw payment logs into a readable history log."""
    if not payments:
        return "سجل المدفوعات فارغ. 📭"

    text = "💰 **سجل المدفوعات**\n" + "━" * 15 + "\n"

    for pay in payments:
        p_id = pay["id"]
        proj_id = pay["project_id"]
        u_id = pay["user_id"]
        status = pay["status"]

        # Emoji Logic
        if status == "accepted":
            icon = "✅"
        elif status == "rejected":
            icon = "❌"
        else:
            icon = "⏳"

        text += f"{icon} **D#{p_id}** | 🆔 Proj: #{proj_id}\n   👤 User: [{u_id}](tg://user?id={u_id})\n   🏷 Status: {status}\n\n"

    return text.strip()
