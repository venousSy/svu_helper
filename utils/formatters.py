def format_project_list(projects, title="📂 Projects"):
    """Standard list for Pending or Ongoing projects."""
    if not projects:
        return "No projects found. ✅"
    
    text = f"**{title}**\n━━━━━━━━━━━━━━━━━━\n"
    for p_id, subject, *rest in projects:
        text += f"• #{p_id}: {subject}\n"
    return text.strip()

def format_project_history(projects):
    """History list with icons based on status."""
    if not projects:
        return "History is empty. 📭"
    
    text = "📜 **Project History:**\n━━━━━━━━━━━━━━━━━━\n"
    for p_id, subject, status in projects:
        icon = "🏁" if status == "Finished" else "❌"
        text += f"{icon} #{p_id} | {subject} ({status})\n"
    return text.strip()

def format_master_report(categorized_data: dict) -> str:
    text = "📑 **MASTER PROJECT REPORT**\n" + "━" * 15 + "\n"
    
    for status_key, projects in categorized_data.items():
        text += f"\n🔹 **{status_key.upper()}**\n"
        if not projects:
            text += "└ _No projects_\n"
            continue

        for item in projects[:15]:
            p_id = item[0]
            sub = item[1]
            # Use a fallback if the 3rd value (tutor or status) isn't there
            extra = item[2] if len(item) > 2 else "N/A"
            
            text += f"└ #{p_id}: {sub} ({extra})\n"
            
    return text.strip()
def format_student_projects(projects):
    """
    Formats the project list specifically for the student view.
    Includes status-specific emojis for better UX.
    """
    if not projects:
        return "📭 You haven't submitted any projects yet."

    response = "📋 **Your Project Status:**\n━━━━━━━━━━━━━━━━━━\n\n"
    for p_id, subject, status in projects:
        # Map statuses to emojis
        if status == "Pending":
            emoji = "⏳"
        elif status in ["Accepted", "Awaiting Verification"]:
            emoji = "🚀"
        elif status == "Finished":
            emoji = "✅"
        elif "Denied" in status or "Rejected" in status:
            emoji = "❌"
        else:
            emoji = "ℹ️"
            
        response += f"• #{p_id} | {subject}\n   ┗ Status: {emoji} {status}\n\n"
        
    return response.strip()

def format_admin_notification(p_id, subject, deadline, details):
    """Formats the alert sent to the admin when a new project arrives."""
    return (
        f"🔔 **NEW PROJECT #{p_id}**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📚 **Sub:** {subject}\n"
        f"📅 **Deadline:** {deadline}\n"
        f"📝 **Details:** {details}"
    )