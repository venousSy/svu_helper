import asyncio
import os
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

try:
    from telethon import TelegramClient
except ImportError:
    print("Telethon is not installed. Please run: pip install telethon")
    sys.exit(1)

BOT_USERNAME = os.getenv("TARGET_BOT_USERNAME", "").strip()
if not BOT_USERNAME.startswith("@"):
    BOT_USERNAME = f"@{BOT_USERNAME}"

BTN_DONE = "انتهى"

# --- Monkey-patch TelegramClient for throttling ---
original_send_message = TelegramClient.send_message
original_send_file = TelegramClient.send_file

async def throttled_send_message(self, *args, **kwargs):
    await asyncio.sleep(0.6)
    return await original_send_message(self, *args, **kwargs)

async def throttled_send_file(self, *args, **kwargs):
    await asyncio.sleep(0.6)
    return await original_send_file(self, *args, **kwargs)

TelegramClient.send_message = throttled_send_message
TelegramClient.send_file = throttled_send_file

def get_future_date(days=30):
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

async def wait_for_message(client, expected_text, timeout=15, error_msg="Timeout"):
    """Polls for a bot message matching any of the expected_text keywords."""
    last_msg = "None"
    for _ in range(timeout):
        try:
            msgs = await client.get_messages(BOT_USERNAME, limit=3)
            if msgs:
                last_msg = msgs[0].text or "Empty message"
                for msg in msgs:
                    content = msg.text or ""
                    if content and any(word in content for word in expected_text):
                        return msg
        except Exception as e:
            if "database is locked" not in str(e):
                print(f"  Ignored minor API error: {e}")
        await asyncio.sleep(1)
    raise Exception(f"{error_msg}. Last msg was: {last_msg}")

async def click_inline_button(client, msg, text_match, error_msg="Button not found"):
    """Finds and clicks an inline keyboard button by partial text match."""
    target_btn = None
    if msg and msg.reply_markup and hasattr(msg.reply_markup, 'rows'):
        for row in msg.reply_markup.rows:
            for btn in row.buttons:
                if text_match in btn.text:
                    target_btn = btn
                    break
            if target_btn:
                break
    if not target_btn:
        raise Exception(f"{error_msg}. Button containing '{text_match}' not found.")
    await asyncio.sleep(0.6)
    await msg.click(data=target_btn.data)
    await asyncio.sleep(2)

async def submit_project(
    student,
    subject="E2E Subject",
    tutor="E2E Tutor",
    deadline=None,
    details="E2E details text.",
):
    if deadline is None:
        deadline = get_future_date(30)
    await student.send_message(BOT_USERNAME, "/new_project")
    await wait_for_message(student, ["[1/4]", "المادة"])
    await student.send_message(BOT_USERNAME, subject)
    await wait_for_message(student, ["[2/4]", "المدرس"])
    await student.send_message(BOT_USERNAME, tutor)
    await wait_for_message(student, ["[3/4]", "التسليم", "Deadline"])
    await student.send_message(BOT_USERNAME, deadline)
    await wait_for_message(student, ["[4/4]", "التفاصيل", "وصف"])
    await student.send_message(BOT_USERNAME, details)
    await wait_for_message(student, ["تم استلام", "انتهى", "المرفق"])
    await student.send_message(BOT_USERNAME, BTN_DONE)
    await wait_for_message(student, ["تم تقديم", "بنجاح"], timeout=15)

async def admin_make_offer(admin, price="30000", delivery=None, notes="لا يوجد"):
    if delivery is None:
        delivery = get_future_date(15)
    alert = await wait_for_message(admin, ["مشروع جديد"], timeout=15)
    await click_inline_button(admin, alert, "إرسال عرض")
    await wait_for_message(admin, ["[1/3]", "السعر"])
    await admin.send_message(BOT_USERNAME, price)
    await wait_for_message(admin, ["[2/3]", "تاريخ", "تسليم"])
    await admin.send_message(BOT_USERNAME, delivery)
    await wait_for_message(admin, ["[3/3]", "ملاحظات"])
    await admin.send_message(BOT_USERNAME, "نعم")
    await wait_for_message(admin, ["اكتب", "ملاحظاتك", "🖋"])
    await admin.send_message(BOT_USERNAME, notes)
    await wait_for_message(admin, ["تم إرسال", "بنجاح"])

async def full_payment_cycle(student, admin, subject):
    await submit_project(student, subject=subject)
    await admin_make_offer(admin)

    offer_msg = await wait_for_message(student, ["عرض جديد"], timeout=15)
    await click_inline_button(student, offer_msg, "قبول")
    await wait_for_message(student, ["إيصال"])

    fname = f"dummy_receipt_{subject[:8].replace(' ', '_')}.pdf"
    with open(fname, "w", encoding="utf-8") as f:
        f.write("%PDF-1.4\nDummy receipt.")
    await student.send_file(BOT_USERNAME, fname)
    os.remove(fname)
    await wait_for_message(student, ["استلام الإيصال"], timeout=15)

    receipt_msg = await wait_for_message(admin, ["verify_pay"], timeout=15)
    await click_inline_button(admin, receipt_msg, "تأكيد الدفع")
    await wait_for_message(student, ["تأكيد الدفع", "بدأ العمل"], timeout=15)
