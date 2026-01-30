import os
import sys

sys.path.append(os.getcwd())
from database import (
    add_project,
    get_db_connection,
    get_pending_projects,
    get_user_projects,
    init_db,
)


def verify_db():
    print("Initializing DB...")
    # Use a test DB file to avoid messing with the real one, or just check the real one if we want to confirm migration
    db_path = "bot_requests.db"

    # Check if DB exists
    if not os.path.exists(db_path):
        print("DB file not found. Initializing...")
        init_db(db_path)

    print("Checking Schema...")
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(projects)")
        columns = {row["name"]: row["type"] for row in cursor.fetchall()}

    required = {"username": "TEXT", "user_full_name": "TEXT"}
    missing = []
    for col, type_ in required.items():
        if col not in columns:
            missing.append(col)
        else:
            print(f"Column '{col}' exists.")

    if missing:
        print(f"Missing columns: {missing}")
        return

    print("Testing Insertion...")
    try:
        pid = add_project(
            12345678,
            "test_user",
            "Test User",
            "Math",
            "TutorA",
            "Tomorrow",
            "Details",
            "file_id_123",
            db_path=db_path,
        )
        print(f"Inserted Project #{pid}")
    except Exception as e:
        print(f"Insertion Failed: {e}")
        return

    print("Testing Retrieval...")
    pending = get_pending_projects(db_path=db_path)
    found = False
    for p in pending:
        if p["id"] == pid:
            print(f"Found in Pending: {p}")
            if "username" in p and p["username"] == "test_user":
                print("Username verified in retrieval.")
                found = True
            else:
                print(f"Username missing or incorrect in retrieval: {p}")

    if not found:
        print("Project not found in pending list.")


if __name__ == "__main__":
    verify_db()
