import pytest
from database import (
    init_db, 
    add_project, 
    update_project_status, 
    get_pending_projects, 
    get_all_projects_categorized,
    execute_query
)

TEST_DB = "test_features.db"

@pytest.fixture(autouse=True)
def setup_db():
    init_db(db_path=TEST_DB)
    # Wiping data and resetting the autoincrement counter
    execute_query("DELETE FROM projects;", db_path=TEST_DB)
    execute_query("DELETE FROM sqlite_sequence WHERE name='projects';", db_path=TEST_DB)
    yield

def test_pending_filter_logic():
    # Capture the ID returned by add_project
    id1 = add_project(1, "Math", "Tutor A", "Date", "Details", "file1", db_path=TEST_DB)
    id2 = add_project(2, "History", "Tutor B", "Date", "Details", "file2", db_path=TEST_DB)

    # Use the dynamic ID
    update_project_status(id2, "Accepted", db_path=TEST_DB)

    pending_list = get_pending_projects(db_path=TEST_DB)
    
    assert len(pending_list) == 1
    assert pending_list[0][1] == "Math"

def test_project_lifecycle():
    proj_id = add_project(10, "Physics", "Dr. X", "Date", "Notes", "File", db_path=TEST_DB)

    # 2. Update and verify using dynamic ID
    update_project_status(proj_id, "Awaiting Verification", db_path=TEST_DB)
    row = execute_query("SELECT status FROM projects WHERE id=?", (proj_id,), fetch_one=True, db_path=TEST_DB)
    assert row[0] == "Awaiting Verification"
    
    update_project_status(proj_id, "Accepted", db_path=TEST_DB)
    row = execute_query("SELECT status FROM projects WHERE id=?", (proj_id,), fetch_one=True, db_path=TEST_DB)
    assert row[0] == "Accepted"

def test_rejection_reasons():
    proj_id = add_project(99, "Bad Project", "Tutor Z", "Date", "Notes", "File", db_path=TEST_DB)
    
    update_project_status(proj_id, "Rejected: Payment Issue", db_path=TEST_DB)
    
    all_projects = get_all_projects_categorized(db_path=TEST_DB)
    
    # Find the specific project in the list
    project_entry = next(p for p in all_projects if p[0] == proj_id)
    assert "Payment Issue" in project_entry[2]