"""TickTick SDK — programmatic access to the TickTick Open API.

Layout:
    sdk.client       — low-level HTTP client and the SDK facade
    sdk.projects     — project (list) operations
    sdk.tasks        — task operations

The :class:`TickTickSDK` facade in ``sdk.client`` is the entry point
for MCP tools. It reads the access token from mcp-app's
``current_user`` context, so callers don't pass tokens around.
"""

from ticktick.sdk.client import (
    APIError,
    AuthenticationError,
    TickTickClient,
    TickTickError,
    TickTickSDK,
)

__all__ = [
    "TickTickClient",
    "TickTickSDK",
    "TickTickError",
    "AuthenticationError",
    "APIError",
]
