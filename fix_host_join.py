with open('handlers/client_routes/matchmaking.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('MSG_TEAM_FULL.format(request_id, team["course_name"])\n            )', 'MSG_TEAM_FULL.format(request_id, team["course_name"])\n            )\n        await callback.answer()')

text = text.replace('MSG_TEAM_JOIN_REJECTED_SEEKER.format(request_id, team["course_name"])\n        )', 'MSG_TEAM_JOIN_REJECTED_SEEKER.format(request_id, team["course_name"])\n        )\n        await callback.answer()')

with open('handlers/client_routes/matchmaking.py', 'w', encoding='utf-8') as f:
    f.write(text)
