import pytest
from unittest.mock import AsyncMock, MagicMock
from infrastructure.repositories.student_repo import StudentRepository
from domain.entities import StudentProfile

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.students.find_one = AsyncMock()
    db.students.update_one = AsyncMock()
    return db

@pytest.mark.asyncio
async def test_get_profile(mock_db):
    repo = StudentRepository(mock_db)
    
    # Not found
    mock_db.students.find_one.return_value = None
    assert await repo.get_profile(1) is None
    
    # Found
    mock_db.students.find_one.return_value = {"user_id": 1, "specialization": "IT"}
    result = await repo.get_profile(1)
    assert isinstance(result, StudentProfile)
    assert result.user_id == 1
    assert result.specialization == "IT"

@pytest.mark.asyncio
async def test_create_profile(mock_db):
    repo = StudentRepository(mock_db)
    result = await repo.create_profile(1, "IT")
    assert isinstance(result, StudentProfile)
    assert result.user_id == 1
    assert result.specialization == "IT"
    mock_db.students.update_one.assert_called_once()
