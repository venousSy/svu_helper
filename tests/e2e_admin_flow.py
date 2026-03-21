import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

try:
    from telethon import TelegramClient
except ImportError:
    print("Telethon is not installed. Please run: pip install telethon")
    sys.exit(1)

# Force UTF-8 for Windows console emojis
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration from .env
# Note: Admins need a SEPARATE testing account from the student account.
API_ID = os.getenv("ADMIN_TEST_API_ID")
API_HASH = os.getenv("ADMIN_TEST_API_HASH")
BOT_USERNAME = os.getenv("TARGET_BOT_USERNAME")

if not API_ID or not API_HASH or not BOT_USERNAME:
    print("⛔ MISSING ADMIN CREDENTIALS: Set ADMIN_TEST_API_ID and ADMIN_TEST_API_HASH in your .env file.")
    sys.exit(1)

if not BOT_USERNAME.startswith("@"):
    BOT_USERNAME = f"@{BOT_USERNAME}"

async def run_admin_tests():
    print("🚀 Initializing Admin E2E UserBot Testing...")
    client = TelegramClient('admin_session', API_ID, API_HASH)
    await client.start()
    
    me = await client.get_me()
    print(f"✅ Logged in as Admin: {me.first_name} (@{me.username})")
    
    try:
        print("\n▶️ [TEST 1] Opening Admin Dashboard...")
        await client.send_message(BOT_USERNAME, "/admin")
        await asyncio.sleep(2)
        
        # Verify dashboard received
        messages = await client.get_messages(BOT_USERNAME, limit=1)
        if not messages or not messages[0].reply_markup:
            print("❌ TEST 1 FAILED: Did not receive the admin dashboard with buttons.")
            return

        print("✅ Dashboard Received. Clicking 'مشاريع قيد الانتظار' (Pending Projects)...")
        pending_btn = None
        for row in messages[0].reply_markup.rows:
            for button in row.buttons:
                 if "مشاريع قيد الانتظار" in button.text:
                      pending_btn = button
                      break
            if pending_btn: break
            
        if not pending_btn:
             print("❌ FAILED: Could not find the pending projects button in the dashboard.")
             return
             
        await messages[0].click(data=pending_btn.data)
        await asyncio.sleep(4)
        
        # Check if we got the list of pending projects by fetching the edited message
        msg = await client.get_messages(BOT_USERNAME, ids=messages[0].id)
        if "مشاريع" not in msg.text:
             print(f"❌ FAILED: Did not get the pending projects list. Got:\n{msg.text}")
             return
             
        # Find the first 'إدارة' (Manage) button
        manage_button = None
        for row in msg.reply_markup.rows:
            for button in row.buttons:
                if "إدارة" in button.text:
                    manage_button = button
                    break
            if manage_button: break
            
        if not manage_button:
             print("⚠️ No pending projects to test! Please run the student test first to create a project.")
             return
             
        print(f"✅ Found a pending project. Clicking '{manage_button.text}'...")
        await msg.click(data=manage_button.data)
        await asyncio.sleep(4)
        
        # We should now see the project details and the 'Make Offer' button
        # This is a NEW message (the photo/document), so we fetch the latest msg in chat
        messages = await client.get_messages(BOT_USERNAME, limit=1)
        
        print("✅ Project details loaded. Clicking '💰 إرسال عرض' (Make Offer)...")
        offer_btn = None
        for row in messages[0].reply_markup.rows:
            for button in row.buttons:
                if "إرسال عرض" in button.text:
                    offer_btn = button
                    break
            if offer_btn: break
            
        if not offer_btn:
             print(f"❌ FAILED: Could not find the Make Offer button. Message text:\n{messages[0].text}")
             if not messages[0].reply_markup:
                 print("   -> (Message has no reply markup!)")
             return
             
        await messages[0].click(data=offer_btn.data)
        await asyncio.sleep(4)
        
        # Bot asks for price
        messages = await client.get_messages(BOT_USERNAME, limit=1)
        if "السعر" not in messages[0].text:
             print(f"❌ FAILED: Expected prompt for Price, got: {messages[0].text}")
             return
             
        print("✅ Received Price prompt. Entering '15000'...")
        await client.send_message(BOT_USERNAME, "15000")
        await asyncio.sleep(2)
        
        # Bot asks for delivery date
        messages = await client.get_messages(BOT_USERNAME, limit=1)
        if "تاريخ" not in messages[0].text and "تسليم" not in messages[0].text:
             print(f"❌ FAILED: Expected prompt for Delivery Date, got: {messages[0].text}")
             return
             
        print("✅ Received Delivery Date prompt. Entering 'After 3 Days'...")
        await client.send_message(BOT_USERNAME, "After 3 Days")
        await asyncio.sleep(3)
        
        # Bot asks for notes
        messages = await client.get_messages(BOT_USERNAME, limit=1)
        if "ملاحظات" not in messages[0].text:
             print(f"❌ FAILED: Expected prompt for Notes, got: {messages[0].text}")
             return
             
        print("✅ Received Notes prompt. Entering 'No special notes.'...")
        await client.send_message(BOT_USERNAME, "No special notes.")
        await asyncio.sleep(3)
        
        # Confirmation
        messages = await client.get_messages(BOT_USERNAME, limit=1)
        if "بنجاح" in messages[0].text or "تم إرسال العرض" in messages[0].text:
             print("✅ TEST PASSED: Offer was successfully generated and sent to the student!")
        else:
             print(f"❌ TEST FAILED: Expected success message, got: {messages[0].text}")
             return

        print("\n🎉 ALL ADMIN FLOW TESTS PASSED! Your Admin UserBot is working flawlessly.")

    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(run_admin_tests())
