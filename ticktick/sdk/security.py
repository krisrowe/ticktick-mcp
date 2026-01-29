"""Security utilities for TickTick access."""

import json
import os
import time
import secrets
import string
from pathlib import Path

def get_otp_path() -> Path:
    """Get the path to the OTP cache file."""
    cache_dir = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache")) / "ticktick-access"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "delete_otp.json"

def generate_otp(expiry_seconds: int = 60) -> str:
    """Generate a random OTP and save it with an expiry timestamp."""
    otp = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    data = {
        "otp": otp,
        "expires_at": time.time() + expiry_seconds
    }
    
    with open(get_otp_path(), 'w') as f:
        json.dump(data, f)
        
    return otp

def validate_otp(provided_otp: str) -> bool:
    """Check if the provided OTP is valid and hasn't expired.
    
    Consumes the OTP (deletes it) on any attempt to prevent reuse.
    """
    path = get_otp_path()
    if not path.exists():
        return False
        
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            
        # Delete immediately to prevent reuse
        path.unlink()
        
        if data.get("otp") != provided_otp:
            return False
            
        if time.time() > data.get("expires_at", 0):
            return False
            
        return True
    except Exception:
        return False
