"""TickTick project (list) operations.

Module-level async functions taking a :class:`TickTickClient`.
Use :class:`ticktick.sdk.client.TickTickSDK` from MCP tools — it
constructs the client from the current user's profile.
"""

from __future__ import annotations

from typing import Any

from ticktick.sdk.client import TickTickClient


async def list_projects(client: TickTickClient) -> list[dict[str, Any]]:
    """Return all TickTick projects for the authenticated user."""
    result = await client.get("project")
    return result if isinstance(result, list) else []


async def count_projects(client: TickTickClient) -> int:
    """Return the number of TickTick projects for the authenticated user."""
    return len(await list_projects(client))


async def get_project_data(client: TickTickClient, project_id: str) -> dict[str, Any] | None:
    """Return full project data including its tasks, or None if not found."""
    return await client.get(f"project/{project_id}/data")
