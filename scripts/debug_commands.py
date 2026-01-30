"""
Command Management Script
=========================
Resets and updates bot menu commands for both standard users and administrators.
Run this script to sync local command definitions with Telegram.
"""

import asyncio
import os

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from dotenv import load_dotenv

# --- CONFIGURATION ---
# --- CONFIGURATION ---
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")

# Parse ADMIN_IDS
env_ids = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in env_ids.split(",") if x.strip()]
if not ADMIN_IDS:
    # Fallback
    sid = os.getenv("ADMIN_ID")
    if sid:
        ADMIN_IDS.append(int(sid))


async def debug_commands():
    bot = Bot(token=API_TOKEN)

    try:
        # Get current commands
        print("📋 Getting current commands...")
        commands = await bot.get_my_commands()
        print(f"Default commands: {[cmd.command for cmd in commands]}")

        # Delete all commands
        print("\n🗑️ Deleting all commands...")
        await bot.delete_my_commands()
        for aid in ADMIN_IDS:
             await bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=aid))

        # Set new commands
        print("\n🔄 Setting new commands...")
        student_commands = [
            BotCommand(command="start", description="🏠 Main Menu"),
            BotCommand(command="new_project", description="📚 Submit New Project"),
            BotCommand(command="my_projects", description="📂 My Status"),
            BotCommand(command="my_offers", description="🎁 View My Offers"),
            BotCommand(command="help", description="❓ Help"),
            BotCommand(command="cancel", description="🚫 Cancel Process"),
        ]

        admin_commands = student_commands + [
            BotCommand(command="admin", description="🛠 Admin Panel"),
            BotCommand(command="maintenance_on", description="🛑 Enable Maint."),
            BotCommand(command="maintenance_off", description="✅ Disable Maint.")
        ]

        await bot.set_my_commands(student_commands, scope=BotCommandScopeDefault())
        
        for aid in ADMIN_IDS:
            await bot.set_my_commands(
                admin_commands, scope=BotCommandScopeChat(chat_id=aid)
            )

        print(f"✅ Commands reset successfully for Admins: {ADMIN_IDS}!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(debug_commands())
