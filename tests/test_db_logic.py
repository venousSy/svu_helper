import pytest
import os
from database import init_db, add_project, get_all_projects_categorized, execute_query

TEST_DB = "test_bot.db"

@pytest.fixture(autouse=True)
def setup_teardown():
    # 1. Ensure DB exists
    init_db(db_path=TEST_DB)
    
    # 2. FORCE WIPE THE DATA (The Fix)
    # Instead of deleting the file, we just delete all rows.
    # This avoids Windows "PermissionError" completely.
    execute_query("DELETE FROM projects;", db_path=TEST_DB)
    
    # 3. Start the test
    yield 

def test_add_and_get_project():
    add_project(123, "Math", "Dr. Smith", "2026-01-01", "Details", None, db_path=TEST_DB)
    projects_dict = get_all_projects_categorized(db_path=TEST_DB)

    # Check the length of the 'Pending' list specifically
    assert len(projects_dict["Pending"]) == 1
def test_empty_db_logic():
    projects_dict = get_all_projects_categorized(db_path=TEST_DB)
    # Check that all categories are empty
    assert len(projects_dict["Pending"]) == 0
    assert len(projects_dict["Ongoing"]) == 0
    assert len(projects_dict["History"]) == 0