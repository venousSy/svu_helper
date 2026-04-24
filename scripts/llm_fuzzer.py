import asyncio
import json
import os
import sys
from dotenv import load_dotenv

try:
    from telethon import TelegramClient
except ImportError:
    print("Telethon is not installed. Please run: pip install telethon")
    sys.exit(1)

try:
    import google.generativeai as genai
except ImportError:
    print("google-generativeai is not installed. Please run: pip install google-generativeai")
    sys.exit(1)

# Ensure proper encoding for printing Arabic
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

S_API_ID   = os.getenv("TEST_API_ID")
S_API_HASH = os.getenv("TEST_API_HASH")
BOT_USERNAME = os.getenv("TARGET_BOT_USERNAME", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([S_API_ID, S_API_HASH, BOT_USERNAME]):
    print("⛔ MISSING TELEGRAM CREDENTIALS. Please check your .env file.")
    sys.exit(1)

if not GEMINI_API_KEY:
    print("⛔ MISSING GEMINI_API_KEY. Please set it in your .env file.")
    sys.exit(1)

if not BOT_USERNAME.startswith("@"):
    BOT_USERNAME = f"@{BOT_USERNAME}"

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

system_instruction = (
    "You are an AI auditor testing a Telegram bot by acting as a university student. "
    "The bot helps students submit project requests, track status, and open support tickets. "
    "Your objective is to discover 'points of confusion' and test if the bot is too rigid. "
    "For example: \n"
    "- When the bot provides inline buttons, try typing a natural language equivalent instead of just clicking (you can't click anyway, you just send text).\n"
    "- When it asks for specific input (like a date), try providing it in a slightly conversational or non-standard format.\n"
    "- Try asking a clarifying question in the middle of a multi-step submission flow.\n"
    "- Use Arabic for the message_to_send, as the bot is in Arabic.\n"
    "- You MUST comprehensively test ALL of the following areas before finishing:\n"
    "  1. Submit a New Project (مشروع جديد) with edge cases.\n"
    "  2. Check My Projects (مشاريعي) or Offers (عروضي).\n"
    "  3. Open a Support Ticket (الدعم الفني).\n"
    "- IMPORTANT: When you finish one path, send '/start' or 'إلغاء' to return to the main menu and test the next path.\n"
    "- DO NOT set \"done\": true until you have explored ALL the areas listed above.\n"
    "You must output ONLY valid JSON in the following format. Do not use markdown blocks:\n"
    "{\n"
    '  "thought": "Your reasoning about what to test next based on the bot\'s response",\n'
    '  "message_to_send": "The exact text to send to the bot",\n'
    '  "done": false\n'
    "}"
)

# Use Gemini 3.1 Flash Lite as it has 15 RPM and 500 RPD
model = genai.GenerativeModel(
    model_name="gemini-3.1-flash-lite-preview",
    system_instruction=system_instruction
)

chat = model.start_chat(history=[])

def clean_json(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

async def main():
    print("🚀 Starting LLM Student Fuzzer...")
    print("Connecting to Telegram...")
    
    session_string = os.getenv("TEST_USER_SESSION_STRING")
    if session_string:
        from telethon.sessions import StringSession
        client = TelegramClient(StringSession(session_string), S_API_ID, S_API_HASH)
        print("Using StringSession from environment variables.")
    else:
        client = TelegramClient('student_session', S_API_ID, S_API_HASH)
        print("Using local 'student_session' file.")
        
    await client.start()
    
    print(f"✅ Logged in as student. Targeting {BOT_USERNAME}")
    
    # Start the conversation
    print("\n>> Sending /start to bot")
    await client.send_message(BOT_USERNAME, "/start")
    
    max_turns = 75
    for turn in range(max_turns):
        print(f"\n{'='*40}\nTurn {turn+1}/{max_turns}\n{'='*40}")
        print("⏳ Waiting for bot to reply...")
        
        # Wait 6 seconds to let bot messages arrive AND to safely respect
        # the 15 RPM limit for Gemini 3.1 Flash Lite.
        await asyncio.sleep(6) 
        
        # Get recent messages
        msgs = await client.get_messages(BOT_USERNAME, limit=5)
        
        bot_messages = []
        for m in msgs:
            if m.out: # Our own message, stop collecting
                break
            bot_messages.append(m)
            
        bot_messages.reverse() # chronological
        
        if not bot_messages:
            print("⚠️ No response from bot. Assuming it's stuck or waiting.")
            prompt_text = "The bot did not reply. It might be waiting for a specific format or it failed. What will you say next?"
        else:
            # Format the bot's response
            prompt_text = "The bot replied with the following message(s):\n\n"
            for m in bot_messages:
                prompt_text += f"Text: {m.text or '[No Text]'}\n"
                if m.reply_markup and hasattr(m.reply_markup, 'rows'):
                    prompt_text += "Inline Buttons provided by bot:\n"
                    for row in m.reply_markup.rows:
                        for btn in row.buttons:
                            prompt_text += f"- [{btn.text}]\n"
                prompt_text += "---\n"
        
        print("\n🤖 BOT SAID:")
        print(prompt_text.strip())
        
        # Get LLM response
        print("\n🧠 LLM is thinking...")
        
        max_retries = 3
        llm_reply_raw = None
        for attempt in range(max_retries):
            try:
                response = chat.send_message(prompt_text)
                llm_reply_raw = response.text
                break
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Quota" in error_msg:
                    print(f"⏳ Rate limit/Quota hit: {error_msg}")
                    print(f"Waiting 60 seconds before retrying... (Attempt {attempt+1}/{max_retries})")
                    import time
                    time.sleep(60) # Wait for quota to refresh
                else:
                    print(f"❌ Error during LLM generation: {e}")
                    break
        
        if not llm_reply_raw:
            print("⚠️ Failed to get a response from the LLM. Ending fuzzer session.")
            break
            
        try:
            parsed = json.loads(clean_json(llm_reply_raw))
            thought = parsed.get("thought", "")
            message_to_send = parsed.get("message_to_send", "")
            is_done = parsed.get("done", False)
        except json.JSONDecodeError:
            print("⚠️ Failed to parse LLM JSON. Raw output:")
            print(llm_reply_raw)
            message_to_send = "مرحبا" # fallback
            thought = "Parse error"
            is_done = False

        print(f"\n💡 LLM THOUGHT: {thought}")
        
        if is_done:
            print("🏁 LLM has decided the testing is comprehensive and complete!")
            break
            
        print(f"💬 LLM SENDING: {message_to_send}")
        
        # Send to bot
        await client.send_message(BOT_USERNAME, message_to_send)
            
    print("\n✅ Fuzzer session complete. Please review the transcript above to discover any UX issues or rigidity.")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
