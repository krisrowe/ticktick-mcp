"""TickTick API HTTP client.

This module provides the HTTP client for making authenticated
requests to the TickTick API. The client requires a token at
construction — it never resolves credentials itself. Token
resolution is the caller's responsibility (CLI, MCP, etc.).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Constants
TICKTICK_API_BASE = "https://api.ticktick.com/open/v1"
USER_AGENT = "ticktick-access/1.0"


class TickTickClient:
    """Authenticated HTTP client for the TickTick API."""

    def __init__(self, token: str):
        self.token = token

    async def request(
        self,
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
        headers = {
            "User-Agent": USER_AGENT,
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        url = f"{TICKTICK_API_BASE}/{endpoint}"

        async with httpx.AsyncClient() as http_client:
            try:
                response = await http_client.request(
                    method, url, headers=headers, json=data, params=params, timeout=30.0
                )
                response.raise_for_status()

                # Handle successful empty responses (e.g. 204 No Content)
                if response.status_code == 204 or not response.content:
                    return {}

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

    async def get(self, endpoint: str, params: dict[str, Any] | None = None):
        """Make a GET request."""
        return await self.request("GET", endpoint, params=params)

    async def post(self, endpoint: str, data: dict[str, Any] | None = None):
        """Make a POST request."""
        return await self.request("POST", endpoint, data=data)

    async def delete(self, endpoint: str):
        """Make a DELETE request."""
        return await self.request("DELETE", endpoint)
