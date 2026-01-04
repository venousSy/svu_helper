import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, ADMIN_ID
from handlers import client, admin, common
from aiogram import types

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Registering Routers
    dp.include_router(admin.router)
    dp.include_router(common.router)
    dp.include_router(client.router)

    # Set up menus
    student_cmds = [
        types.BotCommand(command="start", description="Start"),
        types.BotCommand(command="new_project", description="New Project"),
        types.BotCommand(command="my_projects", description="My Status")
    ]
    admin_cmds = student_cmds + [types.BotCommand(command="admin", description="🛠 Admin Panel")]

    await bot.set_my_commands(student_cmds, scope=types.BotCommandScopeDefault())
    await bot.set_my_commands(admin_cmds, scope=types.BotCommandScopeChat(chat_id=ADMIN_ID))

    print("🚀 Bot is running in MODULAR mode. Run main.py only!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())