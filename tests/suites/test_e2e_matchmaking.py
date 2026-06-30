import asyncio
import uuid
from tests.suites.e2e_helpers import (
    BOT_USERNAME, wait_for_message, click_inline_button
)

async def open_team_menu(client):
    await client.send_message(BOT_USERNAME, "/start")
    await asyncio.sleep(1)
    start_msg = (await client.get_messages(BOT_USERNAME, limit=1))[0]
    await click_inline_button(client, start_msg, "فريق العمل")
    
    msg = await wait_for_message(client, ["زملاء", "فريق العمل", "اختصاص", "اختصاصك"], timeout=10)
    if "اختصاص" in msg.text:
        if msg.reply_markup and hasattr(msg.reply_markup, 'rows'):
            first_btn = msg.reply_markup.rows[0].buttons[0]
            await msg.click(data=first_btn.data)
            await asyncio.sleep(2)
        msg = await wait_for_message(client, ["زملاء", "فريق العمل"], timeout=10)
    return msg

async def clear_chat_history_view(client):
    for _ in range(3):
        await client.send_message(BOT_USERNAME, "/help")
        await asyncio.sleep(0.5)

E2E_COURSE_NAME = ""

async def cleanup_user_state(client):
    session_name = getattr(client.session, 'filename', 'MemorySession')
    print(f"🧹 Cleaning up state for {session_name}...")
    try:
        await client.send_message(BOT_USERNAME, "/start")
        await asyncio.sleep(1)
        
        team_menu = await open_team_menu(client)
        if team_menu:
            try:
                await click_inline_button(client, team_menu, "فرقي المفتوحة")
                teams_msg = await wait_for_message(client, ["حذف", "لا توجد", "إغلاق"], timeout=5)
                if "حذف" in teams_msg.text:
                    await click_inline_button(client, teams_msg, "حذف")
                    await asyncio.sleep(2)
            except Exception:
                pass
            
        team_menu2 = await open_team_menu(client)
        if team_menu2:
            try:
                await click_inline_button(client, team_menu2, "طلباتي المعلقة")
                joins_msg = await wait_for_message(client, ["سحب الطلب", "لا توجد"], timeout=5)
                if "سحب الطلب" in joins_msg.text:
                    await click_inline_button(client, joins_msg, "سحب الطلب")
                    await asyncio.sleep(2)
            except Exception:
                pass
    except Exception as e:
        print(f"  ⚠️ Cleanup error (ignoring): {e}")

async def test_team_creation(host, seeker=None):
    team_menu = await open_team_menu(host)
    await click_inline_button(host, team_menu, "إنشاء فريق")
    await wait_for_message(host, ["المادة"], timeout=10)
    
    course_name = f"E2E Course {uuid.uuid4().hex[:6]}"
    await host.send_message(BOT_USERNAME, course_name)
    await wait_for_message(host, ["دكتور", "منسق"], timeout=10)
    
    await host.send_message(BOT_USERNAME, "Dr. E2E")
    count_msg = await wait_for_message(host, ["عضو", "تحتاج"], timeout=10)
    await click_inline_button(host, count_msg, "2 أعضاء")
    
    await wait_for_message(host, ["تم إنشاء طلب الفريق", "بنجاح"], timeout=15)
    
    global E2E_COURSE_NAME
    E2E_COURSE_NAME = course_name

async def test_team_concurrency(host, seeker=None):
    team_menu = await open_team_menu(host)
    await click_inline_button(host, team_menu, "إنشاء فريق")
    await wait_for_message(host, ["المادة"], timeout=10)
    
    await host.send_message(BOT_USERNAME, E2E_COURSE_NAME)
    await wait_for_message(host, ["دكتور", "منسق"], timeout=10)
    
    await host.send_message(BOT_USERNAME, "Dr. E2E")
    count_msg = await wait_for_message(host, ["عضو", "تحتاج"], timeout=10)
    res = await click_inline_button(host, count_msg, "2 أعضاء")
    if not res or not res.message or not any(w in res.message for w in ["يوجد فريق مفتوح مسبقاً", "عذراً"]):
        raise Exception(f"Expected concurrency alert, got {res.message if res else 'None'}")

