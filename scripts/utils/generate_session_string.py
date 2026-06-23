import os
import sys
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

S_API_ID   = os.getenv("TEST_API_ID")
S_API_HASH = os.getenv("TEST_API_HASH")

if not S_API_ID or not S_API_HASH:
    print("Please ensure TEST_API_ID and TEST_API_HASH are in your .env file.")
    sys.exit(1)

print("Starting Telegram Client...")
with TelegramClient(StringSession(), S_API_ID, S_API_HASH) as client:
    print("\n✅ Successfully authenticated!")
    print("\n" + "="*50)
    print("YOUR TELETHON SESSION STRING (Save this to Railway as TEST_USER_SESSION_STRING):")
    print(client.session.save())
    print("="*50 + "\n")
