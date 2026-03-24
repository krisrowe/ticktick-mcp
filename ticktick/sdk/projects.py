"""TickTick project operations.

This module provides the ProjectService class for managing TickTick projects (lists).
"""

from __future__ import annotations

from typing import Any

from .client import TickTickClient


class ProjectService:
    """Service for TickTick project operations."""

    def __init__(self, client: TickTickClient | None = None, *, token: str | None = None):
        if client:
            self.client = client
        elif token:
            self.client = TickTickClient(token)
        else:
            raise ValueError("Either client or token is required.")

    async def list(self) -> list[dict[str, Any]]:
        """Fetch all projects from TickTick.

        Returns:
            List of project dictionaries, or empty list if request failed.
        """
        result = await self.client.get("project")
        return result if result else []

    async def get_data(self, project_id: str) -> dict[str, Any] | None:
        """Get full project data including tasks.

        Args:
            project_id: The project ID.

        Returns:
            Project data dictionary with tasks, or None if request failed.
        """
        return await self.client.get(f"project/{project_id}/data")
