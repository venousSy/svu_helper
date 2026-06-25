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


async def open_team_menu(client):
    """Navigates to Team Matchmaking menu, handling specialization selection if prompted."""
    await client.send_message(BOT_USERNAME, "/start")
    await asyncio.sleep(1)
    start_msg = (await client.get_messages(BOT_USERNAME, limit=1))[0]
    await click_inline_button(client, start_msg, "فريق العمل")
    
    # Wait for either Team Menu or Specialization
    msg = await wait_for_message(client, ["إنشاء فريق", "اختصاص", "اختصاصك", "البحث عن فريق"], timeout=10)
    if "اختصاص" in msg.text:
        # Click the first specialization
        if msg.reply_markup and hasattr(msg.reply_markup, 'rows'):
            first_btn = msg.reply_markup.rows[0].buttons[0]
            await msg.click(data=first_btn.data)
            await asyncio.sleep(2)
        msg = await wait_for_message(client, ["إنشاء فريق", "البحث عن فريق"], timeout=10)
    return msg

async def clear_chat_history_view(client):
    """Sends dummy commands to push old messages down out of the limit=3 scope."""
    for _ in range(3):
        await client.send_message(BOT_USERNAME, "/help")
        await asyncio.sleep(0.5)


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
# MATCHMAKING TESTS
# ============================================================

async def test_team_creation(host):
    team_menu = await open_team_menu(host)
    
    await click_inline_button(host, team_menu, "إنشاء فريق")
    await wait_for_message(host, ["المادة"], timeout=10)
    
    await host.send_message(BOT_USERNAME, "E2E Matchmaking Course")
    await wait_for_message(host, ["المدرس"], timeout=10)
    
    await host.send_message(BOT_USERNAME, "Dr. E2E")
    
    count_msg = await wait_for_message(host, ["العدد المطلوب", "طلاب"], timeout=10)
    await click_inline_button(host, count_msg, "2 طلاب")
    
    await wait_for_message(host, ["تم إنشاء طلب الفريق", "بنجاح"], timeout=15)
    print("  ✅ Team creation flow completed.")


async def test_team_concurrency(host):
    team_menu = await open_team_menu(host)
    
    await click_inline_button(host, team_menu, "إنشاء فريق")
    await wait_for_message(host, ["المادة"], timeout=10)
    
    await host.send_message(BOT_USERNAME, "E2E Matchmaking Course")
    await wait_for_message(host, ["المدرس"], timeout=10)
    
    await host.send_message(BOT_USERNAME, "Dr. E2E")
    count_msg = await wait_for_message(host, ["العدد المطلوب", "طلاب"], timeout=10)
    await click_inline_button(host, count_msg, "2 طلاب")
    
    await wait_for_message(host, ["يوجد فريق مفتوح مسبقاً", "عذراً"], timeout=10)
    print("  ✅ Concurrency prevention works for hosts.")


async def test_team_join_and_withdraw(seeker, host):
    await clear_chat_history_view(host)
    team_menu = await open_team_menu(seeker)
    
    await click_inline_button(seeker, team_menu, "البحث عن فريق")
    
    find_msg = await wait_for_message(seeker, ["انضمام", "لا توجد فرق"], timeout=10)
    if "لا توجد فرق" in find_msg.text:
        raise Exception("No teams found for joining, but one should exist.")
        
    await click_inline_button(seeker, find_msg, "انضمام")
    await wait_for_message(seeker, ["تم إرسال طلب الانضمام", "بنجاح"], timeout=10)
    print("  ✅ Join request sent.")
    
    await wait_for_message(host, ["طلب انضمام"], timeout=15)
    print("  ✅ Host received join request alert.")
    
    team_menu2 = await open_team_menu(seeker)
    await click_inline_button(seeker, team_menu2, "طلبات الانضمام المعلقة")
    
    pending_msg = await wait_for_message(seeker, ["سحب الطلب", "معلقة"], timeout=10)
    await click_inline_button(seeker, pending_msg, "سحب الطلب")
    
    await wait_for_message(seeker, ["تم سحب طلب الانضمام", "بنجاح", "سحب"], timeout=10)
    print("  ✅ Join request withdrawn.")


