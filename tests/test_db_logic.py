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
    
    projects = get_all_projects_categorized(db_path=TEST_DB)
    
    assert len(projects) == 1
    assert projects[0][1] == "Math"

def test_empty_db_logic():
    # The fixture has already run "DELETE FROM projects", so this is guaranteed empty
    projects = get_all_projects_categorized(db_path=TEST_DB)
    assert len(projects) == 0