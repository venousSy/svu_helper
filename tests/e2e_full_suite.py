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
S_API_ID = os.getenv("TEST_API_ID")
S_API_HASH = os.getenv("TEST_API_HASH")
A_API_ID = os.getenv("ADMIN_TEST_API_ID")
A_API_HASH = os.getenv("ADMIN_TEST_API_HASH")
BOT_USERNAME = os.getenv("TARGET_BOT_USERNAME", "").strip()

if not all([S_API_ID, S_API_HASH, A_API_ID, A_API_HASH, BOT_USERNAME]):
    print("⛔ MISSING CREDENTIALS. Please check your .env file.")
    sys.exit(1)

if not BOT_USERNAME.startswith("@"):
    BOT_USERNAME = f"@{BOT_USERNAME}"


# --- HELPERS ---
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

async def submit_project(student, subject="E2E Subject", tutor="E2E Tutor", deadline="Tomorrow", details="E2E details text."):
    """Helper: Runs through the full project submission FSM."""
    await student.send_message(BOT_USERNAME, "/new_project")
    await wait_for_message(student, ["المادة"])
    await student.send_message(BOT_USERNAME, subject)
    await wait_for_message(student, ["المدرس"])
    await student.send_message(BOT_USERNAME, tutor)
    await wait_for_message(student, ["التسليم", "Deadline"])
    await student.send_message(BOT_USERNAME, deadline)
    await wait_for_message(student, ["التفاصيل", "وصف"])
    await student.send_message(BOT_USERNAME, details)
    await wait_for_message(student, ["تم تقديم", "بنجاح"], timeout=15)

async def admin_make_offer(admin, price="30000", delivery="3 Days", notes="لا يوجد"):
    """Helper: Admin dispatches a pricing offer from an incoming alert."""
    alert = await wait_for_message(admin, ["مشروع جديد"], timeout=15)
    await click_inline_button(admin, alert, "إرسال عرض")
    await wait_for_message(admin, ["السعر"])
    await admin.send_message(BOT_USERNAME, price)
    await wait_for_message(admin, ["تاريخ", "تسليم"])
    await admin.send_message(BOT_USERNAME, delivery)
    await wait_for_message(admin, ["ملاحظات", "نعم", "لا"])
    await admin.send_message(BOT_USERNAME, notes)
    await wait_for_message(admin, ["تم إرسال", "بنجاح"])


# ============================================================
# MAIN TEST SUITE
# ============================================================
PASSED = []
FAILED = []

import traceback

async def run_test(name, coro):
    """Runs a single named test, tracking pass/fail."""
    print(f"\n[🎬 {name}]")
    try:
        await coro
        PASSED.append(name)
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        traceback.print_exc()
        FAILED.append(name)


