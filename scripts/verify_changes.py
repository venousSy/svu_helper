import asyncio
import os
import sys

# Add the project root to the path
sys.path.append(os.getcwd())


async def test_imports():
    print("Testing imports...")
    try:
        from utils.constants import MSG_WELCOME

        print("[OK] utils.constants imported")

        from keyboards.common_kb import get_student_main_kb

        print("[OK] keyboards.common_kb imported")

        from database import init_db

        print("[OK] database imported")

        from handlers.common import router as common_router

        print("[OK] handlers.common imported")

        from handlers.admin import router as admin_router

        print("[OK] handlers.admin imported")

        from handlers.client import router as client_router

        print("[OK] handlers.client imported")

        print("All imports successful.")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False


async def main():
    if await test_imports():
        print("\nVerification passed!")
    else:
        print("\nVerification failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
