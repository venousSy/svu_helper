import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

# Load credentials from .env
load_dotenv()

S_API_ID = int(os.getenv("TEST_API_ID", 0))
S_API_HASH = os.getenv("TEST_API_HASH", "")

A_API_ID = int(os.getenv("ADMIN_TEST_API_ID", 0))
A_API_HASH = os.getenv("ADMIN_TEST_API_HASH", "")

async def generate_session(name, api_id, api_hash):
    print(f"\n--- Generating Session for {name} ---")
    if not api_id or not api_hash:
        print(f"Missing API_ID or API_HASH for {name} in .env file!")
        return
        
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start()
    
    session_string = client.session.save()
    print("\n✅ Successfully generated session string!")
    print(f"\nCopy the line below and add it to your .env file as {name}_STRING_SESSION:\n")
    print(session_string)
    print("\n-------------------------------------------------\n")
    
    await client.disconnect()

async def main():
    print("Welcome to the E2E Session Generator!")
    print("This script will help you generate the needed String Sessions.")
    print("You will need to provide your phone number and the login code Telegram sends you.\n")
    
    try:
        await generate_session("STUDENT", S_API_ID, S_API_HASH)
    except Exception as e:
        print(f"Failed to generate STUDENT session: {e}")
        
    try:
        await generate_session("ADMIN", A_API_ID, A_API_HASH)
    except Exception as e:
        print(f"Failed to generate ADMIN session: {e}")

if __name__ == "__main__":
    asyncio.run(main())
