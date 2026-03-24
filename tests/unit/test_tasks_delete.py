import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from ticktick.sdk.client import TickTickClient
from ticktick.sdk.tasks import TaskService


@pytest.fixture
def mock_client():
    client = MagicMock(spec=TickTickClient)
    return client


@pytest.fixture
def task_svc(mock_client):
    return TaskService(mock_client)


@pytest.fixture
def mock_config():
    with patch("ticktick.config.get_setting") as mock:
        yield mock


@pytest.fixture
def mock_security():
    with patch("ticktick.sdk.security.validate_otp") as mock:
        yield mock


@pytest.fixture
def mock_archiver():
    with patch("ticktick.sdk.archiver.archive_deleted_task") as mock:
        yield mock


@pytest.mark.asyncio
async def test_create_task_all_fields(mock_client, task_svc):
    """Test creating a task with all new fields."""
    mock_client.post = AsyncMock(return_value={"id": "t1"})

    await task_svc.create(
        "p1", "Title", content="Desc", priority=5,
        due_date="2025-01-01", reminders=["TRIGGER:PT0S"],
        status=2, completed_time="2025-01-01T10:00:00Z"
    )

    args = mock_client.post.call_args[0]
    payload = args[1]

    assert payload["reminders"] == ["TRIGGER:PT0S"]
    assert payload["completedTime"] == "2025-01-01T10:00:00Z"
    assert payload["status"] == 2


@pytest.mark.asyncio
async def test_delete_task_disabled(mock_config, task_svc):
    """Test delete fails when disabled in settings."""
    mock_config.return_value = "disabled"

    result = await task_svc.delete("p1", "t1")
    assert result["success"] is False
    assert "disabled" in result["error"]


@pytest.mark.asyncio
async def test_delete_task_elevated_no_otp(mock_config, task_svc):
    """Test delete fails when elevated but no OTP provided."""
    mock_config.return_value = "elevated"

    result = await task_svc.delete("p1", "t1", elevated=True, otp=None)
    assert result["success"] is False
    assert "OTP required" in result["error"]


@pytest.mark.asyncio
async def test_delete_task_elevated_invalid_otp(mock_config, mock_security, task_svc):
    """Test delete fails with invalid OTP."""
    mock_config.return_value = "elevated"
    mock_security.return_value = False

    result = await task_svc.delete("p1", "t1", elevated=True, otp="BAD")
    assert result["success"] is False
    assert "Invalid or expired" in result["error"]


@pytest.mark.asyncio
async def test_delete_task_success_archived(mock_config, mock_client, task_svc, mock_archiver):
    """Test successful delete with auto-archive."""
    mock_config.side_effect = lambda k: {
        "deletion.access": "enabled",
        "deletion.disable_auto_archive": False,
        "deletion.archive": None
    }.get(k)

    mock_client.get = AsyncMock(return_value={"id": "t1", "title": "To Delete"})
    mock_client.delete = AsyncMock(return_value={})

    result = await task_svc.delete("p1", "t1")

    assert result["success"] is True
    mock_archiver.assert_called_once()
    mock_client.delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_task_success_no_archive(mock_config, mock_client, task_svc, mock_archiver):
    """Test delete with auto-archive disabled."""
    mock_config.side_effect = lambda k: {
        "deletion.access": "enabled",
        "deletion.disable_auto_archive": True
    }.get(k)

    mock_client.delete = AsyncMock(return_value={})

    result = await task_svc.delete("p1", "t1")

    assert result["success"] is True
    mock_archiver.assert_not_called()
    mock_client.delete.assert_called_once()
