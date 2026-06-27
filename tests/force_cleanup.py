import asyncio
from telethon import TelegramClient
from config import settings
import re

S_API_ID = 35428933
S_API_HASH = '0788ae56dd4cc256681684bb52941624'
A_API_ID = 30162563
A_API_HASH = 'ef45a964973a8ade5e86f704a37d4565'
BOT_USERNAME = "@SvuAssistant_bot"

async def click_inline_button(client, msg, text_match):
    if not msg.reply_markup:
        raise Exception("No reply markup")
    for row in msg.reply_markup.rows:
        for btn in row.buttons:
            if text_match in btn.text:
                await msg.click(data=btn.data)
                return
    raise Exception(f"Button {text_match} not found")

async def force_cleanup():
    host = TelegramClient('student_session', S_API_ID, S_API_HASH)
    seeker = TelegramClient('admin_session', A_API_ID, A_API_HASH)
    await host.start()
    await seeker.start()
    
    for client in [host, seeker]:
        await client.send_message(BOT_USERNAME, "/cancel")
        await asyncio.sleep(1)
        await client.send_message(BOT_USERNAME, "🤝 فريق العمل")
        await asyncio.sleep(2)
        msgs = await client.get_messages(BOT_USERNAME, limit=1)
        try:
            await click_inline_button(client, msgs[0], "فرقي المفتوحة")
            await asyncio.sleep(2)
            msgs2 = await client.get_messages(BOT_USERNAME, limit=1)
            await click_inline_button(client, msgs2[0], "حذف")
            await asyncio.sleep(1)
            print(f"Deleted team for {client.session.filename}")
        except Exception:
            pass
            
        await client.send_message(BOT_USERNAME, "🤝 فريق العمل")
        await asyncio.sleep(2)
        msgs = await client.get_messages(BOT_USERNAME, limit=1)
        try:
            await click_inline_button(client, msgs[0], "طلبات الانضمام المعلقة")
            await asyncio.sleep(2)
            msgs2 = await client.get_messages(BOT_USERNAME, limit=1)
            await click_inline_button(client, msgs2[0], "سحب الطلب")
            await asyncio.sleep(1)
            print(f"Withdrawn join for {client.session.filename}")
        except Exception:
            pass
            
    await host.disconnect()
    await seeker.disconnect()

if __name__ == "__main__":
    asyncio.run(force_cleanup())
