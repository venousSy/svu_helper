import asyncio
import sqlite3 # Built-in, no install needed
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

ADMIN_ID = 7450958767
# --- DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect("bot_requests.db") # Creates the file if it doesn't exist
    cursor = conn.cursor()
    # Create the table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message_text TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

# Run the initialization
init_db()
# 1. Replace 'YOUR_TOKEN_HERE' with the token from BotFather
API_TOKEN = '8395569134:AAHun2cnEbo8YJ39Y08cEKH2AMvz1_HBrZI'

# 2. Initialize the Bot and the Dispatcher (the brain)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 3. COMMAND HANDLERS (High Priority)
@dp.message(Command("start"))
async def welcome(message: types.Message):
    await message.answer("Hello! Send me a request.")

@dp.message(lambda message: message.from_user.id == ADMIN_ID and message.reply_to_message)
async def admin_reply_handler(message: types.Message):
    # 1. Get the original notification text
    original_text = message.reply_to_message.text
    
    # 2. Extract the Request ID (we'll look for the '#' symbol)
    # Simple logic: split the text and find the part starting with #
    try:
        req_id = original_text.split("ID: #")[1].split("\n")[0]
    except Exception:
        await message.answer("❌ Error: Could not find the Request ID in the replied message.")
        return

    # 3. Look up the User ID in the database using the Request ID
    conn = sqlite3.connect("bot_requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM requests WHERE id = ?", (req_id,))
    result = cursor.fetchone()
    
    if result:
        user_to_reply = result[0]
        
        # 4. Send your reply to that user
        await bot.send_message(chat_id=user_to_reply, text=f"📩 **Reply from Admin:**\n{message.text}")
        
        # 5. Update status in Database
        cursor.execute("UPDATE requests SET status = 'Resolved' WHERE id = ?", (req_id,))
        conn.commit()
        
        await message.answer(f"✅ Reply sent to User {user_to_reply}!")
    else:
        await message.answer("❌ Could not find that request in the database.")
    
    conn.close()

@dp.message()
async def handle_user_request(message: types.Message):
    # 1. Get info from the message
    uid = message.from_user.id
    text = message.text
# Ignore messages from the admin for now (we'll handle those later)
    if message.from_user.id == ADMIN_ID:
        return
    # 2. Save to Database
    conn = sqlite3.connect("bot_requests.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO requests (user_id, message_text) VALUES (?, ?)", 
        (uid, text)
    )
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # 3. Confirm to user
    await message.answer(f"✅ Your request (ID: {request_id}) has been saved and is pending review.")
    # 4. Notify the ADMIN
    notification_text = (
        f"🔔 **NEW REQUEST**\n"
        f"ID: #{request_id}\n"
        f"User: {message.from_user.full_name}\n"
        f"Message: {text}\n\n"
        f"Reply to this message to send your answer!"
    )
    await bot.send_message(chat_id=ADMIN_ID, text=notification_text)
    
# 5. Start the bot
async def main():
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())