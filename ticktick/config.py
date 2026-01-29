"""Configuration management for ticktick-access.

Stores configuration in ~/.ticktick-access/:
  - config.yaml: Client credentials (client_id, client_secret)
  - token: Access token (plain text)
"""

import os
from pathlib import Path
from typing import Optional, Any
import importlib.resources

import yaml

# ... existing code ...

def load_manifest() -> dict:
    """Load the settings manifest from the package."""
    try:
        # Assuming the manifest is at ticktick/sdk/resources/settings-manifest.yaml
        # We need to access it via the package structure
        ref = importlib.resources.files("ticktick.sdk.resources").joinpath("settings-manifest.yaml")
        with ref.open("r") as f:
            return yaml.safe_load(f).get("settings", {})
    except Exception as e:
        # Fallback if resource not found (e.g. during development/editable install quirks)
        # Or log error. For now return empty dict.
        return {}

def get_setting(key: str) -> Any:
    """Get a setting value, falling back to default from manifest."""
    config = load_config()
    
    # Check user config first (settings keys are flat in config.yaml under 'settings' dict?)
    # Or flat at root? Let's namespace them under 'settings' to avoid collision with client_id
    user_val = config.get("settings", {}).get(key)
    if user_val is not None:
        return user_val
        
    # Check manifest default
    manifest = load_manifest()
    setting_def = manifest.get(key)
    if setting_def:
        return setting_def.get("default")
        
    return None

def set_setting(key: str, value: Any) -> None:
    """Set a setting value, validating against manifest."""
    manifest = load_manifest()
    setting_def = manifest.get(key)
    
    if not setting_def:
        raise ValueError(f"Unknown setting: {key}")
        
    # Type Conversion / Validation
    stype = setting_def.get("type")
    
    # Handle booleans from CLI strings
    if stype == "boolean" and isinstance(value, str):
        if value.lower() in ("true", "yes", "1", "on"):
            value = True
        elif value.lower() in ("false", "no", "0", "off"):
            value = False
        else:
            raise ValueError(f"Invalid boolean value '{value}'. Use true/false.")

    if stype == "choice":
        options = setting_def.get("options", [])
        if value not in options:
            raise ValueError(f"Invalid value '{value}'. Allowed: {options}")
            
    # Save
    config = load_config()
    if "settings" not in config:
        config["settings"] = {}
        
    config["settings"][key] = value
    save_config(config)

def list_settings() -> dict:
    """Return all settings with their current values and metadata."""
    manifest = load_manifest()
    config = load_config().get("settings", {})
    
    results = {}
    for key, meta in manifest.items():
        results[key] = {
            "value": config.get(key, meta.get("default")),
            "default": meta.get("default"),
            "description": meta.get("description"),
            "help": meta.get("help"),
            "type": meta.get("type"),
            "options": meta.get("options")
        }
    return results

CONFIG_DIR = Path.home() / ".ticktick-access"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
TOKEN_FILE = CONFIG_DIR / "token"


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    return CONFIG_DIR


def ensure_config_dir() -> Path:
    """Ensure the configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_config() -> dict:
    """Load configuration from config.yaml."""
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f) or {}


def save_config(config: dict) -> None:
    """Save configuration to config.yaml."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    # Secure permissions
    CONFIG_FILE.chmod(0o600)


def get_client_credentials() -> tuple[Optional[str], Optional[str]]:
    """Get client credentials from config.

    Returns:
        Tuple of (client_id, client_secret), either may be None if not set.
    """
    config = load_config()
    return config.get("client_id"), config.get("client_secret")


def save_client_credentials(client_id: str, client_secret: str) -> None:
    """Save client credentials to config."""
    config = load_config()
    config["client_id"] = client_id
    config["client_secret"] = client_secret
    save_config(config)


def load_token() -> Optional[str]:
    """Load access token from token file.

    Returns:
        The access token, or None if not found.
    """
    if not TOKEN_FILE.exists():
        return None
    return TOKEN_FILE.read_text().strip()


def save_token(token: str) -> None:
    """Save access token to token file."""
    ensure_config_dir()
    TOKEN_FILE.write_text(token)
    # Secure permissions
    TOKEN_FILE.chmod(0o600)


def get_token() -> str:
    """Get access token from environment or config file.

    Priority:
    1. TICKTICK_ACCESS_TOKEN environment variable
    2. ~/.ticktick-access/token file

    Returns:
        The access token.

    Raises:
        ValueError: If no token is found.
    """
    # Check environment variable first (for Docker/container usage)
    token = os.getenv("TICKTICK_ACCESS_TOKEN")
    if token:
        return token

    # Fall back to config file
    token = load_token()
    if token:
        return token

    raise ValueError(
        "No access token found. Run 'ticktick auth' to authenticate, "
        "or set TICKTICK_ACCESS_TOKEN environment variable."
    )
