import asyncio
from tests.suites.e2e_helpers import (
    BOT_USERNAME, wait_for_message, click_inline_button
)

async def test_ticket_open_and_close(student, admin):
    await student.send_message(BOT_USERNAME, "/start")
    await asyncio.sleep(1)
    start_msg = (await student.get_messages(BOT_USERNAME, limit=1))[0]
    await click_inline_button(student, start_msg, "الدعم الفني")
    support_menu = await wait_for_message(student, ["الدعم الفني"], timeout=10)
    await click_inline_button(student, support_menu, "فتح تذكرة جديدة")
    await wait_for_message(student, ["فتح تذكرة", "أرسل رسالتك"], timeout=10)

    await student.send_message(BOT_USERNAME, "E2E support ticket — please help!")
    await wait_for_message(student, ["تم فتح التذكرة", "بنجاح"], timeout=15)

    await admin.send_message(BOT_USERNAME, "/admin")
    dashboard = await wait_for_message(admin, ["لوحة تحكم"])
    await click_inline_button(admin, dashboard, "التذاكر المفتوحة")
    await wait_for_message(admin, ["التذاكر", "تذكرة"], timeout=10)

    await student.send_message(BOT_USERNAME, "/start")
    await asyncio.sleep(1)
    start_msg2 = (await student.get_messages(BOT_USERNAME, limit=1))[0]
    await click_inline_button(student, start_msg2, "الدعم الفني")
    support_menu2 = await wait_for_message(student, ["الدعم الفني"], timeout=10)
    await click_inline_button(student, support_menu2, "تذاكري المفتوحة")
    tickets_list = await wait_for_message(student, ["تذاكرك", "اختر تذكرة"], timeout=10)
    
    if tickets_list.reply_markup and hasattr(tickets_list.reply_markup, 'rows'):
        first_row = tickets_list.reply_markup.rows[0]
        if first_row.buttons:
            await tickets_list.click(data=first_row.buttons[0].data)
            await asyncio.sleep(2)
            
    ticket_detail = await wait_for_message(student, ["تذكرة #", "مفتوحة"], timeout=10)
    await click_inline_button(student, ticket_detail, "إغلاق التذكرة")
    await wait_for_message(student, ["تم إغلاق التذكرة", "شكراً"], timeout=10)

async def test_ticket_reply_flow(student, admin):
    await student.send_message(BOT_USERNAME, "/start")
    await asyncio.sleep(1)
    start_msg = (await student.get_messages(BOT_USERNAME, limit=1))[0]
    await click_inline_button(student, start_msg, "الدعم الفني")
    support_menu = await wait_for_message(student, ["الدعم الفني"], timeout=10)
    await click_inline_button(student, support_menu, "فتح تذكرة جديدة")
    await wait_for_message(student, ["فتح تذكرة", "أرسل رسالتك"], timeout=10)
    await student.send_message(BOT_USERNAME, "E2E reply flow ticket test")
    await wait_for_message(student, ["تم فتح التذكرة", "بنجاح"], timeout=15)

    await student.send_message(BOT_USERNAME, "/start")
    await asyncio.sleep(1)
    start_msg2 = (await student.get_messages(BOT_USERNAME, limit=1))[0]
    await click_inline_button(student, start_msg2, "الدعم الفني")
    support_menu2 = await wait_for_message(student, ["الدعم الفني"], timeout=10)
    await click_inline_button(student, support_menu2, "تذاكري المفتوحة")
    tickets_list = await wait_for_message(student, ["تذاكرك", "اختر تذكرة"], timeout=10)
    if tickets_list.reply_markup and hasattr(tickets_list.reply_markup, 'rows'):
        first_row = tickets_list.reply_markup.rows[0]
        if first_row.buttons:
            await tickets_list.click(data=first_row.buttons[0].data)
            await asyncio.sleep(2)
            
    ticket_detail = await wait_for_message(student, ["تذكرة #", "مفتوحة"], timeout=10)
    await click_inline_button(student, ticket_detail, "إرسال رد")
    await wait_for_message(student, ["الرد على تذكرة", "أرسل رسالتك"], timeout=10)
    await student.send_message(BOT_USERNAME, "This is my follow-up reply.")
    await wait_for_message(student, ["تم إرسال ردك", "التذكرة #"], timeout=10)

def get_tests():
    return {
        "Ticket Open and Close": test_ticket_open_and_close,
        "Ticket Reply Flow": test_ticket_reply_flow,
    }
