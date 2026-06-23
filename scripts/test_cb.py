import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from keyboards.callbacks import TeamCallback, TeamAction
from aiogram import F

cb = TeamCallback(action=TeamAction.find)
packed = cb.pack()
print(f"Packed: {packed}")

parsed = TeamCallback.unpack(packed)
print(f"Parsed action: {repr(parsed.action)}, type: {type(parsed.action)}")

magic = (F.action == TeamAction.find)
print(f"Magic filter match: {magic.resolve(parsed)}")
