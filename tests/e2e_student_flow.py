import asyncio
import os
import sys

# Load environment variables (from svu_helper's .env)
from dotenv import load_dotenv
load_dotenv()

try:
    from telethon import TelegramClient
except ImportError:
    print("Telethon is not installed. Please run: pip install telethon")
    sys.exit(1)

# Configuration from .env
API_ID = os.getenv("TEST_API_ID")
API_HASH = os.getenv("TEST_API_HASH")
BOT_USERNAME = os.getenv("TARGET_BOT_USERNAME")

if not API_ID or not API_HASH or not BOT_USERNAME:
    print("⛔ MISSING CREDENTIALS: Set TEST_API_ID, TEST_API_HASH, and TARGET_BOT_USERNAME in your .env file.")
    sys.exit(1)

# Ensure username formatting is correct
if not BOT_USERNAME.startswith("@"):
    BOT_USERNAME = f"@{BOT_USERNAME}"

async def run_student_tests():
    """Simulates a student interacting with the bot."""
    print("🚀 Initializing E2E UserBot Testing...")
    
    # Create the client and connect
    # 'student_session' will save the login locally so you don't have to authenticate every time.
    client = TelegramClient('student_session', API_ID, API_HASH)
    await client.start()
    
    me = await client.get_me()
    print(f"✅ Logged in as: {me.first_name} (@{me.username})")
    print(f"🤖 Targeting Bot: {BOT_USERNAME}")

    try:
        # --- TEST 1: THE WELCOME COMMAND ---
        print("\n▶️ [TEST 1] Sending /start...")
        await client.send_message(BOT_USERNAME, "/start")
        
        # Wait for the bot's response
        await asyncio.sleep(2) 
        messages = await client.get_messages(BOT_USERNAME, limit=1)
        
        if messages and "مرحباً" in messages[0].text:
            print("✅ TEST 1 PASSED: Bot welcomed the student.")
        else:
            print("❌ TEST 1 FAILED: Unexpected response or no response.")
            print(f"Bot said: {messages[0].text if messages else 'Nothing'}")
            return

        # --- TEST 2: THE NEW PROJECT FLOW ---
        print("\n▶️ [TEST 2] Starting /new_project flow...")
        await client.send_message(BOT_USERNAME, "/new_project")
        await asyncio.sleep(2)
        
        msg = (await client.get_messages(BOT_USERNAME, limit=1))[0]
        if "المادة" not in msg.text:
            print(f"❌ TEST 2 FAILED: Expected Subject prompt, got: {msg.text}")
            return
            
        print("✅ Received Subject prompt. Entering 'Automated Test Subject'...")
        await client.send_message(BOT_USERNAME, "Automated Test Subject")
        await asyncio.sleep(2)
        
        msg = (await client.get_messages(BOT_USERNAME, limit=1))[0]
        if "المدرس" not in msg.text:
            print(f"❌ TEST 2 FAILED: Expected Tutor prompt, got: {msg.text}")
            return
            
        print("✅ Received Tutor prompt. Entering 'Auto-Tutor'...")
        await client.send_message(BOT_USERNAME, "Auto-Tutor")
        await asyncio.sleep(2)
        
        msg = (await client.get_messages(BOT_USERNAME, limit=1))[0]
        if "الموعد" not in msg.text:
            print(f"❌ TEST 2 FAILED: Expected Deadline prompt, got: {msg.text}")
            return
            
        print("✅ Received Deadline prompt. Entering 'Tomorrow'...")
        await client.send_message(BOT_USERNAME, "Tomorrow")
        await asyncio.sleep(2)
        
        msg = (await client.get_messages(BOT_USERNAME, limit=1))[0]
        if "التفاصيل" not in msg.text:
            print(f"❌ TEST 2 FAILED: Expected Details prompt, got: {msg.text}")
            return
            
        print("✅ Received Details prompt. Sending final test text...")
        await client.send_message(BOT_USERNAME, "These are the final automated test details!")
        await asyncio.sleep(3) # Give it time to save to DB and notify admin
        
        msg = (await client.get_messages(BOT_USERNAME, limit=1))[0]
        if "بنجاح" in msg.text:
             print("✅ TEST 2 PASSED: Project was successfully submitted exactly like a human would!")
        else:
             print(f"❌ TEST 2 FAILED: Expected Success message, got: {msg.text}")
             return

        print("\n🎉 ALL STUDENT FLOW TESTS PASSED! Your UserBot is working flawlessly.")

    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    # Fix for weird "Event loop is closed" errors on Windows occasionally
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_student_tests())
