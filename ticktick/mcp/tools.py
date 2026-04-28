"""MCP tools for TickTick task management.

Plain async functions — discovered and registered by mcp-app.
Function names become tool names, docstrings become descriptions,
type hints become schemas. All business logic lives in the SDK.
"""

from __future__ import annotations

import logging
from typing import Any

from ticktick.sdk.client import APIError, AuthenticationError, TickTickSDK

logger = logging.getLogger(__name__)
sdk = TickTickSDK


async def list_projects() -> dict[str, Any]:
    """List all TickTick projects (lists) for the authenticated user.

    Returns project IDs, names, and metadata. Use a project ID with
    list_tasks to retrieve its tasks.
    """
    try:
        return await sdk.list_projects()
    except AuthenticationError as e:
        return {"error": str(e), "projects": [], "count": 0}
    except APIError as e:
        logger.error(f"list_projects: {e}")
        return {"error": str(e), "projects": [], "count": 0}


async def list_tasks(project_id: str) -> dict[str, Any]:
    """List all tasks in a TickTick project.

    Args:
        project_id: The project ID (from list_projects).
    """
    try:
        return await sdk.list_tasks(project_id)
    except AuthenticationError as e:
        return {"error": str(e), "project_id": project_id, "tasks": [], "count": 0}
    except APIError as e:
        logger.error(f"list_tasks: {e}")
        return {"error": str(e), "project_id": project_id, "tasks": [], "count": 0}


async def create_task(
    project_id: str,
    title: str,
    content: str = "",
    priority: int = 0,
    due_date: str | None = None,
    reminders: list[str] | None = None,
    status: int | None = None,
    completed_time: str | None = None,
) -> dict[str, Any]:
    """Create a new task in a TickTick project.

    Args:
        project_id: The project ID where the task should be created.
        title: The task title.
        content: Optional task description.
        priority: Priority level 0-5 (0=none, 1=low, 3=medium, 5=high).
        due_date: Optional due date in ISO 8601 format.
        reminders: Optional list of reminder triggers in ISO 8601
            duration format. Examples: ['TRIGGER:PT0S'] (at due time),
            ['TRIGGER:-PT30M'] (30 min before), ['TRIGGER:-P1D']
            (1 day before).
        status: Optional status (0=open, 2=completed, -1=won't do).
        completed_time: Optional completion timestamp in ISO 8601
            format (only meaningful when status=2).
    """
    try:
        return await sdk.create_task(
            project_id,
            title,
            content=content,
            priority=priority,
            due_date=due_date,
            reminders=reminders,
            status=status,
            completed_time=completed_time,
        )
    except AuthenticationError as e:
        return {"success": False, "error": str(e), "task": None}
    except APIError as e:
        logger.error(f"create_task: {e}")
        return {"success": False, "error": str(e), "task": None}


async def update_task(
    project_id: str,
    task_id: str,
    title: str | None = None,
    content: str | None = None,
    priority: int | None = None,
    due_date: str | None = None,
    status: int | None = None,
    tags: list[str] | None = None,
    reminders: list[str] | None = None,
    completed_time: str | None = None,
) -> dict[str, Any]:
    """Update an existing task in a TickTick project.

    Untouched fields are preserved.

    Args:
        project_id: The project ID containing the task.
        task_id: The task ID to update.
        title: Optional new title.
        content: Optional new description.
        priority: Optional new priority (0-5).
        due_date: Optional new due date in ISO 8601 format.
        status: Optional new status (0=open, 2=completed, -1=won't do).
        tags: Optional new tag list.
        reminders: Optional new reminders in ISO 8601 duration format.
        completed_time: Optional completion timestamp.
    """
    try:
        return await sdk.update_task(
            project_id,
            task_id,
            title=title,
            content=content,
            priority=priority,
            due_date=due_date,
            status=status,
            tags=tags,
            reminders=reminders,
            completed_time=completed_time,
        )
    except AuthenticationError as e:
        return {"success": False, "error": str(e), "task": None}
    except APIError as e:
        logger.error(f"update_task: {e}")
        return {"success": False, "error": str(e), "task": None}


async def complete_task(project_id: str, task_id: str) -> dict[str, Any]:
    """Mark a task as completed.

    Args:
        project_id: The project ID containing the task.
        task_id: The task ID to complete.
    """
    try:
        return await sdk.complete_task(project_id, task_id)
    except AuthenticationError as e:
        return {"success": False, "error": str(e), "task": None}
    except APIError as e:
        logger.error(f"complete_task: {e}")
        return {"success": False, "error": str(e), "task": None}


async def delete_task(project_id: str, task_id: str) -> dict[str, Any]:
    """Permanently delete a task in a TickTick project.

    This action is irreversible. The MCP client should confirm with
    the user before invoking it.

    Args:
        project_id: The project ID containing the task.
        task_id: The task ID to delete.
    """
    try:
        return await sdk.delete_task(project_id, task_id)
    except AuthenticationError as e:
        return {"success": False, "error": str(e)}
    except APIError as e:
        logger.error(f"delete_task: {e}")
        return {"success": False, "error": str(e)}
