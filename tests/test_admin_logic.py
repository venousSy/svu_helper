import pytest
from database import execute_query, update_project_status

def test_database_connection():
    # Test if we can at least perform a simple selection
    result = execute_query("SELECT 1", fetch_one=True)
    assert result[0] == 1

def test_status_update():
    # 1. Create a dummy project (or use an existing test ID)
    # 2. Update status
    update_project_status(1, "TestingStatus")
    
    # 3. Verify
    res = execute_query("SELECT status FROM projects WHERE id = 1", fetch_one=True)
    assert res[0] == "TestingStatus"