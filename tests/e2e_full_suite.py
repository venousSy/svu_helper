import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

try:
    from telethon import TelegramClient
except ImportError:
    print("Telethon is not installed. Please run: pip install telethon")
    sys.exit(1)

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURATION ---
S_API_ID   = os.getenv("TEST_API_ID")
S_API_HASH = os.getenv("TEST_API_HASH")
A_API_ID   = os.getenv("ADMIN_TEST_API_ID")
A_API_HASH = os.getenv("ADMIN_TEST_API_HASH")
BOT_USERNAME = os.getenv("TARGET_BOT_USERNAME", "").strip()

if not all([S_API_ID, S_API_HASH, A_API_ID, A_API_HASH, BOT_USERNAME]):
    print("⛔ MISSING CREDENTIALS. Please check your .env file.")
    sys.exit(1)

if not BOT_USERNAME.startswith("@"):
    BOT_USERNAME = f"@{BOT_USERNAME}"

BTN_DONE = "انتهى"


# ============================================================
# SHARED HELPERS
# ============================================================

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
    await msg.click(data=target_btn.data)
    await asyncio.sleep(2)


async def submit_project(
    student,
    subject="E2E Subject",
    tutor="E2E Tutor",
    deadline="2026-12-31",
    details="E2E details text.",
):
    """
    Full project submission FSM — now uses the multi-attachment accumulation flow.
    Steps 1-3 are the same; step 4 sends details text, waits for ack, then presses انتهى.
    """
    await student.send_message(BOT_USERNAME, "/new_project")
    await wait_for_message(student, ["[1/4]", "المادة"])
    await student.send_message(BOT_USERNAME, subject)
    await wait_for_message(student, ["[2/4]", "المدرس"])
    await student.send_message(BOT_USERNAME, tutor)
    await wait_for_message(student, ["[3/4]", "التسليم", "Deadline"])
    await student.send_message(BOT_USERNAME, deadline)
    await wait_for_message(student, ["[4/4]", "التفاصيل", "وصف"])
    # --- NEW: accumulation loop ---
    await student.send_message(BOT_USERNAME, details)
    await wait_for_message(student, ["تم استلام", "انتهى", "المرفق"])
    await student.send_message(BOT_USERNAME, BTN_DONE)
    await wait_for_message(student, ["تم تقديم", "بنجاح"], timeout=15)


async def admin_make_offer(admin, price="30000", delivery="3 Days", notes="لا يوجد"):
    """Helper: Admin dispatches a pricing offer from an incoming alert."""
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
    """Accept offer + upload receipt + admin confirms payment. Returns when active."""
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


# ============================================================
# TEST RUNNER
# ============================================================
PASSED = []
FAILED = []
import traceback


async def run_test(name, coro):
    print(f"\n[🎬 {name}]")
    try:
        await coro
        PASSED.append(name)
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        traceback.print_exc()
        FAILED.append(name)


# ============================================================
# TEST DEFINITIONS
# ============================================================

async def test_cancellation(student):
    await student.send_message(BOT_USERNAME, "/new_project")
    await wait_for_message(student, ["[1/4]", "المادة"])
    await student.send_message(BOT_USERNAME, "/cancel")
    await wait_for_message(student, ["تم الإلغاء", "إلغاء"])
    print("  ✅ Cancellation flow works correctly.")


async def test_maintenance(admin, student):
    await admin.send_message(BOT_USERNAME, "/maintenance_on")
    await wait_for_message(admin, ["تم تفعيل"])
    await student.send_message(BOT_USERNAME, "/new_project")
    await wait_for_message(student, ["الصيانة", "maintenance"])
    print("  ✅ Student correctly blocked during maintenance.")
    await admin.send_message(BOT_USERNAME, "/maintenance_off")
    await wait_for_message(admin, ["إيقاف", "متاح"])
    print("  ✅ Maintenance mode disabled successfully.")


async def test_stats(admin):
    await admin.send_message(BOT_USERNAME, "/stats")
    await wait_for_message(admin, ["إحصائيات", "شامل"])
    print("  ✅ /stats responded without error.")


