import asyncio
import sqlite3
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F # Added F here
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext 
from aiogram.utils.keyboard import InlineKeyboardBuilder

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# --- 1. Database & States ---
def init_project_db():
    conn = sqlite3.connect("bot_requests.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject_name TEXT,
            tutor_name TEXT,
            deadline TEXT,
            details TEXT,
            file_id TEXT,
            status TEXT DEFAULT 'Pending',
            admin_price TEXT,
            admin_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_project_db()

class ProjectOrder(StatesGroup):
    subject = State()
    tutor = State()
    deadline = State()
    details = State()

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- 2. Handlers (Commands & FSM) ---

@dp.message(Command("start"))
async def welcome(message: types.Message):
    await message.answer("Hello! Use /new_project to submit a homework request.")

@dp.message(Command("new_project"))
async def start_project(message: types.Message, state: FSMContext):
    await message.answer("📚 What is the **Subject Name**?")
    await state.set_state(ProjectOrder.subject)

@dp.message(ProjectOrder.subject)
async def process_subject(message: types.Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await message.answer("👨‍🏫 What is the **Tutor's Name**?")
    await state.set_state(ProjectOrder.tutor)

@dp.message(ProjectOrder.tutor)
async def process_tutor(message: types.Message, state: FSMContext):
    await state.update_data(tutor=message.text)
    await message.answer("📅 What is the **Final Date (Deadline)**?")
    await state.set_state(ProjectOrder.deadline)

@dp.message(ProjectOrder.deadline)
async def process_deadline(message: types.Message, state: FSMContext):
    await state.update_data(deadline=message.text)
    await message.answer("📝 Please send the **Project Details** (Text or PDF).")
    await state.set_state(ProjectOrder.details)

@dp.message(ProjectOrder.details)
async def process_details(message: types.Message, state: FSMContext):
    data = await state.get_data()
    file_id = message.document.file_id if message.document else None
    details_text = message.caption if message.document else message.text
    
    conn = sqlite3.connect("bot_requests.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO projects (user_id, subject_name, tutor_name, deadline, details, file_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (message.from_user.id, data['subject'], data['tutor'], data['deadline'], details_text, file_id))
    
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()

    await message.answer(f"✅ Project #{project_id} submitted!")
    await bot.send_message(ADMIN_ID, f"🔔 **NEW PROJECT #{project_id}**\nSub: {data['subject']}\nDetails: {details_text}")
    await state.clear()
@dp.message(Command("my_projects"))
async def view_projects(message: types.Message):
    uid = message.from_user.id
    
    conn = sqlite3.connect("bot_requests.db")
    cursor = conn.cursor()
    # Fetch all projects belonging to this specific user
    cursor.execute("SELECT id, subject_name, status FROM projects WHERE user_id = ?", (uid,))
    projects = cursor.fetchall()
    conn.close()

    if not projects:
        await message.answer("📭 You haven't submitted any projects yet.")
        return

    response = "📋 **Your Projects:**\n\n"
    for p_id, subject, status in projects:
        # Determine an emoji based on status
        emoji = "⏳" if status == "Pending" else "✅" if status == "Accepted" else "❌"
        response += f"#{p_id} | {subject} - {emoji} {status}\n"
    
    await message.answer(response)


@dp.message(Command("broadcast"), F.from_user.id == ADMIN_ID)
async def start_broadcast(message: types.Message, state: FSMContext):
    # Create a Cancel Button
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="❌ Cancel Broadcast", callback_data="cancel_broadcast"))
    
    await message.answer(
        "📢 Please enter the message you want to broadcast to **ALL** users:",
        reply_markup=builder.as_markup()
    )
    await state.set_state("waiting_for_broadcast_text")
@dp.message(Command("cancel"))
async def global_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("No active process to cancel.")
        return

    await state.clear()
    await message.answer("🚫 Process cancelled and memory cleared.", reply_markup=types.ReplyKeyboardRemove())

@dp.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_dashboard(message: types.Message):
    builder = InlineKeyboardBuilder()
    # Row 1: Management
    builder.row(types.InlineKeyboardButton(text="📊 Pending Projects", callback_data="view_pending"))
    # Row 2: Communication
    builder.row(types.InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast"))
    # Row 3: Stats
    builder.row(types.InlineKeyboardButton(text="📈 Statistics", callback_data="view_stats"))
    
    await message.answer(
        "🛠 **Admin Control Panel**\nSelect an action below:",
        reply_markup=builder.as_markup()
    )
# --- 3. Admin & Callback Handlers ---
@dp.callback_query(F.data == "view_pending", F.from_user.id == ADMIN_ID)
async def admin_view_pending(callback: types.CallbackQuery):
    conn = sqlite3.connect("bot_requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, subject_name, user_id FROM projects WHERE status = 'Pending'")
    pending = cursor.fetchall()
    conn.close()

    if not pending:
        await callback.answer("No pending projects! ✅")
        return

    text = "⏳ **Pending Projects:**\n\n"
    for p_id, subject, u_id in pending:
        text += f"ID: #{p_id} | {subject} (User: {u_id})\n"
    
    await callback.message.answer(text)
    await callback.answer()
@dp.message(F.text, F.from_user.id == ADMIN_ID)
async def execute_broadcast(message: types.Message, state: FSMContext):
    # Check if we are actually waiting for broadcast text
    current_state = await state.get_state()
    if current_state != "waiting_for_broadcast_text":
        return # Skip if it's just a regular admin message

    broadcast_text = message.text
    
    # 1. Get all unique users from the projects table
    conn = sqlite3.connect("bot_requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM projects")
    users = cursor.fetchall()
    conn.close()

    count = 0
    # 2. Loop and send
    for user in users:
        try:
            user_id = user[0]
            await bot.send_message(chat_id=user_id, text=f"🔔 **ANNOUNCEMENT:**\n\n{broadcast_text}")
            count += 1
            # Small sleep to avoid hitting Telegram's rate limits
            await asyncio.sleep(0.05) 
        except Exception as e:
            print(f"Failed to send to {user_id}: {e}")

    await message.answer(f"✅ Broadcast sent successfully to {count} users.")
    await state.clear()
    
@dp.message(lambda message: message.from_user.id == ADMIN_ID and message.reply_to_message)
async def admin_reply_handler(message: types.Message):
    try:
        proj_id = message.reply_to_message.text.split("#")[1].split("\n")[0].strip()
    except:
        return

    conn = sqlite3.connect("bot_requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, subject_name FROM projects WHERE id = ?", (proj_id,))
    result = cursor.fetchone()
    
    if result:
        user_to_reply, subject = result
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="✅ Accept", callback_data=f"accept_{proj_id}"),
            types.InlineKeyboardButton(text="❌ Deny", callback_data=f"deny_{proj_id}")
        )
        
        await bot.send_message(
            chat_id=user_to_reply, 
            text=f"💰 **Offer for {subject}:**\n\n{message.text}", 
            reply_markup=builder.as_markup()
        )
        await message.answer("✅ Offer sent!")
    conn.close()
