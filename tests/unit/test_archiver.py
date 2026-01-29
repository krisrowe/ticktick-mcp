import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from ticktick.sdk import archiver

@pytest.fixture
def mock_env_cache():
    with patch.dict(os.environ, {"XDG_CACHE_HOME": "/tmp/custom_cache"}):
        yield

def test_get_cache_dir_custom(mock_env_cache):
    """Test get_cache_dir uses XDG_CACHE_HOME."""
    path = archiver.get_cache_dir()
    assert path == Path("/tmp/custom_cache/ticktick-access")

def test_get_cache_dir_default():
    """Test get_cache_dir uses ~/.cache by default."""
    with patch.dict(os.environ, {}, clear=True):
        with patch.object(Path, "home", return_value=Path("/home/user")):
            with patch("pathlib.Path.mkdir"):
                path = archiver.get_cache_dir()
                assert path == Path("/home/user/.cache/ticktick-access")

def test_archive_deleted_task_auto_path(mock_env_cache):
    """Test archiving to the default location."""
    task_data = {"id": "t1", "title": "Deleted Task", "projectId": "p1"}
    
    # Mock datetime to have stable filenames
    mock_now = datetime(2025, 1, 1, 12, 0, 0)
    
    with patch("ticktick.sdk.archiver.datetime") as mock_dt:
        mock_dt.now.return_value = mock_now
        
        # Mock filesystem
        with patch("builtins.open", new_callable=MagicMock) as mock_open:
            with patch("pathlib.Path.mkdir") as mock_mkdir:
                
                archiver.archive_deleted_task("p1", "t1", task_data)
                
                # Check mkdir calls
                # 1. get_cache_dir -> mkdir
                # 2. archive_deleted_task -> archive_dir.mkdir
                assert mock_mkdir.called
                
                # Verify JSON write
                expected_json_path = Path("/tmp/custom_cache/ticktick-access/deleted_tasks/task_t1_project_p1.deleted_20250101120000.json")
                mock_open.assert_any_call(expected_json_path, 'w')
                
                # Verify Log append
                expected_log_path = Path("/tmp/custom_cache/ticktick-access/deleted-tasks.log")
                mock_open.assert_any_call(expected_log_path, 'a')
                
                # Verify content written (roughly)
                # We can capture the file handle and check write calls if needed, 
                # but simply asserting the file opens is a good start.

def test_archive_deleted_task_explicit_path():
    """Test archiving to an explicit path."""
    task_data = {"id": "t1"}
    custom_path = Path("/custom/archive")
    
    with patch("ticktick.sdk.archiver.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2025, 1, 1, 12, 0, 0)
        
        with patch("builtins.open", new_callable=MagicMock) as mock_open:
            with patch("pathlib.Path.mkdir"):
                archiver.archive_deleted_task("p1", "t1", task_data, archive_path=custom_path)
                
                expected_json_path = custom_path / "task_t1_project_p1.deleted_20250101120000.json"
                mock_open.assert_any_call(expected_json_path, 'w')
