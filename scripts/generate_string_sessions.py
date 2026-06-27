import os
import sys
import asyncio
from dotenv import load_dotenv

# Ensure telethon is available
try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
except ImportError:
    print("Telethon is not installed. Please run: pip install telethon")
    sys.exit(1)

# Ensure script is run from project root to find sessions and .env
if not os.path.exists(".env"):
    print("Please run this script from the project root folder.")
    sys.exit(1)

load_dotenv()

S_API_ID   = os.getenv("TEST_API_ID")
S_API_HASH = os.getenv("TEST_API_HASH")
A_API_ID   = os.getenv("ADMIN_TEST_API_ID")
A_API_HASH = os.getenv("ADMIN_TEST_API_HASH")

if not all([S_API_ID, S_API_HASH, A_API_ID, A_API_HASH]):
    print("Missing API credentials in .env")
    sys.exit(1)

async def main():
    print("Generating String Sessions...\n")
    
    # 1. Student Session
    if os.path.exists("student_session.session"):
        client = TelegramClient('student_session', S_API_ID, S_API_HASH)
        await client.connect()
        if await client.is_user_authorized():
            string_session = StringSession.save(client.session)
            print("=======================================")
            print("STUDENT_STRING_SESSION:")
            print(string_session)
            print("=======================================\n")
        else:
            print("student_session.session exists but is not authorized.")
        await client.disconnect()
    else:
        print("student_session.session file not found.")

    # 2. Admin Session
    if os.path.exists("admin_session.session"):
        client = TelegramClient('admin_session', A_API_ID, A_API_HASH)
        await client.connect()
        if await client.is_user_authorized():
            string_session = StringSession.save(client.session)
            print("=======================================")
            print("ADMIN_STRING_SESSION:")
            print(string_session)
            print("=======================================\n")
        else:
            print("admin_session.session exists but is not authorized.")
        await client.disconnect()
    else:
        print("admin_session.session file not found.")
        
    print("Add these variables to your Railway Environment Variables and your local .env file.")

if __name__ == "__main__":
    asyncio.run(main())