@dp.callback_query(F.data == "admin_broadcast", F.from_user.id == ADMIN_ID)
async def trigger_broadcast_from_panel(callback: types.CallbackQuery, state: FSMContext):
    # This re-uses the logic we already built!
    await callback.message.answer("📢 Please enter the message you want to broadcast:")
    await state.set_state("waiting_for_broadcast_text")
    await callback.answer()
@dp.callback_query(F.data.startswith("accept_"))
async def handle_accept(callback: types.CallbackQuery):
    proj_id = callback.data.split("_")[1]
    # Update DB status to 'Accepted'
    await callback.message.edit_text("✅ Offer Accepted! The tutor is starting.")
    await bot.send_message(ADMIN_ID, f"🚀 Project #{proj_id} was ACCEPTED.")

@dp.callback_query(F.data.startswith("deny_"))
async def handle_deny(callback: types.CallbackQuery):
    await callback.message.edit_text("❌ Offer Declined.")
@dp.callback_query(F.data == "cancel_broadcast", F.from_user.id == ADMIN_ID)
async def cancel_broadcast(callback: types.CallbackQuery, state: FSMContext):
    await state.clear() # This is the most important part!
    await callback.message.edit_text("🚫 Broadcast cancelled. No messages were sent.")
    await callback.answer("Cancelled")
# --- 4. Launch ---
async def main():
    # 1. Define commands for regular Students
    student_commands = [
        types.BotCommand(command="start", description="Restart the bot"),
        types.BotCommand(command="new_project", description="Submit a homework/project"),
        types.BotCommand(command="my_projects", description="Check your orders")
    ]

    # 2. Define commands for the Admin (Students see these + Broadcast)
    admin_commands = student_commands + [
       types.BotCommand(command="broadcast", description="Send msg to all"),
       types.BotCommand(command="admin", description="🛠 Open Admin Dashboard")
    ]

    # 3. Apply the Student commands to everyone (Default)
    await bot.set_my_commands(student_commands, scope=types.BotCommandScopeDefault())

    # 4. Apply the Admin commands ONLY to your ID
    await bot.set_my_commands(
        admin_commands, 
        scope=types.BotCommandScopeChat(chat_id=ADMIN_ID)
    )

    print("Bot is running and command scopes are set...")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())