import asyncio
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
import os
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

async def debug_commands():
    bot = Bot(token=API_TOKEN)
    
    try:
        # Get current commands
        print("📋 Getting current commands...")
        commands = await bot.get_my_commands()
        print(f"Default commands: {[cmd.command for cmd in commands]}")
        
        # Get admin commands
        admin_cmds = await bot.get_my_commands(scope=BotCommandScopeChat(chat_id=ADMIN_ID))
        print(f"Admin commands: {[cmd.command for cmd in admin_cmds]}")
        
        # Delete all commands
        print("\n🗑️ Deleting all commands...")
        await bot.delete_my_commands()
        await bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=ADMIN_ID))
        
        # Set new commands
        print("\n🔄 Setting new commands...")
        student_commands = [
            BotCommand(command="start", description="🏠 Main Menu"),
            BotCommand(command="new_project", description="📚 Submit New Project"),
            BotCommand(command="my_projects", description="📂 My Status"),
            BotCommand(command="my_offers", description="🎁 View My Offers"),
            BotCommand(command="help", description="❓ Help"),
            BotCommand(command="cancel", description="🚫 Cancel Process")
        ]
        
        admin_commands = student_commands + [
            BotCommand(command="admin", description="🛠 Admin Panel")
        ]
        
        await bot.set_my_commands(student_commands, scope=BotCommandScopeDefault())
        await bot.set_my_commands(
            admin_commands, 
            scope=BotCommandScopeChat(chat_id=ADMIN_ID)
        )
        
        print("✅ Commands reset successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(debug_commands())