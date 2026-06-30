import asyncio
import os
import sys
import argparse
import traceback

from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from telethon.sessions import StringSession

# Add parent directory to sys.path to allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.mongo_db import init_db
from infrastructure.repositories.e2e_test_repo import E2ETestRepo

from tests.suites import (
    test_e2e_general,
    test_e2e_matchmaking,
    test_e2e_projects,
    test_e2e_tickets
)

S_API_ID   = os.getenv("TEST_API_ID")
S_API_HASH = os.getenv("TEST_API_HASH")
A_API_ID   = os.getenv("ADMIN_TEST_API_ID")
A_API_HASH = os.getenv("ADMIN_TEST_API_HASH")

SUITES = {
    "general": test_e2e_general.get_tests(),
    "matchmaking": test_e2e_matchmaking.get_tests(),
    "projects": test_e2e_projects.get_tests(),
    "tickets": test_e2e_tickets.get_tests(),
}

async def run_suite_tests(suite_name, tests, student, admin):
    print(f"\n[{'='*40}]\n[🚀 Running Suite: {suite_name}]\n[{'='*40}]")
    passed = []
    failed = []
    for test_name, coro_func in tests.items():
        print(f"\n[🎬 {test_name}]")
        try:
            if "Matchmaking" in test_name:
                # Matchmaking tests expect host, seeker. We use student as host, admin as seeker.
                await coro_func(host=student, seeker=admin)
            else:
                await coro_func(student=student, admin=admin)
            passed.append(test_name)
            print(f"  ✅ PASSED: {test_name}")
        except Exception as e:
            print(f"  ❌ FAILED: {test_name} - {e}")
            traceback.print_exc()
            failed.append(test_name)
            
    suite_result = "passed" if len(failed) == 0 else "failed"
    return suite_result, passed, failed

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--failed-only", action="store_true", help="Run only failed suites")
    args = parser.parse_args()

    await init_db()

    target_suites = list(SUITES.keys())
    if args.failed_only:
        last_results = await E2ETestRepo.get_last_test_run()
        if not last_results:
            print("No previous test results found. Running all suites.")
        else:
            target_suites = [s for s, res in last_results.items() if res == "failed" and s in SUITES]
            if not target_suites:
                print("All suites passed in the last run! Nothing to do.")
                sys.exit(0)
            print(f"Running only failed suites: {target_suites}")

    student_session_str = os.getenv("STUDENT_STRING_SESSION")
    admin_session_str = os.getenv("ADMIN_STRING_SESSION")

    if not student_session_str or not admin_session_str:
        print("⛔️ MISSING CREDENTIALS. Please check your .env file or Railway variables.")
        sys.exit(1)

    student_session = StringSession(student_session_str)
    admin_session = StringSession(admin_session_str)

    student = TelegramClient(student_session, S_API_ID, S_API_HASH)
    admin   = TelegramClient(admin_session,   A_API_ID, A_API_HASH)

    await student.start()
    await admin.start()
    print("✅ Both clients logged in successfully.\n")

    current_results = await E2ETestRepo.get_last_test_run() or {}
    
    overall_passed = 0
    overall_failed = 0

    for suite_name in target_suites:
        if suite_name == "matchmaking":
            from tests.suites.test_e2e_matchmaking import cleanup_user_state
            print("\n[🧹 Cleaning Matchmaking State]")
            await cleanup_user_state(student)
            await cleanup_user_state(admin)

        suite_tests = SUITES[suite_name]
        status, passed, failed = await run_suite_tests(suite_name, suite_tests, student, admin)
        
        overall_passed += len(passed)
        overall_failed += len(failed)
        current_results[suite_name] = status

    # Save to DB
    await E2ETestRepo.save_test_run(current_results)

    print("\n" + "=" * 50)
    print(f"📊 OVERALL RESULTS: {overall_passed} PASSED / {overall_failed} FAILED")
    print("=" * 50)

    await student.disconnect()
    await admin.disconnect()

    if overall_failed > 0:
        print(f"\n⚠️ {overall_failed} test(s) failed.")
        sys.exit(1)
    else:
        print("\n🏆 ALL TARGET TESTS PASSED! 🏆")
        sys.exit(0)

if __name__ == '__main__':
    asyncio.run(main())
