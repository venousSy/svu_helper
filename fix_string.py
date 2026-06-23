with open('handlers/client_routes/matchmaking.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
text = re.sub(r'text=.*?,\n\s*reply_markup=KeyboardFactory\.inline_cancel\(\)\n\s*\)\n\n\s*for t in open_teams:', 'text="🔍 فرق متاحة:",\n        reply_markup=KeyboardFactory.inline_cancel()\n    )\n\n    for t in open_teams:', text, flags=re.DOTALL)

with open('handlers/client_routes/matchmaking.py', 'w', encoding='utf-8') as f:
    f.write(text)
