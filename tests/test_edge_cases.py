import pytest
from database import init_db, add_project, execute_query
from utils.formatters import format_student_projects

TEST_DB = "test_edges.db"

@pytest.fixture(autouse=True)
def setup_db():
    init_db(db_path=TEST_DB)
    execute_query("DELETE FROM projects;", db_path=TEST_DB)
    execute_query("DELETE FROM sqlite_sequence WHERE name='projects';", db_path=TEST_DB)
    yield

def test_project_with_empty_details():
    """Edge Case: Student submits a project but the details text is empty or None."""
    proj_id = add_project(777, "EmptyTest", "Tutor", "Date", None, None, db_path=TEST_DB)
    
    row = execute_query("SELECT details FROM projects WHERE id=?", (proj_id,), fetch_one=True, db_path=TEST_DB)
    # The DB should handle None gracefully
    assert row[0] is None or row[0] == ""

def test_extreme_character_input():
    """Edge Case: Student enters a massive string (SQL injection or spam attempt)."""
    long_string = "A" * 5000 
    proj_id = add_project(888, long_string, "Tutor", "Date", "Details", None, db_path=TEST_DB)
    
    row = execute_query("SELECT subject_name FROM projects WHERE id=?", (proj_id,), fetch_one=True, db_path=TEST_DB)
    assert len(row[0]) == 5000

def test_status_formatting_mismatch():
    """Edge Case: If the DB has a status we haven't defined emojis for."""
    mock_data = [(99, "Mystery Project", "UnknownStatus")]
    result = format_student_projects(mock_data)
    
    # It should fallback to the 'info' emoji we set in our formatter
    assert "ℹ️ UnknownStatus" in result