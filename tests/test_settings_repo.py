import pytest
from unittest.mock import AsyncMock, MagicMock
from infrastructure.repositories.settings import SettingsRepository

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.settings.find_one = AsyncMock()
    db.settings.update_one = AsyncMock()
    return db

@pytest.mark.asyncio
async def test_get_maintenance_mode(mock_db):
    repo = SettingsRepository(mock_db)
    
    # None document
    mock_db.settings.find_one.return_value = None
    assert await repo.get_maintenance_mode() is False
    
    # False
    mock_db.settings.find_one.return_value = {"maintenance_mode": False}
    assert await repo.get_maintenance_mode() is False
    
    # True
    mock_db.settings.find_one.return_value = {"maintenance_mode": True}
    assert await repo.get_maintenance_mode() is True

@pytest.mark.asyncio
async def test_set_maintenance_mode(mock_db):
    repo = SettingsRepository(mock_db)
    await repo.set_maintenance_mode(True)
    mock_db.settings.update_one.assert_called_with(
        {"_id": "global_config"},
        {"$set": {"maintenance_mode": True}},
        upsert=True,
    )