async def test_team_join_and_withdraw(host, seeker):
    await clear_chat_history_view(host)
    team_menu = await open_team_menu(seeker)
    
    await click_inline_button(seeker, team_menu, "البحث عن فريق")
    find_msg = await wait_for_message(seeker, ["فريق #", "لا توجد فرق"], timeout=10)
    if "لا توجد فرق" in find_msg.text:
        raise Exception("No teams found for joining, but one should exist.")
        
    res = await click_inline_button(seeker, find_msg, "انضمام")
    if not res or not res.message or not any(w in res.message for w in ["تم إرسال طلب الانضمام", "بنجاح"]):
        raise Exception(f"Expected join success alert, got {res.message if res else 'None'}")
    
    await wait_for_message(host, ["طلب انضمام"], timeout=15)
    
    team_menu2 = await open_team_menu(seeker)
    await click_inline_button(seeker, team_menu2, "طلباتي المعلقة")
    
    pending_msg = await wait_for_message(seeker, ["المعلقة", "طلبات"], timeout=10)
    await click_inline_button(seeker, pending_msg, "سحب الطلب")
    await wait_for_message(seeker, ["تم سحب طلب الانضمام", "بنجاح", "سحب"], timeout=10)

async def test_team_join_and_accept(host, seeker):
    await clear_chat_history_view(host)
    team_menu = await open_team_menu(seeker)
    
    await click_inline_button(seeker, team_menu, "البحث عن فريق")
    find_msg = await wait_for_message(seeker, ["فريق #", "لا توجد فرق"], timeout=10)
    res = await click_inline_button(seeker, find_msg, "انضمام")
    if not res or not res.message or not any(w in res.message for w in ["تم إرسال طلب الانضمام", "بنجاح"]):
        raise Exception(f"Expected join success alert, got {res.message if res else 'None'}")
    
    join_alert = await wait_for_message(host, ["طلب انضمام"], timeout=15)
    await click_inline_button(host, join_alert, "قبول")
    
    await wait_for_message(host, ["تم قبول", "انضمام"], timeout=10)
    await wait_for_message(seeker, ["تم قبولك", "حساب المنشئ"], timeout=15)

async def test_host_close_team(host, seeker=None):
    team_menu = await open_team_menu(host)
    await click_inline_button(host, team_menu, "إنشاء فريق")
    await wait_for_message(host, ["المادة"], timeout=10)
    await host.send_message(BOT_USERNAME, "Close E2E Course")
    await wait_for_message(host, ["دكتور", "منسق"], timeout=10)
    await host.send_message(BOT_USERNAME, "Dr. Close")
    
    count_msg = await wait_for_message(host, ["عضو", "تحتاج"], timeout=10)
    await click_inline_button(host, count_msg, "2 أعضاء")
    await wait_for_message(host, ["تم إنشاء طلب الفريق"], timeout=15)
    
    team_menu2 = await open_team_menu(host)
    await click_inline_button(host, team_menu2, "فرقي المفتوحة")
    
    my_teams = await wait_for_message(host, ["إغلاق", "إدارة", "Close E2E"], timeout=10)
    await click_inline_button(host, my_teams, "إغلاق")
    await wait_for_message(host, ["تم إغلاق الفريق يدوياً", "أغلق"], timeout=10)

async def test_host_delete_team(host, seeker=None):
    team_menu = await open_team_menu(host)
    await click_inline_button(host, team_menu, "إنشاء فريق")
    await wait_for_message(host, ["المادة"], timeout=10)
    await host.send_message(BOT_USERNAME, "Delete E2E Course")
    await wait_for_message(host, ["دكتور", "منسق"], timeout=10)
    await host.send_message(BOT_USERNAME, "Dr. Delete")
    
    count_msg = await wait_for_message(host, ["عضو", "تحتاج"], timeout=10)
    await click_inline_button(host, count_msg, "2 أعضاء")
    await wait_for_message(host, ["تم إنشاء طلب الفريق"], timeout=15)
    
    team_menu2 = await open_team_menu(host)
    await click_inline_button(host, team_menu2, "فرقي المفتوحة")
    
    my_teams = await wait_for_message(host, ["حذف", "إدارة", "Delete E2E"], timeout=10)
    await click_inline_button(host, my_teams, "حذف")
    await wait_for_message(host, ["تم حذف الفريق"], timeout=10)

def get_tests():
    return {
        "Matchmaking: Create Team": test_team_creation,
        "Matchmaking: Concurrency": test_team_concurrency,
        "Matchmaking: Join & Withdraw": test_team_join_and_withdraw,
        "Matchmaking: Join & Accept": test_team_join_and_accept,
        "Matchmaking: Close Team": test_host_close_team,
        "Matchmaking: Delete Team": test_host_delete_team,
    }
