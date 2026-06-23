import re
with open('handlers/client_routes/matchmaking.py', 'r', encoding='utf-8') as f:
    text = f.read()

def replace_func(match):
    return '''async def find_teams(
    callback: types.CallbackQuery,
    team_request_repo: TeamRequestRepository,
) -> None:
    """Find open teams matching the seeker's courses."""
    courses = get_all_courses()
    
    service = FindOpenTeamsService(team_request_repo)
    open_teams = await service.execute(courses, callback.from_user.id)

    if not open_teams:
        await callback.message.edit_text(
            text=MSG_TEAM_NO_OPEN,
            reply_markup=KeyboardFactory.inline_cancel()
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        text="🔍 فرق متاحة:",
        reply_markup=KeyboardFactory.inline_cancel()
    )

    for t in open_teams:
        card_text = MSG_TEAM_CARD.format(
            t["id"],
            t.get("host_name", "Unknown"),
            t["course_name"],
            len(t["current_members"]),
            t["required_members"],
        )
        await callback.message.answer(
            text=card_text,
            reply_markup=KeyboardFactory.team_join_action(t["id"])
        )
    await callback.answer()'''

text = re.sub(r'async def find_teams\(.*?(?=\n\n# --- Seeker Flow: Join Team ---)', replace_func, text, flags=re.DOTALL)

with open('handlers/client_routes/matchmaking.py', 'w', encoding='utf-8') as f:
    f.write(text)
