import asyncio
import os
import sys

# Add the project root to the path
sys.path.append(os.getcwd())


async def test_extensions():
    print("Testing new extensions...")
    try:
        from keyboards.admin_kb import get_new_project_alert_kb

        print("[OK] get_new_project_alert_kb imported")

        # Simulate creating the keyboard
        kb = get_new_project_alert_kb(123)
        print("[OK] Keyboard generated successfully")

        return True
    except Exception as e:
        print(f"[FAIL] Extension test failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_extensions())
