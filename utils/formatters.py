from utils.constants import (
    STATUS_PENDING, STATUS_ACCEPTED, STATUS_AWAITING_VERIFICATION,
    STATUS_FINISHED, STATUS_DENIED_ADMIN, STATUS_DENIED_STUDENT,
    MSG_NO_PROJECTS, MSG_NO_OFFERS
)

def escape_md(text):
    """Escapes Markdown special characters to prevent parsing errors."""
    if not text:
        return ""
    text = str(text)
    for char in ["_", "*", "`", "["]:
        text = text.replace(char, f"\\{char}")
    return text

def format_project_list(projects, title="📂 قائمة المشاريع"):
    """Standard list for Pending or Ongoing projects."""
    if not projects:
        return "لا توجد مشاريع. ✅"
    
    text = f"**{title}**\n━━━━━━━━━━━━━━━━━━\n"
    for project in projects:
        # Check if it IS a dictionary (new style) or tuple (old style/fallback)
        if isinstance(project, dict):
            p_id = project['id']
            subject = project['subject_name']
            
            # Add user info if available
            user_info = ""
            if 'user_full_name' in project and project['user_full_name']:
                name = escape_md(project['user_full_name'])
                u_id = project.get('user_id')
                username = f" (@{escape_md(project['username'])})" if project.get('username') else ""
                
                # Link user if u_id is present
                if u_id:
                    user_info = f"\n   👤 [{name}](tg://user?id={u_id}){username}"
                else:
                    user_info = f"\n   👤 {name}{username}"
            
            # Add Tutor and Deadline if available
            extra_info = ""
            if 'tutor_name' in project and project['tutor_name']:
                tutor = escape_md(project['tutor_name'])
                extra_info += f"\n   👨‍🏫 المدرس: {tutor}"
            
            if 'deadline' in project and project['deadline']:
                deadline = escape_md(project['deadline'])
                extra_info += f" | 📅 الموعد: {deadline}"
                
            user_info += extra_info
                
        else:
            p_id = project[0]
            subject = escape_md(project[1])
            user_info = ""
            
        text += f"• #{p_id}: {escape_md(subject) if isinstance(project, dict) else subject}{user_info}\n"
    return text.strip()

# ... (rest of file) ...

def format_admin_notification(p_id, subject, deadline, details, user_name="Unknown", username=None):
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
        if isinstance(project, dict):
            p_id = project['id']
            subject = project['subject_name']
            status = project['status']
        else:
            p_id, subject, status = project

        icon = "🏁" if status == STATUS_FINISHED else "❌"
        text += f"{icon} #{p_id} | {escape_md(subject)} ({status})\n"
    return text.strip()

def format_master_report(categorized_data: dict) -> str:
    """
    Formats the project dictionary into a summary.
    Distinguishes between New requests and Sent offers.
    """
    text = "📑 **تقارير المشاريع الشاملة**\n" + "━" * 15 + "\n"
    
    # Mapping keys to their visual representation
    meta = {
        "New / Pending": {"icon": "🆕", "label": "طلبات جديدة"},
        "Offered / Waiting": {"icon": "📨", "label": "عروض مرسلة"},
        "Ongoing": {"icon": "🚀", "label": "قيد التنفيذ"},
        "History": {"icon": "📜", "label": "الأرشيف"}
    }
    
    for key, projects in categorized_data.items():
        config = meta.get(key, {"icon": "🔹", "label": key.upper()})
        
        text += f"\n{config['icon']} **{config['label']}** ({len(projects)})\n"
        
        if not projects:
            text += "└ _فارغ_\n"
            continue

        for item in projects:
            if isinstance(item, dict):
                p_id = item['id']
                sub = escape_md(item['subject_name'])
                
                # Construct User Info
                u_id = item.get('user_id')
                name = escape_md(item.get('user_full_name') or "مجهول")
                username = escape_md(item.get('username'))
                
                user_link = f"[{name}](tg://user?id={u_id})"
                if username:
                    user_link += f" (@{username})"
                
                # Determine "extra" based on available keys
                if 'tutor_name' in item:
                    extra = f"المدرس: {escape_md(item['tutor_name'])}"
                elif 'status' in item:
                    extra = f"الحالة: {item['status']}"
                else:
                    extra = ""
            else:
                p_id = item[0]
                sub = escape_md(item[1])
                extra = escape_md(item[2]) if len(item) > 2 else ""
                user_link = "المستخدم: مجهول"
            
            text += f"└ #{p_id}: {sub}\n   👤 {user_link}\n   ℹ️ {extra}\n"
            
    return text.strip()

def format_student_projects(projects):
    """
    Formats the project list specifically for the student view.
    Includes status-specific emojis for better UX.
    """
    if not projects:
        return MSG_NO_PROJECTS

    response = "📋 **حالة مشاريعك:**\n━━━━━━━━━━━━━━━━━━\n\n"
    for project in projects:
        if isinstance(project, dict):
            p_id = project['id']
            subject = project['subject_name']
            status = project['status']
        else:
            p_id, subject, status = project

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
            
        response += f"• #{p_id} | {escape_md(subject)}\n   ┗ الحالة: {emoji} {status}\n\n"
        
    return response.strip()


def format_offer_list(offers: list) -> str:
    """Formats a list of pending offers for the student."""
    if not offers:
        return MSG_NO_OFFERS
    
    text = "🎁 **العروض المعلقة**\n" + "━" * 15 + "\n"
    for offer in offers:
        if isinstance(offer, dict):
            p_id = offer['id']
            sub = escape_md(offer['subject_name'])
            tutor = escape_md(offer['tutor_name'])
        else:
            p_id, sub, tutor = offer

        text += f"📍 **المشروع #{p_id}**: {sub}\n└ _المدرس: {tutor}_\n\n"
    
    text += "💡 اضغط على الزر أدناه لعرض التفاصيل والرد."
    return text

def format_payment_list(payments: list) -> str:
    """Formats the raw payment logs into a readable history log."""
    if not payments:
        return "سجل المدفوعات فارغ. 📭"

    text = "💰 **سجل المدفوعات**\n" + "━" * 15 + "\n"
    
    for pay in payments:
        p_id = pay['id']
        proj_id = pay['project_id']
        u_id = pay['user_id']
        status = pay['status']
        
        # Emoji Logic
        if status == "accepted": icon = "✅"
        elif status == "rejected": icon = "❌"
        else: icon = "⏳"
        
        text += f"{icon} **D#{p_id}** | 🆔 Proj: #{proj_id}\n   👤 User: [{u_id}](tg://user?id={u_id})\n   🏷 Status: {status}\n\n"
        
    return text.strip()