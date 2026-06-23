import re

with open('main.py', 'r', encoding='utf-8') as f:
    main_code = f.read()

main_code = main_code.replace(
    "if isinstance(event, types.CallbackQuery):",
    "if isinstance(event, types.Update) and event.callback_query:"
).replace(
    "logger.info(\"RAW CALLBACK\", data=event.data)",
    "logger.info(\"RAW CALLBACK\", data=event.callback_query.data)"
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_code)

with open('handlers/client_routes/matchmaking.py', 'r', encoding='utf-8') as f:
    mm = f.read()

# Replace filters
mm = mm.replace(
    "@router.callback_query(TeamCallback.filter(F.action == TeamAction.select_course), TeamStates.choosing_course)",
    "@router.callback_query(F.data.startswith(\"team:select_course:\"), TeamStates.choosing_course)"
)
mm = mm.replace(
    "@router.callback_query(TeamCallback.filter(F.action == TeamAction.select_count), TeamStates.choosing_member_count)",
    "@router.callback_query(F.data.startswith(\"team:select_count:\"), TeamStates.choosing_member_count)"
)
mm = mm.replace(
    "@router.callback_query(TeamCallback.filter(F.action == TeamAction.my_teams))",
    "@router.callback_query(F.data.startswith(\"team:my_teams:\"))"
)
mm = mm.replace(
    "@router.callback_query(TeamCallback.filter(F.action == TeamAction.find))",
    "@router.callback_query(F.data.startswith(\"team:find:\"))"
)
mm = mm.replace(
    "@router.callback_query(TeamCallback.filter(F.action == TeamAction.join))",
    "@router.callback_query(F.data.startswith(\"team:join:\"))"
)
mm = mm.replace(
    "@router.callback_query(TeamCallback.filter(F.action.in_([TeamAction.accept_join, TeamAction.reject_join])))",
    "@router.callback_query(F.data.startswith(\"team:accept_join:\") | F.data.startswith(\"team:reject_join:\"))"
)

# Add callback.answer()
mm = mm.replace(
    "        await callback.message.answer(text)\n",
    "        await callback.message.answer(text)\n    await callback.answer()\n"
)
mm = mm.replace(
    "        return\n\n    await callback.message.edit_text(\n        text=\"🔍 فرق متاحة:\"",
    "        await callback.answer()\n        return\n\n    await callback.message.edit_text(\n        text=\"🔍 فرق متاحة:\""
)
mm = mm.replace(
    "            text=text,\n            reply_markup=KeyboardFactory.team_join_action(t[\"id\"])\n        )\n",
    "            text=text,\n            reply_markup=KeyboardFactory.team_join_action(t[\"id\"])\n        )\n    await callback.answer()\n"
)

with open('handlers/client_routes/matchmaking.py', 'w', encoding='utf-8') as f:
    f.write(mm)
