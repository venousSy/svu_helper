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
    """Formats the categorized project dictionary into a readable summary."""
    text = "📋 **MASTER PROJECT REPORT**\n" + "━" * 15 + "\n"
    
    for status, projects in categorized_data.items():
        count = len(projects)
        icon = {"Pending": "⏳", "Accepted": "🚀", "Finished": "✅", "Denied": "❌"}.get(status, "🔹")
        
        text += f"\n{icon} **{status}** ({count})\n"
        if not projects:
            text += "└ _No projects in this category_\n"
        else:
            for p_id, sub, tutor in projects[:5]: # Show only top 5 to avoid message length limits
                text += f"└ #{p_id}: {sub} ({tutor})\n"
            if count > 5:
                text += f"   ... and {count-5} more.\n"
                
    return text
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