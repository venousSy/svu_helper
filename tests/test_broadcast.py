import pytest
from database import init_db, add_project, get_all_users, execute_query

TEST_DB = "test_broadcast.db"

@pytest.fixture(autouse=True)
def setup_db():
    init_db(db_path=TEST_DB)
    execute_query("DELETE FROM projects;", db_path=TEST_DB)
    execute_query("DELETE FROM sqlite_sequence WHERE name='projects';", db_path=TEST_DB)
    yield

def test_unique_user_broadcast_logic():
    # 1. Add multiple projects for the SAME user
    add_project(user_id=111, subject="Math", tutor="A", deadline="D", details="X", file_id=None, db_path=TEST_DB)
    add_project(user_id=111, subject="Physics", tutor="B", deadline="D", details="X", file_id=None, db_path=TEST_DB)
    
    # 2. Add a project for a DIFFERENT user
    add_project(user_id=222, subject="History", tutor="C", deadline="D", details="X", file_id=None, db_path=TEST_DB)
    
    # 3. Get broadcast list
    users = get_all_users(db_path=TEST_DB)
    
    # 4. Assert
    assert len(users) == 2  # Should be 2 users, not 3 projects
    assert 111 in users
    assert 222 in users