"""TickTick task operations.

This module provides functions for managing TickTick tasks.
"""

import logging
from typing import Any

from . import client

logger = logging.getLogger(__name__)

# Valid task fields that can be included in update payloads
TASK_FIELDS = {
    "id",
    "projectId",
    "title",
    "content",
    "desc",
    "startDate",
    "dueDate",
    "reminders",
    "repeat",
    "priority",
    "status",
    "sortOrder",
    "timeZone",
    "isAllDay",
    "completedTime",
    "createdTime",
    "modifiedTime",
    "progress",
    "items",
    "kind",
    "etag",
    "tags",
    "assignee",
    "modifier",
    "creator",
    "columnId",
    "checkStatus",
    "reminderCount",
    "commentCount",
    "attachments",
}


async def list_tasks(project_id: str) -> dict[str, Any]:
    """Fetch all tasks from a specific project.

    Args:
        project_id: The project ID.

    Returns:
        Dict with project_id, tasks list, count, and status breakdown.
    """
    tasks_data = await client.get(f"project/{project_id}/data")

    if tasks_data and "tasks" in tasks_data:
        tasks = tasks_data["tasks"]
        return {
            "project_id": project_id,
            "tasks": tasks,
            "count": len(tasks),
            "completed": sum(1 for t in tasks if t.get("status") == 2),
            "incomplete": sum(1 for t in tasks if t.get("status") == 0),
        }

    return {"project_id": project_id, "tasks": [], "count": 0, "completed": 0, "incomplete": 0}


async def get_task(project_id: str, task_id: str) -> dict[str, Any] | None:
    """Get a single task by ID.

    Args:
        project_id: The project ID containing the task.
        task_id: The task ID.

    Returns:
        Task dictionary, or None if not found.
    """
    return await client.get(f"project/{project_id}/task/{task_id}")


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
    """Create a new task in a project.

    Args:
        project_id: The project ID where the task should be created.
        title: The task title.
        content: Optional task description.
        priority: Priority level 0-5 (0=none, 1=low, 3=medium, 5=high).
        due_date: Optional due date in ISO 8601 format.
        reminders: Optional list of reminder triggers in ISO 8601 duration format.
            Examples: ["TRIGGER:PT0S"] (at due time), ["TRIGGER:-PT30M"] (30 min before),
            ["TRIGGER:-PT1H"] (1 hour before), ["TRIGGER:-P1D"] (1 day before).
        status: Optional status (0=open, 2=completed, -1=won't do). Default is 0 (open).
        completed_time: Optional completion timestamp in ISO 8601 format.
            Only meaningful when status=2. Example: "2025-01-15T10:30:00+0000".

    Returns:
        Dict with success status, task data, and message.
    """
    task_data = {
        "projectId": project_id,
        "title": title,
        "priority": max(0, min(5, priority)),
    }

    if content:
        task_data["content"] = content
    if due_date:
        task_data["dueDate"] = due_date
    if reminders:
        task_data["reminders"] = reminders
    if status is not None:
        task_data["status"] = status
    if completed_time:
        task_data["completedTime"] = completed_time

    result = await client.post("task", task_data)

    if result:
        return {
            "success": True,
            "task": result,
            "message": f"Task '{title}' created successfully",
        }

    return {"success": False, "error": "Failed to create task", "task": None}


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
    """Update an existing task.

    Args:
        project_id: The project ID containing the task.
        task_id: The task ID to update.
        title: Optional new title.
        content: Optional new description.
        priority: Optional new priority (0-5).
        due_date: Optional new due date in ISO 8601 format.
        status: Optional new status (0=open, 2=completed, -1=won't do).
        tags: Optional list of tags.
        reminders: Optional list of reminder triggers in ISO 8601 duration format.
            Examples: ["TRIGGER:PT0S"] (at due time), ["TRIGGER:-PT30M"] (30 min before).
        completed_time: Optional completion timestamp in ISO 8601 format.
            Example: "2025-01-15T10:30:00+0000".

    Returns:
        Dict with success status, task data, and message.
    """
    # Fetch existing task to merge with updates
    existing_task = await get_task(project_id, task_id)
    if not existing_task:
        return {"success": False, "error": f"Could not retrieve task {task_id}", "task": None}

    # Build update payload from existing task, keeping only valid fields
    update_payload = {k: v for k, v in existing_task.items() if k in TASK_FIELDS}
    update_payload["projectId"] = project_id

    # Apply updates
    if title is not None:
        update_payload["title"] = title
    if content is not None:
        update_payload["content"] = content
    if priority is not None:
        update_payload["priority"] = priority
    if due_date is not None:
        update_payload["dueDate"] = due_date
    if status is not None:
        update_payload["status"] = status
    if tags is not None:
        update_payload["tags"] = tags
    if reminders is not None:
        update_payload["reminders"] = reminders
    if completed_time is not None:
        update_payload["completedTime"] = completed_time

    result = await client.post(f"task/{task_id}", update_payload)

    if result:
        return {
            "success": True,
            "task": result,
            "message": f"Task '{update_payload.get('title', task_id)}' updated successfully",
        }

    return {"success": False, "error": "Failed to update task", "task": None}


