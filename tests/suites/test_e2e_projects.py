import os
from tests.suites.e2e_helpers import (
    BOT_USERNAME, wait_for_message, click_inline_button,
    submit_project, admin_make_offer, full_payment_cycle
)

async def test_admin_deny(student, admin):
    await submit_project(student, subject="Deny Test Subject")
    alert = await wait_for_message(admin, ["مشروع جديد"], timeout=15)
    await click_inline_button(admin, alert, "رفض")
    await wait_for_message(student, ["تم رفض المشروع", "من قبل المشرف"], timeout=15)

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
    await wait_for_message(student, ["رفض عملية الدفع", "رفض الدفع", "تعذر التحقق"], timeout=15)

async def test_student_deny_offer(student, admin):
    await submit_project(student, subject="Student Deny Offer")
    await admin_make_offer(admin)
    offer_msg = await wait_for_message(student, ["عرض جديد"], timeout=15)

    await click_inline_button(student, offer_msg, "رفض")
    await wait_for_message(student, ["تم إغلاق", "رفض"], timeout=15)
    await wait_for_message(admin, ["تم رفض العرض", "الطالب"], timeout=15)

async def test_submit_finished_work(student, admin):
    await full_payment_cycle(student, admin, subject="Finish Work Subject")
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
    await wait_for_message(student, ["إنجاز", "النهائي", "جاهز", "تم الانتهاء"], timeout=15)

def get_tests():
    return {
        "Admin Deny": test_admin_deny,
        "Reject Payment": test_reject_payment,
        "Student Deny Offer": test_student_deny_offer,
        "Submit Finished Work": test_submit_finished_work,
    }
