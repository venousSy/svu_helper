import pytest
from database import init_db, add_project, update_project_status, get_user_projects, execute_query

TEST_DB = "test_journey_full.db"

@pytest.fixture(autouse=True)
def setup_db():
    init_db(db_path=TEST_DB)
    # Clear data before each test case
    execute_query("DELETE FROM projects;", db_path=TEST_DB)
    execute_query("DELETE FROM sqlite_sequence WHERE name='projects';", db_path=TEST_DB)
    yield

def test_path_successful_completion():
    """Path: Submit -> Offer -> Pay -> Verify -> Finish"""
    uid = 101
    pid = add_project(uid, "Math", "Tutor", "Date", "Notes", None, db_path=TEST_DB)
    
    # 1. Admin sends offer, student accepts (moves to verification)
    update_project_status(pid, "Awaiting Verification", db_path=TEST_DB)
    
    # 2. Admin confirms payment
    update_project_status(pid, "Accepted", db_path=TEST_DB)
    
    # 3. Admin finishes work
    update_project_status(pid, "Finished", db_path=TEST_DB)
    
    status = get_user_projects(uid, db_path=TEST_DB)[0][2]
    assert status == "Finished"

def test_path_payment_rejection():
    """Path: Submit -> Offer -> Pay -> Admin REJECTS receipt"""
    uid = 102
    pid = add_project(uid, "Physics", "Tutor", "Date", "Notes", None, db_path=TEST_DB)
    
    # Student sends proof
    update_project_status(pid, "Awaiting Verification", db_path=TEST_DB)
    
    # Admin says "This receipt is fake/blurry"
    update_project_status(pid, "Rejected: Payment Issue", db_path=TEST_DB)
    
    status = get_user_projects(uid, db_path=TEST_DB)[0][2]
    assert "Payment Issue" in status

def test_path_admin_initial_rejection():
    """Path: Submit -> Admin REJECTS immediately (No offer)"""
    uid = 103
    pid = add_project(uid, "History", "Tutor", "Date", "Notes", None, db_path=TEST_DB)
    
    update_project_status(pid, "Denied: Admin Rejected", db_path=TEST_DB)
    
    status = get_user_projects(uid, db_path=TEST_DB)[0][2]
    assert "Admin Rejected" in status

def test_path_student_cancels():
    """Path: Submit -> Offer -> Student REJECTS offer"""
    uid = 104
    pid = add_project(uid, "Bio", "Tutor", "Date", "Notes", None, db_path=TEST_DB)
    
    update_project_status(pid, "Denied: Student Cancelled", db_path=TEST_DB)
    
    status = get_user_projects(uid, db_path=TEST_DB)[0][2]
    assert "Student Cancelled" in status