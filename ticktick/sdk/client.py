"""TickTick API HTTP client.

This module provides the low-level HTTP client for making authenticated
requests to the TickTick API.
"""

import logging
import os
from typing import Any

import httpx

from ..config import get_token, load_token

logger = logging.getLogger(__name__)

# Constants
TICKTICK_API_BASE = "https://api.ticktick.com/open/v1"
USER_AGENT = "ticktick-access/1.0"


def get_access_token() -> str:
    """Get access token from environment or config file.

    Returns:
        The access token.
    """
    return get_token()


async def request(
    method: str,
    endpoint: str,
    data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any] | list[dict[str, Any]] | None:
    """Make an authenticated request to the TickTick API.

    Args:
        method: HTTP method (GET, POST, DELETE, etc.)
        endpoint: API endpoint (without base URL)
        data: Optional JSON body data
        params: Optional query parameters

    Returns:
        Parsed JSON response, or None if request failed.
    """
    access_token = get_access_token()
    headers = {
        "User-Agent": USER_AGENT,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    url = f"{TICKTICK_API_BASE}/{endpoint}"

    async with httpx.AsyncClient() as http_client:
        try:
            response = await http_client.request(
                method, url, headers=headers, json=data, params=params, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {url}: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            return None


async def get(endpoint: str, params: dict[str, Any] | None = None):
    """Make a GET request."""
    return await request("GET", endpoint, params=params)


async def post(endpoint: str, data: dict[str, Any] | None = None):
    """Make a POST request."""
    return await request("POST", endpoint, data=data)


async def delete(endpoint: str):
    """Make a DELETE request."""
    return await request("DELETE", endpoint)
