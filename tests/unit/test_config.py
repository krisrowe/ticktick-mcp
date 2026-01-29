import pytest
from unittest.mock import MagicMock, patch
from ticktick import config

# Mock manifest data
MOCK_MANIFEST = {
    "test.string": {
        "description": "A test string",
        "type": "string",
        "default": "default_str"
    },
    "test.bool": {
        "description": "A test boolean",
        "type": "boolean",
        "default": False
    },
    "test.choice": {
        "description": "A test choice",
        "type": "choice",
        "options": ["a", "b", "c"],
        "default": "a"
    }
}

@pytest.fixture
def mock_manifest():
    with patch("ticktick.config.load_manifest", return_value=MOCK_MANIFEST):
        yield

@pytest.fixture
def mock_config_file():
    # Mock load_config to return empty dict by default
    with patch("ticktick.config.load_config", return_value={}) as mock_load:
        with patch("ticktick.config.save_config") as mock_save:
            yield mock_load, mock_save

def test_get_setting_defaults(mock_manifest, mock_config_file):
    """Test retrieving default values."""
    assert config.get_setting("test.string") == "default_str"
    assert config.get_setting("test.bool") is False

def test_get_setting_user_value(mock_manifest, mock_config_file):
    """Test retrieving user-configured values."""
    mock_load, _ = mock_config_file
    mock_load.return_value = {"settings": {"test.string": "user_val"}}
    
    assert config.get_setting("test.string") == "user_val"

def test_set_setting_valid(mock_manifest, mock_config_file):
    """Test setting a valid value."""
    _, mock_save = mock_config_file
    
    config.set_setting("test.string", "new_val")
    
    mock_save.assert_called_once()
    saved_config = mock_save.call_args[0][0]
    assert saved_config["settings"]["test.string"] == "new_val"

def test_set_setting_unknown(mock_manifest, mock_config_file):
    """Test setting an unknown key raises ValueError."""
    with pytest.raises(ValueError, match="Unknown setting"):
        config.set_setting("unknown.key", "val")

def test_set_setting_bool_conversion(mock_manifest, mock_config_file):
    """Test boolean string conversion."""
    _, mock_save = mock_config_file
    
    config.set_setting("test.bool", "true")
    assert mock_save.call_args[0][0]["settings"]["test.bool"] is True
    
    config.set_setting("test.bool", "False")
    assert mock_save.call_args[0][0]["settings"]["test.bool"] is False

    with pytest.raises(ValueError):
        config.set_setting("test.bool", "not_a_bool")

def test_set_setting_choice_validation(mock_manifest, mock_config_file):
    """Test choice validation."""
    config.set_setting("test.choice", "b") # Valid
    
    with pytest.raises(ValueError, match="Invalid value"):
        config.set_setting("test.choice", "d") # Invalid