async def test_my_projects(student):
    await student.send_message(BOT_USERNAME, "/my_projects")
    await wait_for_message(student, ["مشاريع", "لم تقم"])
    print("  ✅ /my_projects responded without error.")


async def test_help(student):
    await student.send_message(BOT_USERNAME, "/help")
    await wait_for_message(student, ["الأوامر", "المتاحة"])
    print("  ✅ /help responded without error.")


async def test_submit_text_only(student, admin):
    """Full submission with plain text details (no file)."""
    await submit_project(student, subject="Text Only Subject")
    await wait_for_message(admin, ["مشروع جديد"], timeout=15)
    print("  ✅ Text-only project submitted and admin notified.")


async def test_pdf_upload(student, admin):
    """Submit a project using a PDF attachment in the accumulation step."""
    await student.send_message(BOT_USERNAME, "/new_project")
    await wait_for_message(student, ["[1/4]", "المادة"])
    await student.send_message(BOT_USERNAME, "PDF Test Subject")
    await wait_for_message(student, ["[2/4]", "المدرس"])
    await student.send_message(BOT_USERNAME, "PDF Tutor")
    await wait_for_message(student, ["[3/4]", "التسليم", "Deadline"])
    await student.send_message(BOT_USERNAME, "2026-12-31")
    await wait_for_message(student, ["[4/4]", "التفاصيل", "وصف"])

    with open("dummy_test.pdf", "w", encoding="utf-8") as f:
        f.write("%PDF-1.4\nE2E dummy PDF content for testing.")
    await student.send_file(BOT_USERNAME, "dummy_test.pdf")
    os.remove("dummy_test.pdf")

    # After upload the bot acks and shows انتهى button
    await wait_for_message(student, ["تم استلام", "المرفق", "انتهى"])
    print("  ✅ Bot acknowledged PDF upload.")

    # Finalize
    await student.send_message(BOT_USERNAME, BTN_DONE)
    await wait_for_message(student, ["تم تقديم", "بنجاح"], timeout=15)
    print("  ✅ PDF project submission accepted by bot.")

    await wait_for_message(admin, ["مشروع جديد"], timeout=15)
    print("  ✅ Admin received PDF project alert.")


async def test_multi_attachment(student, admin):
    """Submit a project with multiple items (text + two messages) accumulation."""
    await student.send_message(BOT_USERNAME, "/new_project")
    await wait_for_message(student, ["[1/4]", "المادة"])
    await student.send_message(BOT_USERNAME, "Multi-Attach Subject")
    await wait_for_message(student, ["[2/4]", "المدرس"])
    await student.send_message(BOT_USERNAME, "Multi Tutor")
    await wait_for_message(student, ["[3/4]", "التسليم"])
    await student.send_message(BOT_USERNAME, "2026-11-01")
    await wait_for_message(student, ["[4/4]", "التفاصيل"])

    # First item
    await student.send_message(BOT_USERNAME, "Part 1 details")
    await wait_for_message(student, ["تم استلام", "انتهى"])
    print("  ✅ First item acknowledged.")

    # Second item — a PDF
    with open("dummy_multi.pdf", "w", encoding="utf-8") as f:
        f.write("%PDF-1.4\nMulti-attach test.")
    await student.send_file(BOT_USERNAME, "dummy_multi.pdf")
    os.remove("dummy_multi.pdf")
    await wait_for_message(student, ["تم استلام", "انتهى"])
    print("  ✅ Second item (PDF) acknowledged.")

    # Finalize
    await student.send_message(BOT_USERNAME, BTN_DONE)
    await wait_for_message(student, ["تم تقديم", "بنجاح"], timeout=15)
    print("  ✅ Multi-attachment project submitted successfully.")

    await wait_for_message(admin, ["مشروع جديد"], timeout=15)
    print("  ✅ Admin received multi-attachment alert.")


