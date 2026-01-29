import pytest
from unittest.mock import patch, AsyncMock
from ticktick.sdk import tasks

@pytest.fixture
def mock_client():
    with patch("ticktick.sdk.tasks.client") as mock:
        yield mock

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
async def test_create_task_all_fields(mock_client):
    """Test creating a task with all new fields."""
    mock_client.post = AsyncMock(return_value={"id": "t1"})
    
    await tasks.create_task(
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
async def test_delete_task_disabled(mock_config, mock_client):
    """Test delete fails when disabled in settings."""
    mock_config.return_value = "disabled"
    mock_client.delete = AsyncMock()
    
    result = await tasks.delete_task("p1", "t1")
    assert result["success"] is False
    assert "disabled" in result["error"]
    mock_client.delete.assert_not_called()

@pytest.mark.asyncio
async def test_delete_task_elevated_no_otp(mock_config, mock_client):
    """Test delete fails when elevated but no OTP provided."""
    mock_config.return_value = "elevated"
    mock_client.delete = AsyncMock()
    
    result = await tasks.delete_task("p1", "t1", elevated=True, otp=None)
    assert result["success"] is False
    assert "OTP required" in result["error"]

@pytest.mark.asyncio
async def test_delete_task_elevated_invalid_otp(mock_config, mock_security, mock_client):
    """Test delete fails with invalid OTP."""
    mock_config.return_value = "elevated"
    mock_security.return_value = False
    mock_client.delete = AsyncMock()
    
    result = await tasks.delete_task("p1", "t1", elevated=True, otp="BAD")
    assert result["success"] is False
    assert "Invalid or expired" in result["error"]

@pytest.mark.asyncio
async def test_delete_task_success_archived(mock_config, mock_client, mock_archiver):
    """Test successful delete with auto-archive."""
    # Settings: enabled (no OTP), auto-archive ON (default)
    mock_config.side_effect = lambda k: {
        "deletion.access": "enabled",
        "deletion.disable_auto_archive": False,
        "deletion.archive": None
    }.get(k)
    
    mock_client.delete = AsyncMock(return_value={})
    
    # We must patch get_task in tasks module because it's called by delete_task
    with patch("ticktick.sdk.tasks.get_task", new_callable=AsyncMock) as mock_get_task:
        mock_get_task.return_value = {"id": "t1", "title": "To Delete"}
        
        result = await tasks.delete_task("p1", "t1")
        
        assert result["success"] is True
        mock_archiver.assert_called_once()
        mock_client.delete.assert_called_once()

@pytest.mark.asyncio
async def test_delete_task_success_no_archive(mock_config, mock_client, mock_archiver):
    """Test delete with auto-archive disabled."""
    mock_config.side_effect = lambda k: {
        "deletion.access": "enabled",
        "deletion.disable_auto_archive": True
    }.get(k)
    
    mock_client.delete = AsyncMock(return_value={})
    
    result = await tasks.delete_task("p1", "t1")
    
    assert result["success"] is True
    mock_archiver.assert_not_called()
    mock_client.delete.assert_called_once()