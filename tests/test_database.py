"""
Unit tests for repository implementations.
==========================================
All tests use constructor-injected repositories (infrastructure.repositories)
with a fully mocked db object. There is NO mutation of Database.db globals.

Pattern:
    1. A `mock_db` fixture provides a clean AsyncMock database handle.
    2. A per-repo fixture builds the repository with that mock handle.
    3. Individual tests configure return values on mock_db and assert behaviour.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domain.enums import ProjectStatus
from infrastructure.repositories import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    PaymentRepository,
    ProjectRepository,
    SettingsRepository,
    StatsRepository,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """A fresh AsyncMock database handle. Shared within a test via repo fixtures."""
    db = AsyncMock()
    # Default sequence counter response used by add_project / add_payment
    db.counters.find_one_and_update.return_value = {"seq": 101}
    return db


@pytest.fixture
def project_repo(mock_db):
    return ProjectRepository(mock_db)


@pytest.fixture
def payment_repo(mock_db):
    return PaymentRepository(mock_db)


@pytest.fixture
def settings_repo(mock_db):
    return SettingsRepository(mock_db)


@pytest.fixture
def stats_repo(mock_db):
    return StatsRepository(mock_db)


# ---------------------------------------------------------------------------
# ProjectRepository tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_project(project_repo, mock_db):
    with patch(
        "infrastructure.repositories.Database.get_next_sequence",
        new=AsyncMock(return_value=101),
    ):
        project_id = await project_repo.add_project(
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
    mock_db.projects.insert_one.assert_called_once()
    inserted_doc = mock_db.projects.insert_one.call_args[0][0]
    assert inserted_doc["id"] == 101
    assert inserted_doc["subject_name"] == "Math"
    assert inserted_doc["status"] == ProjectStatus.PENDING


@pytest.mark.asyncio
async def test_get_project_by_id_found(project_repo, mock_db):
    mock_project = {"id": 101, "subject_name": "Math"}
    mock_db.projects.find_one.return_value = mock_project

    result = await project_repo.get_project_by_id(101)

    assert result == mock_project
    mock_db.projects.find_one.assert_called_with({"id": 101})


@pytest.mark.asyncio
async def test_get_project_by_id_not_found(project_repo, mock_db):
    mock_db.projects.find_one.return_value = None

    result = await project_repo.get_project_by_id(999)

    assert result is None


@pytest.mark.asyncio
async def test_update_status(project_repo, mock_db):
    await project_repo.update_status(42, ProjectStatus.ACCEPTED)

    mock_db.projects.update_one.assert_called_once_with(
        {"id": 42},
        {"$set": {"status": ProjectStatus.ACCEPTED}},
    )


@pytest.mark.asyncio
async def test_get_projects_by_status(project_repo, mock_db):
    mock_projects = [{"id": 1}, {"id": 2}]
    # Cursor is a plain MagicMock so .skip() and .limit() can chain synchronously,
    # while .to_list() is awaitable.
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=mock_projects)
    mock_db.projects.find = MagicMock(return_value=mock_cursor)

    result = await project_repo.get_projects_by_status(
        [ProjectStatus.PENDING], user_id=10
    )

    assert result == mock_projects
    mock_db.projects.find.assert_called_once_with(
        {"status": {"$in": [ProjectStatus.PENDING]}, "user_id": 10}
    )
    mock_cursor.skip.assert_called_once_with(0)
    mock_cursor.limit.assert_called_once_with(DEFAULT_PAGE_SIZE)


@pytest.mark.asyncio
async def test_get_projects_by_status_custom_pagination(project_repo, mock_db):
    """Custom limit/skip values are forwarded to the cursor."""
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[])
    mock_db.projects.find = MagicMock(return_value=mock_cursor)

    await project_repo.get_projects_by_status(
        [ProjectStatus.PENDING], limit=25, skip=50
    )

    mock_cursor.skip.assert_called_once_with(50)
    mock_cursor.limit.assert_called_once_with(25)


@pytest.mark.asyncio
async def test_get_projects_by_status_max_page_size_cap(project_repo, mock_db):
    """Requests exceeding MAX_PAGE_SIZE are capped silently."""
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[])
    mock_db.projects.find = MagicMock(return_value=mock_cursor)

    await project_repo.get_projects_by_status(
        [ProjectStatus.PENDING], limit=99_999
    )

    # The cursor must receive MAX_PAGE_SIZE, not the caller's huge value.
    mock_cursor.limit.assert_called_once_with(MAX_PAGE_SIZE)


@pytest.mark.asyncio
async def test_get_all_user_ids(project_repo, mock_db):
    mock_db.projects.distinct.return_value = [1, 2, 3]

    result = await project_repo.get_all_user_ids()

    assert result == [1, 2, 3]
    mock_db.projects.distinct.assert_called_once_with("user_id")


# ---------------------------------------------------------------------------
# PaymentRepository tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_payment(payment_repo, mock_db):
    with patch(
        "infrastructure.repositories.Database.get_next_sequence",
        new=AsyncMock(return_value=101),
    ):
        payment_id = await payment_repo.add_payment(
            project_id=42, user_id=7, file_id="f_abc"
        )

    assert payment_id == 101
    mock_db.payments.insert_one.assert_called_once()
    inserted_doc = mock_db.payments.insert_one.call_args[0][0]
    assert inserted_doc["id"] == 101
    assert inserted_doc["project_id"] == 42


@pytest.mark.asyncio
async def test_get_payment_found(payment_repo, mock_db):
    mock_payment = {"id": 101, "project_id": 42}
    mock_db.payments.find_one.return_value = mock_payment

    result = await payment_repo.get_payment(101)

    assert result == mock_payment


@pytest.mark.asyncio
async def test_get_payment_not_found(payment_repo, mock_db):
    mock_db.payments.find_one.return_value = None

    result = await payment_repo.get_payment(999)

    assert result is None


@pytest.mark.asyncio
async def test_payment_get_all_uses_pagination(payment_repo, mock_db):
    """get_all() must use skip/limit and not load an unbounded cursor."""
    mock_payments = [{"id": 5}, {"id": 4}]
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=mock_payments)
    mock_db.payments.find = MagicMock(return_value=mock_cursor)

    result = await payment_repo.get_all()

    assert result == mock_payments
    mock_cursor.sort.assert_called_once_with("id", -1)
    mock_cursor.skip.assert_called_once_with(0)
    mock_cursor.limit.assert_called_once_with(DEFAULT_PAGE_SIZE)


# ---------------------------------------------------------------------------
# SettingsRepository tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_maintenance_mode_true(settings_repo, mock_db):
    mock_db.settings.find_one.return_value = {"maintenance_mode": True}

    result = await settings_repo.get_maintenance_mode()

    assert result is True


@pytest.mark.asyncio
async def test_get_maintenance_mode_missing_doc(settings_repo, mock_db):
    mock_db.settings.find_one.return_value = None

    result = await settings_repo.get_maintenance_mode()

    assert result is False


@pytest.mark.asyncio
async def test_set_maintenance_mode(settings_repo, mock_db):
    await settings_repo.set_maintenance_mode(True)

    mock_db.settings.update_one.assert_called_once_with(
        {"_id": "global_config"},
        {"$set": {"maintenance_mode": True}},
        upsert=True,
    )