async def test_cancel_during_accumulation(student):
    """Cancel mid-accumulation (after sending one item) using /cancel."""
    await student.send_message(BOT_USERNAME, "/new_project")
    await wait_for_message(student, ["[1/4]", "المادة"])
    await student.send_message(BOT_USERNAME, "Cancel Mid Subject")
    await wait_for_message(student, ["[2/4]", "المدرس"])
    await student.send_message(BOT_USERNAME, "Cancel Tutor")
    await wait_for_message(student, ["[3/4]", "التسليم"])
    await student.send_message(BOT_USERNAME, "2026-10-01")
    await wait_for_message(student, ["[4/4]", "التفاصيل"])
    await student.send_message(BOT_USERNAME, "Some details before cancel")
    await wait_for_message(student, ["تم استلام", "انتهى"])
    await student.send_message(BOT_USERNAME, "/cancel")
    await wait_for_message(student, ["تم الإلغاء", "إلغاء"])
    print("  ✅ Cancel during accumulation works correctly.")


async def test_admin_deny(student, admin):
    await submit_project(student, subject="Deny Test Subject")
    alert = await wait_for_message(admin, ["مشروع جديد"], timeout=15)
    await click_inline_button(admin, alert, "رفض")
    print("  ✅ Admin clicked Deny button.")
    await wait_for_message(student, ["تم رفض المشروع", "من قبل المشرف"], timeout=15)
    print("  ✅ Student received denial notification.")


async def test_reject_payment(student, admin):
    await submit_project(student, subject="RejectPay Test")
    await admin_make_offer(admin)

    offer_msg = await wait_for_message(student, ["عرض جديد"], timeout=15)
    await click_inline_button(student, offer_msg, "قبول")
    await wait_for_message(student, ["إيصال"])

    with open("dummy_receipt.pdf", "w", encoding="utf-8") as f:
        f.write("%PDF-1.4\nDummy receipt for reject payment test.")
    await student.send_file(BOT_USERNAME, "dummy_receipt.pdf")
    os.remove("dummy_receipt.pdf")
    await wait_for_message(student, ["استلام الإيصال"], timeout=15)

    receipt_msg = await wait_for_message(admin, ["verify_pay"], timeout=15)
    await click_inline_button(admin, receipt_msg, "رفض الدفع")
    print("  ✅ Admin rejected the payment.")

    await wait_for_message(student, ["رفض عملية الدفع", "رفض الدفع", "تعذر التحقق"], timeout=15)
    print("  ✅ Student received payment rejection notification.")


async def test_full_lifecycle(student, admin):
    await full_payment_cycle(student, admin, subject="Full Lifecycle Subject")
    print("  ✅ Full lifecycle (submit → offer → pay → confirm) completed.")


async def test_broadcast(admin, student):
    await admin.send_message(BOT_USERNAME, "/admin")
    await wait_for_message(admin, ["لوحة تحكم"])
    dashboard = (await admin.get_messages(BOT_USERNAME, limit=1))[0]
    await click_inline_button(admin, dashboard, "إرسال إعلان")
    await wait_for_message(admin, ["أدخل رسالة", "الإعلان"])
    print("  ✅ Admin entered broadcast FSM.")

    await admin.send_message(BOT_USERNAME, "📢 This is an automated E2E broadcast test message.")
    await wait_for_message(admin, ["تم الإرسال", "مستخدم"])
    print("  ✅ Broadcast sent successfully.")

    await wait_for_message(student, ["E2E broadcast test"], timeout=15)
    print("  ✅ Student received the broadcast message!")


async def test_student_deny_offer(student, admin):
    await submit_project(student, subject="Student Deny Offer")
    await admin_make_offer(admin)
    offer_msg = await wait_for_message(student, ["عرض جديد"], timeout=15)

    await click_inline_button(student, offer_msg, "رفض")
    print("  ✅ Student clicked Deny offer.")

    await wait_for_message(student, ["تم إغلاق", "رفض"], timeout=15)
    await wait_for_message(admin, ["تم رفض العرض", "الطالب"], timeout=15)
    print("  ✅ Admin notified of student denial.")