async def run_full_suite():
    print("🚀 Initializing E2E Test Suite Orchestrator...")

    student = TelegramClient('student_session', S_API_ID, S_API_HASH)
    admin = TelegramClient('admin_session', A_API_ID, A_API_HASH)

    await student.start()
    await admin.start()
    print("✅ Both clients logged in successfully.\n")

    # --- TEST 1: CANCELLATION ---
    async def test_cancellation():
        await student.send_message(BOT_USERNAME, "/new_project")
        await wait_for_message(student, ["المادة"])
        await student.send_message(BOT_USERNAME, "/cancel")
        await wait_for_message(student, ["تم الإلغاء", "إلغاء"])
        print("  ✅ Cancellation flow works correctly.")
    await run_test("TEST 1: Cancellation Flow", test_cancellation())

    # --- TEST 2: MAINTENANCE MODE ---
    async def test_maintenance():
        await admin.send_message(BOT_USERNAME, "/maintenance_on")
        await wait_for_message(admin, ["تم تفعيل"])
        await student.send_message(BOT_USERNAME, "/new_project")
        await wait_for_message(student, ["الصيانة", "maintenance"])
        print("  ✅ Student correctly blocked during maintenance.")
        await admin.send_message(BOT_USERNAME, "/maintenance_off")
        await wait_for_message(admin, ["إيقاف", "متاح"])
        print("  ✅ Maintenance mode disabled successfully.")
    await run_test("TEST 2: Maintenance Mode", test_maintenance())

    # --- TEST 3: STATS COMMAND ---
    async def test_stats():
        await admin.send_message(BOT_USERNAME, "/stats")
        await wait_for_message(admin, ["إحصائيات", "شامل"])
        print("  ✅ /stats responded without error.")
    await run_test("TEST 3: Admin /stats Command", test_stats())

    # --- TEST 4: MY_PROJECTS COMMAND ---
    async def test_my_projects():
        await student.send_message(BOT_USERNAME, "/my_projects")
        await wait_for_message(student, ["مشاريع", "لم تقم"])
        print("  ✅ /my_projects responded without error.")
    await run_test("TEST 4: Student /my_projects Command", test_my_projects())

    # --- TEST 5: FILE UPLOAD - PDF ---
    async def test_pdf_upload():
        await student.send_message(BOT_USERNAME, "/new_project")
        await wait_for_message(student, ["المادة"])
        await student.send_message(BOT_USERNAME, "PDF Test Subject")
        await wait_for_message(student, ["المدرس"])
        await student.send_message(BOT_USERNAME, "PDF Tutor")
        await wait_for_message(student, ["التسليم", "Deadline"])
        await student.send_message(BOT_USERNAME, "Next Week")
        await wait_for_message(student, ["التفاصيل", "وصف"])

        with open("dummy_test.pdf", "w", encoding="utf-8") as f:
            f.write("%PDF-1.4\nE2E dummy PDF content for testing.")
        await student.send_file(BOT_USERNAME, "dummy_test.pdf")
        os.remove("dummy_test.pdf")

        await wait_for_message(student, ["تم تقديم", "بنجاح"], timeout=15)
        print("  ✅ PDF project submission accepted by bot.")

        # Admin verifies receipt
        await wait_for_message(admin, ["مشروع جديد"], timeout=15)
        print("  ✅ Admin received PDF project alert.")
    await run_test("TEST 5: File Upload — PDF Document", test_pdf_upload())

    # --- TEST 6: ADMIN DENY PROJECT ---
    async def test_admin_deny():
        await submit_project(student, subject="Deny Test Subject")
        alert = await wait_for_message(admin, ["مشروع جديد"], timeout=15)
        await click_inline_button(admin, alert, "رفض")
        print("  ✅ Admin clicked Deny button.")
        await wait_for_message(student, ["تم رفض المشروع", "من قبل المشرف"], timeout=15)
        print("  ✅ Student received denial notification.")
    await run_test("TEST 6: Admin Deny Project", test_admin_deny())

    # --- TEST 7: REJECT PAYMENT ---
    async def test_reject_payment():
        await submit_project(student, subject="RejectPay Test")
        await admin_make_offer(admin)

        # Student accepts offer
        offer_msg = await wait_for_message(student, ["عرض جديد"], timeout=15)
        await click_inline_button(student, offer_msg, "قبول")
        await wait_for_message(student, ["إيصال"])

        # Student uploads receipt
        with open("dummy_receipt.pdf", "w", encoding="utf-8") as f:
            f.write("%PDF-1.4\nDummy receipt for reject payment test.")
        await student.send_file(BOT_USERNAME, "dummy_receipt.pdf")
        os.remove("dummy_receipt.pdf")
        await wait_for_message(student, ["استلام الإيصال"], timeout=15)

        # Admin REJECTS the payment
        receipt_msg = await wait_for_message(admin, ["verify_pay"], timeout=15)
        await click_inline_button(admin, receipt_msg, "رفض الدفع")
        print("  ✅ Admin rejected the payment.")

        # Student receives rejection notification
        await wait_for_message(student, ["رفض عملية الدفع", "رفض الدفع", "تعذر التحقق"], timeout=15)
        print("  ✅ Student received payment rejection notification.")
    await run_test("TEST 7: Reject Payment Flow", test_reject_payment())

    # --- TEST 8: FULL LIFECYCLE (Offer -> Pay -> Confirm) ---
    async def test_full_lifecycle():
        await submit_project(student, subject="Full Lifecycle Subject")
        await admin_make_offer(admin)
        print("  ✅ Admin dispatched the offer.")

        offer_msg = await wait_for_message(student, ["عرض جديد"], timeout=15)
        await click_inline_button(student, offer_msg, "قبول")
        await wait_for_message(student, ["إيصال"])

        with open("dummy_lifecycle.pdf", "w", encoding="utf-8") as f:
            f.write("%PDF-1.4\nDummy receipt for full lifecycle test.")
        await student.send_file(BOT_USERNAME, "dummy_lifecycle.pdf")
        os.remove("dummy_lifecycle.pdf")
        await wait_for_message(student, ["استلام الإيصال"], timeout=15)
        print("  ✅ Student uploaded receipt.")

        receipt_msg = await wait_for_message(admin, ["verify_pay"], timeout=15)
        await click_inline_button(admin, receipt_msg, "تأكيد الدفع")
        print("  ✅ Admin confirmed payment.")

        await wait_for_message(student, ["تم تأكيد الدفع", "بدأ العمل"], timeout=15)
        print("  ✅ Student notified project is now Active!")
    await run_test("TEST 8: Full Lifecycle (Offer → Pay → Confirm)", test_full_lifecycle())

    # --- TEST 9: BROADCAST ---
    async def test_broadcast():
        await admin.send_message(BOT_USERNAME, "/admin")
        await wait_for_message(admin, ["لوحة تحكم"])

        dashboard = (await admin.get_messages(BOT_USERNAME, limit=1))[0]
        await click_inline_button(admin, dashboard, "إرسال إعلان")
        await wait_for_message(admin, ["أدخل رسالة", "الإعلان"])
        print("  ✅ Admin entered broadcast FSM.")

        await admin.send_message(BOT_USERNAME, "📢 This is an automated E2E broadcast test message.")
        await wait_for_message(admin, ["تم الإرسال", "مستخدم"])
        print("  ✅ Broadcast sent successfully.")

        # Student should receive it
        await wait_for_message(student, ["E2E broadcast test"], timeout=15)
        print("  ✅ Student received the broadcast message!")
    await run_test("TEST 9: Admin Broadcast System", test_broadcast())

    # --- TEST 10: HELP COMMAND ---
    async def test_help():
        await student.send_message(BOT_USERNAME, "/help")
        await wait_for_message(student, ["الأوامر", "المتاحة"])
        print("  ✅ /help responded without error.")
    await run_test("TEST 10: Help Command", test_help())

    # --- TEST 11: STUDENT DENY OFFER ---
    async def test_student_deny_offer():
        await submit_project(student, subject="Student Deny Offer")
        await admin_make_offer(admin)
        offer_msg = await wait_for_message(student, ["عرض جديد"], timeout=15)
        
        # Student denies the offer
        await click_inline_button(student, offer_msg, "رفض")
        print("  ✅ Student clicked Deny offer.")
        
        # Student gets confirmation of closure
        await wait_for_message(student, ["تم إغلاق", "رفض"], timeout=15)
        
        # Admin gets notification that student denied it
        await wait_for_message(admin, ["تم رفض العرض", "الطالب"], timeout=15)
        print("  ✅ Admin notified of student denial.")
    await run_test("TEST 11: Student Deny Offer", test_student_deny_offer())

    # --- TEST 12: ADMIN SUBMIT FINISHED WORK ---
    async def test_submit_finished_work():
        await submit_project(student, subject="Finish Work Subject")
        await admin_make_offer(admin)
        
        offer_msg = await wait_for_message(student, ["عرض جديد"], timeout=15)
        await click_inline_button(student, offer_msg, "قبول")
        await wait_for_message(student, ["إيصال"])
        
        with open("dummy_receipt_fin.pdf", "w", encoding="utf-8") as f:
            f.write("%PDF-1.4\nDummy receipt")
        await student.send_file(BOT_USERNAME, "dummy_receipt_fin.pdf")
        os.remove("dummy_receipt_fin.pdf")
        await wait_for_message(student, ["استلام الإيصال"], timeout=15)
        
        receipt_msg = await wait_for_message(admin, ["verify_pay"], timeout=15)
        await click_inline_button(admin, receipt_msg, "تأكيد الدفع")
        await wait_for_message(student, ["تأكيد الدفع", "بدأ العمل"], timeout=15)
        
        # Project is ACCEPTED (Active). Admin needs to submit work.
        await admin.send_message(BOT_USERNAME, "/admin")
        dashboard = await wait_for_message(admin, ["لوحة تحكم"])
        await click_inline_button(admin, dashboard, "مقبولة/جارية")
        
        active_list = await wait_for_message(admin, ["مشاريع جارية", "🚀"], timeout=15)
        await click_inline_button(admin, active_list, "إنهاء")
        
        # Admin is waiting for finished work upload
        upload_prompt = await wait_for_message(admin, ["رفع الملف النهائي", "النهائي"], timeout=15)
        
        with open("dummy_final_work.pdf", "w", encoding="utf-8") as f:
            f.write("%PDF-1.4\nThis is the final delivered work.")
        await admin.send_file(BOT_USERNAME, "dummy_final_work.pdf")
        os.remove("dummy_final_work.pdf")
        
        # Project finished msgs
        await wait_for_message(admin, ["إنهاء", "تم إنهاء المشروع", "تسليم"], timeout=15)
        print("  ✅ Admin submitted final work.")
        
        await wait_for_message(student, ["إنجاز", "النهائي", "جاهز", "تم الانتهاء"], timeout=15)
        print("  ✅ Student received final work!")
        
    await run_test("TEST 12: Admin Submit Finished Work", test_submit_finished_work())

    # --- TEST 13: ADMIN REPORTS ---
    async def test_admin_reports():
        await admin.send_message(BOT_USERNAME, "/admin")
        dashboard = await wait_for_message(admin, ["لوحة تحكم"])
        
        await click_inline_button(admin, dashboard, "سجل المشاريع")
        await wait_for_message(admin, ["التاريخ", "سجل", "انتهى"], timeout=15)
        print("  ✅ Viewed Project History.")
        
        await admin.send_message(BOT_USERNAME, "/admin")
        dashboard2 = await wait_for_message(admin, ["لوحة تحكم"])
        
        # The button "سجل المدفوعات" might not exist if using another text, let's look at views.py
        # Actually it's 'view_payments' action. In admin_kb.py: "سجل المدفوعات".
        await click_inline_button(admin, dashboard2, "سجل المدفوعات")
        await wait_for_message(admin, ["دفعات", "المدفوعات", "لا يوجد"], timeout=15)
        print("  ✅ Viewed Payments History.")
        
    await run_test("TEST 13: Admin Viewing Reports", test_admin_reports())

    # --- RESULTS SUMMARY ---
    print("\n" + "="*50)
    print(f"📊 RESULTS: {len(PASSED)} PASSED / {len(FAILED)} FAILED")
    print("="*50)
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
