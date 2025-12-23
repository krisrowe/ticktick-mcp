"""TickTick project operations.

This module provides functions for managing TickTick projects (lists).
"""

from typing import Any

from . import client


async def list_projects() -> list[dict[str, Any]]:
    """Fetch all projects from TickTick.

    Returns:
        List of project dictionaries, or empty list if request failed.
    """
    result = await client.get("project")
    return result if result else []


async def get_project_data(project_id: str) -> dict[str, Any] | None:
    """Get full project data including tasks.

    Args:
        project_id: The project ID.

    Returns:
        Project data dictionary with tasks, or None if request failed.
    """
    return await client.get(f"project/{project_id}/data")