async def test_submit_finished_work(student, admin):
    await full_payment_cycle(student, admin, subject="Finish Work Subject")
    print("  ✅ Payment confirmed — project now active.")

    await admin.send_message(BOT_USERNAME, "/admin")
    dashboard = await wait_for_message(admin, ["لوحة تحكم"])
    await click_inline_button(admin, dashboard, "مقبولة/جارية")

    active_list = await wait_for_message(admin, ["مشاريع جارية", "🚀"], timeout=15)
    await click_inline_button(admin, active_list, "Finish Work Subject")

    await wait_for_message(admin, ["رفع الملف النهائي", "النهائي"], timeout=15)

    with open("dummy_final_work.pdf", "w", encoding="utf-8") as f:
        f.write("%PDF-1.4\nThis is the final delivered work.")
    await admin.send_file(BOT_USERNAME, "dummy_final_work.pdf")
    os.remove("dummy_final_work.pdf")

    await wait_for_message(admin, ["إنهاء", "تم إنهاء المشروع", "تسليم"], timeout=15)
    print("  ✅ Admin submitted final work.")

    await wait_for_message(student, ["إنجاز", "النهائي", "جاهز", "تم الانتهاء"], timeout=15)
    print("  ✅ Student received final work!")


async def test_admin_reports(admin):
    await admin.send_message(BOT_USERNAME, "/admin")
    dashboard = await wait_for_message(admin, ["لوحة تحكم"])
    await click_inline_button(admin, dashboard, "سجل المشاريع")
    await wait_for_message(admin, ["التاريخ", "سجل", "انتهى"], timeout=15)
    print("  ✅ Viewed Project History.")

    await admin.send_message(BOT_USERNAME, "/admin")
    dashboard2 = await wait_for_message(admin, ["لوحة تحكم"])
    await click_inline_button(admin, dashboard2, "سجل المدفوعات")
    await wait_for_message(admin, ["دفعات", "المدفوعات", "لا يوجد"], timeout=15)
    print("  ✅ Viewed Payments History.")


async def test_ticket_open_and_close(student, admin):
    """Student opens a support ticket, admin sees it, student closes it."""
    await student.send_message(BOT_USERNAME, "/start")
    await asyncio.sleep(1)
    start_msg = (await student.get_messages(BOT_USERNAME, limit=1))[0]
    await click_inline_button(student, start_msg, "الدعم الفني")
    support_menu = await wait_for_message(student, ["الدعم الفني"], timeout=10)
    await click_inline_button(student, support_menu, "فتح تذكرة جديدة")
    await wait_for_message(student, ["فتح تذكرة", "أرسل رسالتك"], timeout=10)
    print("  ✅ Student entered new ticket FSM.")

    await student.send_message(BOT_USERNAME, "E2E support ticket — please help!")
    ticket_ack = await wait_for_message(student, ["تم فتح التذكرة", "بنجاح"], timeout=15)
    print("  ✅ Ticket created successfully.")

    # Admin should receive the ticket in the forum group (verify via admin dashboard)
    await admin.send_message(BOT_USERNAME, "/admin")
    dashboard = await wait_for_message(admin, ["لوحة تحكم"])
    await click_inline_button(admin, dashboard, "التذاكر المفتوحة")
    await wait_for_message(admin, ["التذاكر", "تذكرة"], timeout=10)
    print("  ✅ Admin can see open tickets.")

    # Student views their tickets and closes the ticket
    await student.send_message(BOT_USERNAME, "/start")
    await asyncio.sleep(1)
    start_msg2 = (await student.get_messages(BOT_USERNAME, limit=1))[0]
    await click_inline_button(student, start_msg2, "الدعم الفني")
    support_menu2 = await wait_for_message(student, ["الدعم الفني"], timeout=10)
    await click_inline_button(student, support_menu2, "تذاكري المفتوحة")
    tickets_list = await wait_for_message(student, ["تذاكرك", "اختر تذكرة"], timeout=10)
    # Click first available ticket
    if tickets_list.reply_markup and hasattr(tickets_list.reply_markup, 'rows'):
        first_row = tickets_list.reply_markup.rows[0]
        if first_row.buttons:
            await tickets_list.click(data=first_row.buttons[0].data)
            await asyncio.sleep(2)
    ticket_detail = await wait_for_message(student, ["تذكرة #", "مفتوحة"], timeout=10)
    print("  ✅ Student viewing ticket detail.")

    await click_inline_button(student, ticket_detail, "إغلاق التذكرة")
    await wait_for_message(student, ["تم إغلاق التذكرة", "شكراً"], timeout=10)
    print("  ✅ Ticket closed by student.")


