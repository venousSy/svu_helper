import pytest
from database import init_db, add_project, update_project_status, get_all_projects_categorized

TEST_DB = "test_admin.db"

@pytest.fixture(autouse=True)
def setup_db():
    init_db(db_path=TEST_DB)
    # Start with a clean slate
    from database import execute_query
    execute_query("DELETE FROM projects;", db_path=TEST_DB)
    yield

def test_admin_list_segregation():
    """Ensures that projects are correctly binned into dictionary keys."""
    # Setup: Create dummy data
    add_project(1, "Math", "Tutor", "Date", "Notes", None, db_path=TEST_DB)
    p2 = add_project(2, "History", "Tutor", "Date", "Notes", None, db_path=TEST_DB)
    update_project_status(p2, "Finished", db_path=TEST_DB)

    # This call now returns a dictionary!
    categorized = get_all_projects_categorized(db_path=TEST_DB)

    # These assertions will now PASS because categorized is a dict
    assert len(categorized["New / Pending"]) == 1
    assert len(categorized["History"]) == 1
    assert categorized["New / Pending"][0][1] == "Math"
    assert categorized["History"][0][1] == "History"
def test_status_update_persistence():
    """Ensures that when an admin clicks 'Accept', the change is permanent in the DB."""
    p_id = add_project(999, "Physics", "Tutor", "Date", "Notes", None, db_path=TEST_DB)
    
    update_project_status(p_id, "Accepted", db_path=TEST_DB)
    
    # Fetch directly from DB to verify
    from database import execute_query
    res = execute_query("SELECT status FROM projects WHERE id = ?", (p_id,), fetch_one=True, db_path=TEST_DB)
    assert res[0] == "Accepted"