import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from ticktick.sdk import security

@pytest.fixture
def mock_otp_path():
    with patch("ticktick.sdk.security.get_otp_path", return_value=Path("/tmp/mock_otp.json")):
        yield

def test_generate_otp(mock_otp_path):
    """Test generating an OTP saves to file."""
    with patch("builtins.open", new_callable=MagicMock) as mock_open:
        with patch("json.dump") as mock_json_dump:
            otp = security.generate_otp(expiry_seconds=60)
            
            assert len(otp) == 6
            mock_open.assert_called_with(Path("/tmp/mock_otp.json"), 'w')
            
            # Verify JSON structure was passed to dump
            mock_json_dump.assert_called_once()
            args = mock_json_dump.call_args[0]
            data = args[0]
            assert data["otp"] == otp
            assert "expires_at" in data

def test_validate_otp_success(mock_otp_path):
    """Test validating a correct OTP."""
    valid_data = {
        "otp": "ABC123",
        "expires_at": time.time() + 60
    }
    
    with patch("builtins.open", new_callable=MagicMock) as mock_open:
        # Setup read mock
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps(valid_data)
        mock_open.return_value = mock_file
        
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "unlink") as mock_unlink:
                
                result = security.validate_otp("ABC123")
                
                assert result is True
                mock_unlink.assert_called_once() # Should delete after use

def test_validate_otp_expired(mock_otp_path):
    """Test validating an expired OTP."""
    expired_data = {
        "otp": "ABC123",
        "expires_at": time.time() - 10
    }
    
    with patch("builtins.open", new_callable=MagicMock) as mock_open:
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps(expired_data)
        mock_open.return_value = mock_file
        
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "unlink"):
                result = security.validate_otp("ABC123")
                assert result is False

def test_validate_otp_wrong_code(mock_otp_path):
    """Test validating a wrong OTP."""
    data = {
        "otp": "ABC123",
        "expires_at": time.time() + 60
    }
    
    with patch("builtins.open", new_callable=MagicMock) as mock_open:
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps(data)
        mock_open.return_value = mock_file
        
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "unlink"):
                result = security.validate_otp("WRONG")
                assert result is False

def test_validate_otp_no_file(mock_otp_path):
    """Test validating when no OTP file exists."""
    with patch.object(Path, "exists", return_value=False):
        assert security.validate_otp("ABC123") is False