async def test_ticket_reply_flow(student, admin):
    """Student opens ticket, replies to it, then checks closed tickets log."""
    # Open ticket
    await student.send_message(BOT_USERNAME, "/start")
    await asyncio.sleep(1)
    start_msg = (await student.get_messages(BOT_USERNAME, limit=1))[0]
    await click_inline_button(student, start_msg, "الدعم الفني")
    support_menu = await wait_for_message(student, ["الدعم الفني"], timeout=10)
    await click_inline_button(student, support_menu, "فتح تذكرة جديدة")
    await wait_for_message(student, ["فتح تذكرة", "أرسل رسالتك"], timeout=10)
    await student.send_message(BOT_USERNAME, "E2E reply flow ticket test")
    await wait_for_message(student, ["تم فتح التذكرة", "بنجاح"], timeout=15)
    print("  ✅ Ticket opened for reply test.")

    # View tickets and reply
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
    print("  ✅ Reply sent successfully.")


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

async def run_full_suite():
    print("🚀 Initializing E2E Test Suite Orchestrator...")

    student = TelegramClient('student_session', S_API_ID, S_API_HASH)
    admin   = TelegramClient('admin_session',   A_API_ID, A_API_HASH)

    await student.start()
    await admin.start()
    print("✅ Both clients logged in successfully.\n")

    await run_test("TEST 1: Cancellation Flow",
                   test_cancellation(student))

    await run_test("TEST 2: Maintenance Mode",
                   test_maintenance(admin, student))

    await run_test("TEST 3: Admin /stats Command",
                   test_stats(admin))

    await run_test("TEST 4: Student /my_projects Command",
                   test_my_projects(student))

    await run_test("TEST 5: Help Command",
                   test_help(student))

    await run_test("TEST 6: Text-Only Project Submission",
                   test_submit_text_only(student, admin))

    await run_test("TEST 7: File Upload — PDF Document",
                   test_pdf_upload(student, admin))

    await run_test("TEST 8: Multi-Attachment Submission",
                   test_multi_attachment(student, admin))

    await run_test("TEST 9: Cancel During Accumulation",
                   test_cancel_during_accumulation(student))

    await run_test("TEST 10: Admin Deny Project",
                   test_admin_deny(student, admin))

    await run_test("TEST 11: Reject Payment Flow",
                   test_reject_payment(student, admin))

    await run_test("TEST 12: Full Lifecycle (Offer → Pay → Confirm)",
                   test_full_lifecycle(student, admin))

    await run_test("TEST 13: Admin Broadcast System",
                   test_broadcast(admin, student))

    await run_test("TEST 14: Student Deny Offer",
                   test_student_deny_offer(student, admin))

    await run_test("TEST 15: Admin Submit Finished Work",
                   test_submit_finished_work(student, admin))

    await run_test("TEST 16: Admin Viewing Reports",
                   test_admin_reports(admin))

    await run_test("TEST 17: Ticket Open and Close",
                   test_ticket_open_and_close(student, admin))

    await run_test("TEST 18: Ticket Reply Flow",
                   test_ticket_reply_flow(student, admin))

    # --- RESULTS ---
    print("\n" + "=" * 50)
    print(f"📊 RESULTS: {len(PASSED)} PASSED / {len(FAILED)} FAILED")
    print("=" * 50)
    for t in PASSED:
        print(f"  ✅ {t}")
    for t in FAILED:
        print(f"  ❌ {t}")

    if not FAILED:
        print("\n🏆 ALL TESTS PASSED! Bot is production-ready! 🏆")
    else:
        print(f"\n⚠️ {len(FAILED)} test(s) failed. Review output above.")

    await student.disconnect()
    await admin.disconnect()


if __name__ == '__main__':
    asyncio.run(run_full_suite())
