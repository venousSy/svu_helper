from tests.suites.e2e_helpers import (
    BOT_USERNAME, BTN_DONE, get_future_date, wait_for_message, click_inline_button
)
import os

async def test_cancellation(student, admin=None):
    await student.send_message(BOT_USERNAME, "/new_project")
    await wait_for_message(student, ["[1/4]", "المادة"])
    await student.send_message(BOT_USERNAME, "/cancel")
    await wait_for_message(student, ["تم الإلغاء", "إلغاء"])

async def test_maintenance(student, admin):
    await admin.send_message(BOT_USERNAME, "/maintenance_on")
    await wait_for_message(admin, ["تم تفعيل"])
    await student.send_message(BOT_USERNAME, "/new_project")
    await wait_for_message(student, ["الصيانة", "maintenance"])
    await admin.send_message(BOT_USERNAME, "/maintenance_off")
    await wait_for_message(admin, ["إيقاف", "متاح"])

async def test_stats(student, admin):
    await admin.send_message(BOT_USERNAME, "/stats")
    await wait_for_message(admin, ["إحصائيات", "شامل"])

async def test_my_projects(student, admin=None):
    await student.send_message(BOT_USERNAME, "/my_projects")
    await wait_for_message(student, ["مشاريع", "لم تقم"])

async def test_help(student, admin=None):
    await student.send_message(BOT_USERNAME, "/help")
    await wait_for_message(student, ["الأوامر", "المتاحة"])

async def test_multi_attachment(student, admin):
    await student.send_message(BOT_USERNAME, "/new_project")
    await wait_for_message(student, ["[1/4]", "المادة"])
    await student.send_message(BOT_USERNAME, "Multi-Attach Subject")
    await wait_for_message(student, ["[2/4]", "المدرس"])
    await student.send_message(BOT_USERNAME, "Multi Tutor")
    await wait_for_message(student, ["[3/4]", "التسليم"])
    await student.send_message(BOT_USERNAME, get_future_date(60))
    await wait_for_message(student, ["[4/4]", "التفاصيل"])

    await student.send_message(BOT_USERNAME, "Part 1 details")
    await wait_for_message(student, ["تم استلام", "انتهى"])

    with open("dummy_multi.pdf", "w", encoding="utf-8") as f:
        f.write("%PDF-1.4\nMulti-attach test.")
    await student.send_file(BOT_USERNAME, "dummy_multi.pdf")
    os.remove("dummy_multi.pdf")
    await wait_for_message(student, ["العدد الإجمالي: 2"])

    await student.send_message(BOT_USERNAME, BTN_DONE)
    await wait_for_message(student, ["تم تقديم", "بنجاح"], timeout=15)
    await wait_for_message(admin, ["مشروع جديد"], timeout=15)

async def test_cancel_during_accumulation(student, admin=None):
    await student.send_message(BOT_USERNAME, "/new_project")
    await wait_for_message(student, ["[1/4]", "المادة"])
    await student.send_message(BOT_USERNAME, "Cancel Mid Subject")
    await wait_for_message(student, ["[2/4]", "المدرس"])
    await student.send_message(BOT_USERNAME, "Cancel Tutor")
    await wait_for_message(student, ["[3/4]", "التسليم"])
    await student.send_message(BOT_USERNAME, get_future_date(45))
    await wait_for_message(student, ["[4/4]", "التفاصيل"])
    await student.send_message(BOT_USERNAME, "Some details before cancel")
    await wait_for_message(student, ["تم استلام", "انتهى"])
    await student.send_message(BOT_USERNAME, "/cancel")
    await wait_for_message(student, ["تم الإلغاء", "إلغاء"])

async def test_admin_reports(student, admin):
    await admin.send_message(BOT_USERNAME, "/admin")
    dashboard = await wait_for_message(admin, ["لوحة تحكم"])
    await click_inline_button(admin, dashboard, "سجل المشاريع")
    await wait_for_message(admin, ["التاريخ", "سجل", "انتهى"], timeout=15)

    await admin.send_message(BOT_USERNAME, "/admin")
    dashboard2 = await wait_for_message(admin, ["لوحة تحكم"])
    await click_inline_button(admin, dashboard2, "سجل المدفوعات")
    await wait_for_message(admin, ["دفعات", "المدفوعات", "لا يوجد"], timeout=15)

def get_tests():
    return {
        "Cancellation": test_cancellation,
        "Maintenance": test_maintenance,
        "Stats": test_stats,
        "My Projects": test_my_projects,
        "Help": test_help,
        "Multi Attachment": test_multi_attachment,
        "Cancel During Accumulation": test_cancel_during_accumulation,
        "Admin Reports": test_admin_reports,
    }