async def test_team_join_and_accept(seeker, host):
    await clear_chat_history_view(host)
    team_menu = await open_team_menu(seeker)
    
    await click_inline_button(seeker, team_menu, "البحث عن فريق")
    find_msg = await wait_for_message(seeker, ["انضمام"], timeout=10)
    await click_inline_button(seeker, find_msg, "انضمام")
    await wait_for_message(seeker, ["تم إرسال طلب الانضمام"], timeout=10)
    print("  ✅ Join request sent again.")
    
    join_alert = await wait_for_message(host, ["طلب انضمام"], timeout=15)
    await click_inline_button(host, join_alert, "قبول")
    
    await wait_for_message(host, ["تم قبول", "انضمام"], timeout=10)
    print("  ✅ Host accepted join request.")
    
    await wait_for_message(seeker, ["تم قبول طلبك", "أصبحت عضواً"], timeout=15)
    print("  ✅ Seeker notified of acceptance.")


async def test_host_close_team(host):
    team_menu = await open_team_menu(host)
    
    await click_inline_button(host, team_menu, "إنشاء فريق")
    await wait_for_message(host, ["المادة"], timeout=10)
    await host.send_message(BOT_USERNAME, "Close E2E Course")
    await wait_for_message(host, ["المدرس"], timeout=10)
    await host.send_message(BOT_USERNAME, "Dr. Close")
    
    count_msg = await wait_for_message(host, ["العدد المطلوب", "طلاب"], timeout=10)
    await click_inline_button(host, count_msg, "2 طلاب")
    await wait_for_message(host, ["تم إنشاء طلب الفريق"], timeout=15)
    
    team_menu2 = await open_team_menu(host)
    await click_inline_button(host, team_menu2, "فرقي المفتوحة")
    
    my_teams = await wait_for_message(host, ["إغلاق", "إدارة", "Close E2E"], timeout=10)
    await click_inline_button(host, my_teams, "إغلاق")
    await wait_for_message(host, ["تم إغلاق الفريق يدوياً", "أغلق"], timeout=10)
    print("  ✅ Team closed manually by host.")


async def test_host_delete_team(host):
    team_menu = await open_team_menu(host)
    
    await click_inline_button(host, team_menu, "إنشاء فريق")
    await wait_for_message(host, ["المادة"], timeout=10)
    await host.send_message(BOT_USERNAME, "Delete E2E Course")
    await wait_for_message(host, ["المدرس"], timeout=10)
    await host.send_message(BOT_USERNAME, "Dr. Delete")
    
    count_msg = await wait_for_message(host, ["العدد المطلوب", "طلاب"], timeout=10)
    await click_inline_button(host, count_msg, "2 طلاب")
    await wait_for_message(host, ["تم إنشاء طلب الفريق"], timeout=15)
    
    team_menu2 = await open_team_menu(host)
    await click_inline_button(host, team_menu2, "فرقي المفتوحة")
    
    my_teams = await wait_for_message(host, ["حذف", "إدارة", "Delete E2E"], timeout=10)
    await click_inline_button(host, my_teams, "حذف")
    await wait_for_message(host, ["تم حذف الفريق"], timeout=10)
    print("  ✅ Team deleted manually by host.")


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

async def run_matchmaking_suite():
    print("🚀 Initializing E2E Matchmaking Test Suite...")

    # For matchmaking, both clients act as students interacting with the bot
    # We will use 'student' as host and 'admin' as seeker
    host   = TelegramClient('student_session', S_API_ID, S_API_HASH)
    seeker = TelegramClient('admin_session',   A_API_ID, A_API_HASH)

    await host.start()
    await seeker.start()
    print("✅ Both clients logged in successfully.\n")

    await run_test("TEST 1: Create Team",
                   test_team_creation(host))

    await run_test("TEST 2: Prevent Concurrent Same-Course Team Creation",
                   test_team_concurrency(host))

    await run_test("TEST 3: Join Team & Withdraw Request",
                   test_team_join_and_withdraw(seeker, host))

    await run_test("TEST 4: Join Team & Host Accepts",
                   test_team_join_and_accept(seeker, host))

    await run_test("TEST 5: Host Closes Open Team",
                   test_host_close_team(host))

    await run_test("TEST 6: Host Deletes Open Team",
                   test_host_delete_team(host))

    # --- RESULTS ---
    print("\n" + "=" * 50)
    print(f"📊 RESULTS: {len(PASSED)} PASSED / {len(FAILED)} FAILED")
    print("=" * 50)
    for t in PASSED:
        print(f"  ✅ {t}")
    for t in FAILED:
        print(f"  ❌ {t}")

    if not FAILED:
        print("\n🏆 ALL MATCHMAKING TESTS PASSED! 🏆")
    else:
        print(f"\n⚠️ {len(FAILED)} test(s) failed. Review output above.")

    await host.disconnect()
    await seeker.disconnect()


if __name__ == '__main__':
    asyncio.run(run_matchmaking_suite())