async def complete_task(project_id: str, task_id: str) -> dict[str, Any]:
    """Mark a task as completed.

    Args:
        project_id: The project ID containing the task.
        task_id: The task ID to complete.

    Returns:
        Dict with success status, task data, and message.
    """
    result = await update_task(project_id, task_id, status=2)

    if result.get("success"):
        result["message"] = f"Task '{result['task'].get('title', task_id)}' marked as completed"

    return result


async def delete_task(
    project_id: str, 
    task_id: str, 
    archive_path: str | None = None, 
    otp: str | None = None,
    elevated: bool = False
) -> dict[str, Any]:
    """Delete a task permanently.

    Args:
        project_id: The project ID containing the task.
        task_id: The task ID to delete.
        archive_path: Optional directory to save the local snapshot. Falls back to 
                     'deletion.archive_path' setting, then XDG cache.
        otp: One-time password for elevated access.
        elevated: If True, enforces OTP validation (used by MCP tools).

    Returns:
        Dict with success status.
    """
    from .. import config
    from . import archiver, security

    # 1. Check Access Mode
    access_mode = config.get_setting("deletion.access")
    
    if access_mode == "disabled":
        return {"success": False, "error": "Deletion is disabled in settings (deletion.access)."}
    
    # 2. Security Check (OTP)
    if elevated:
        if not otp:
            return {"success": False, "error": "OTP required for deletion (elevated access)."}
        if not security.validate_otp(otp):
            return {"success": False, "error": "Security Check Failed: Invalid or expired OTP."}

    # 3. Handle Archival Logic
    # If explicit path provided, we ALWAYS archive there.
    # If NO path provided, we check if auto-archive is disabled.
    should_archive = False
    resolved_path = None

    if archive_path:
        should_archive = True
        resolved_path = archive_path
    else:
        # Check settings
        disable_auto = config.get_setting("deletion.disable_auto_archive")
        if not disable_auto:
            should_archive = True
            resolved_path = config.get_setting("deletion.archive") # Fallback to XDG handled in archiver if None

    if should_archive:
        # Fetch task details for archival
        task_data = await get_task(project_id, task_id)
        if task_data:
            archiver.archive_deleted_task(project_id, task_id, task_data, resolved_path)
        else:
            logger.warning(f"Task {task_id} not found for archival, proceeding with delete attempt.")
    else:
        logger.info(f"Archival skipped for task {task_id} (No path provided and auto-archive disabled).")

    # 4. Perform deletion
    # TickTick API: DELETE /open/v1/project/{projectId}/task/{taskId}
    result = await client.delete(f"project/{project_id}/task/{task_id}")
    
    # TickTick returns {} on success, None on error via our client wrapper
    if result is not None:
        return {"success": True, "message": f"Task {task_id} deleted successfully."}
        
    return {"success": False, "error": f"Failed to delete task {task_id}"}
