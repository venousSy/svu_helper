with open('handlers/client_routes/matchmaking.py', 'r', encoding='utf-8') as f:
    mm = f.read()

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
