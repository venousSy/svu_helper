import asyncio
import sqlite3
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext 
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- 0. CONFIGURATION & SETUP ---
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- 1. DATABASE LOGIC ---
def init_project_db():
    """Initializes the SQLite database and ensures the projects table exists."""
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

# --- 2. STATES (FSM) ---
class ProjectOrder(StatesGroup):
    """States for the student submission flow."""
    subject = State()
    tutor = State()
    deadline = State()
    details = State()

class AdminStates(StatesGroup):
    """States for administrative actions."""
    waiting_for_broadcast = State()

# --- 3. STUDENT HANDLERS ---

@dp.message(Command("start"))
async def welcome(message: types.Message):
    """Greets the user and provides basic instructions."""
    await message.answer("👋 Hello! Use /new_project to submit a homework request or /my_projects to check status.")

@dp.message(Command("cancel"))
async def global_cancel(message: types.Message, state: FSMContext):
    """Universal cancel command to reset any active FSM state."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ No active process to cancel.")
        return
    await state.clear()
    await message.answer("🚫 Process cancelled.", reply_markup=types.ReplyKeyboardRemove())

@dp.message(Command("new_project"))
async def start_project(message: types.Message, state: FSMContext):
    """Begins the FSM 'staircase' for project submission."""
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
    await message.answer("📝 Please send **Details** (Type text or upload a PDF/Image).")
    await state.set_state(ProjectOrder.details)

@dp.message(ProjectOrder.details)
async def process_details(message: types.Message, state: FSMContext):
    """Finalizes submission, saves to DB, and notifies admin."""
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

    await message.answer(f"✅ Project #{project_id} submitted! Waiting for admin review.")
    await bot.send_message(ADMIN_ID, f"🔔 **NEW PROJECT #{project_id}**\nSub: {data['subject']}\nDetails: {details_text}")
    await state.clear()

@dp.message(Command("my_projects"))
async def view_projects(message: types.Message):
    """Allows students to view their own submission history and status."""
    conn = sqlite3.connect("bot_requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, subject_name, status FROM projects WHERE user_id = ?", (message.from_user.id,))
    projects = cursor.fetchall()
    conn.close()

    if not projects:
        await message.answer("📭 You haven't submitted any projects yet.")
        return

    response = "📋 **Your Projects:**\n\n"
    for p_id, subject, status in projects:
        emoji = "⏳" if status == "Pending" else "✅" if status == "Accepted" else "❌"
        response += f"#{p_id} | {subject} - {emoji} {status}\n"
    await message.answer(response)

# --- 4. ADMIN DASHBOARD & COMMANDS ---

@dp.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_dashboard(message: types.Message):
    """Main hub for admin controls."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Pending Projects", callback_data="view_pending"))
    builder.row(types.InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast"))
    builder.row(types.InlineKeyboardButton(text="📈 Statistics", callback_data="view_stats"))
    
    await message.answer("🛠 **Admin Control Panel**", reply_markup=builder.as_markup())

# --- 5. ADMIN CALLBACKS & REPLIES ---

@dp.callback_query(F.data == "view_pending", F.from_user.id == ADMIN_ID)
async def admin_view_pending(callback: types.CallbackQuery):
    """Fetches and displays all projects with 'Pending' status."""
    conn = sqlite3.connect("bot_requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, subject_name, user_id FROM projects WHERE status = 'Pending'")
    pending = cursor.fetchall()
    conn.close()

    if not pending:
        await callback.answer("No pending projects! ✅", show_alert=True)
        return

    text = "⏳ **Pending Projects:**\n\n"
    for p_id, subject, u_id in pending:
        text += f"ID: #{p_id} | {subject} (User: {u_id})\n"
    await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(F.data == "admin_broadcast", F.from_user.id == ADMIN_ID)
async def trigger_broadcast(callback: types.CallbackQuery, state: FSMContext):
    """Initiates the broadcast state with a cancel button."""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_broadcast"))
    
    await callback.message.answer("📢 Enter the broadcast message for ALL users:", reply_markup=builder.as_markup())
    await state.set_state(AdminStates.waiting_for_broadcast)
    await callback.answer()

@dp.message(AdminStates.waiting_for_broadcast, F.from_user.id == ADMIN_ID)
async def execute_broadcast(message: types.Message, state: FSMContext):
    """Sends the provided text to every unique user in the database."""
    conn = sqlite3.connect("bot_requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM projects")
    users = cursor.fetchall()
    conn.close()

    count = 0
    for (user_id,) in users:
        try:
            await bot.send_message(user_id, f"🔔 **ANNOUNCEMENT:**\n\n{message.text}")
            count += 1
            await asyncio.sleep(0.05) 
        except Exception:
            pass

    await message.answer(f"✅ Broadcast sent to {count} users.")
    await state.clear()

@dp.callback_query(F.data == "cancel_broadcast", F.from_user.id == ADMIN_ID)
async def cancel_broadcast_btn(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🚫 Broadcast cancelled.")
    await callback.answer()

@dp.message(F.reply_to_message, F.from_user.id == ADMIN_ID)
async def admin_reply_handler(message: types.Message):
    """Parses replies to project notifications to send offers to students."""
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
        await bot.send_message(user_to_reply, f"💰 **Offer for {subject}:**\n\n{message.text}", reply_markup=builder.as_markup())
        await message.answer(f"✅ Offer for #{proj_id} sent!")
    conn.close()

@dp.callback_query(F.data.startswith("accept_"))
async def handle_accept(callback: types.CallbackQuery):
    proj_id = callback.data.split("_")[1]
    conn = sqlite3.connect("bot_requests.db")
    conn.execute("UPDATE projects SET status = 'Accepted' WHERE id = ?", (proj_id,))
    conn.commit()
    conn.close()
    await callback.message.edit_text("✅ Offer Accepted! The tutor is starting.")
    await bot.send_message(ADMIN_ID, f"🚀 Project #{proj_id} was ACCEPTED.")

@dp.callback_query(F.data.startswith("deny_"))
async def handle_deny(callback: types.CallbackQuery):
    await callback.message.edit_text("❌ Offer Declined.")

# --- 6. LIFECYCLE & LAUNCH ---

async def main():
    """Sets command menus and starts polling."""
    student_cmds = [
        types.BotCommand(command="start", description="Start"),
        types.BotCommand(command="new_project", description="New Project"),
        types.BotCommand(command="my_projects", description="My Status"),
        types.BotCommand(command="cancel", description="Stop process")
    ]
    admin_cmds = student_cmds + [types.BotCommand(command="admin", description="🛠 Admin Panel")]

    await bot.set_my_commands(student_cmds, scope=types.BotCommandScopeDefault())
    await bot.set_my_commands(admin_cmds, scope=types.BotCommandScopeChat(chat_id=ADMIN_ID))

    print("Bot is online...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())