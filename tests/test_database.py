from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from database.connection import Database
from database.repositories import ProjectRepository
from utils.enums import ProjectStatus

@pytest.mark.asyncio
async def test_add_project():
    # Mock the database connection and collection
    mock_db = AsyncMock()
    mock_collection = AsyncMock()
    mock_db.projects = mock_collection

    # Mock the counters collection for get_next_sequence
    mock_db.counters.find_one_and_update.return_value = {"seq": 101}

    # Patch the get_db function or Database.db directly
    # Since Repositories access Database.db directly
    Database.db = mock_db

    project_id = await ProjectRepository.add_project(
        user_id=1,
        username="testuser",
        user_full_name="Test User",
        subject="Math",
        tutor="Dr. X",
        deadline="2024-01-01",
        details="Details",
        file_id="file_123",
        file_type="document",
    )

    assert project_id == 101
    mock_collection.insert_one.assert_called_once()
    call_args = mock_collection.insert_one.call_args[0][0]
    assert call_args["id"] == 101
    assert call_args["subject_name"] == "Math"
    assert call_args["status"] == ProjectStatus.PENDING


@pytest.mark.asyncio
async def test_get_project_by_id():
    mock_db = AsyncMock()
    mock_collection = AsyncMock()
    mock_db.projects = mock_collection

    mock_project = {"id": 101, "subject_name": "Math"}
    mock_collection.find_one.return_value = mock_project

    mock_collection.find_one.return_value = mock_project

    Database.db = mock_db  # Ensure class var is set
    result = await ProjectRepository.get_project_by_id(101)

    assert result == mock_project
    mock_collection.find_one.assert_called_with({"id": 101})


@pytest.mark.asyncio
async def test_get_project_by_id_none():
    mock_db = AsyncMock()
    mock_collection = AsyncMock()
    mock_db.projects = mock_collection

    mock_collection.find_one.return_value = None

    mock_collection.find_one.return_value = None

    Database.db = mock_db
    result = await ProjectRepository.get_project_by_id(999)

    assert result is None
