"""TickTick task operations.

Module-level async functions taking a :class:`TickTickClient`.
Use :class:`ticktick.sdk.client.TickTickSDK` from MCP tools — it
constructs the client from the current user's profile.
"""

from __future__ import annotations

from typing import Any

from ticktick.sdk.client import APIError, TickTickClient


# Fields that round-trip through the TickTick task PUT endpoint.
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


async def list_tasks(client: TickTickClient, project_id: str) -> dict[str, Any]:
    """Return all tasks in a project plus a small status summary."""
    data = await client.get(f"project/{project_id}/data")
    tasks = (data or {}).get("tasks", []) if isinstance(data, dict) else []
    return {
        "project_id": project_id,
        "tasks": tasks,
        "count": len(tasks),
        "completed": sum(1 for t in tasks if t.get("status") == 2),
        "incomplete": sum(1 for t in tasks if t.get("status") == 0),
    }


async def get_task(
    client: TickTickClient, project_id: str, task_id: str,
) -> dict[str, Any] | None:
    """Return a single task by ID, or None if not found."""
    return await client.get(f"project/{project_id}/task/{task_id}")


async def create_task(
    client: TickTickClient,
    project_id: str,
    title: str,
    content: str = "",
    priority: int = 0,
    due_date: str | None = None,
    reminders: list[str] | None = None,
    status: int | None = None,
    completed_time: str | None = None,
) -> dict[str, Any]:
    """Create a new task in a project."""
    payload: dict[str, Any] = {
        "projectId": project_id,
        "title": title,
        "priority": max(0, min(5, priority)),
    }
    if content:
        payload["content"] = content
    if due_date:
        payload["dueDate"] = due_date
    if reminders:
        payload["reminders"] = reminders
    if status is not None:
        payload["status"] = status
    if completed_time:
        payload["completedTime"] = completed_time

    return await client.post("task", payload)


async def update_task(
    client: TickTickClient,
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
    """Update an existing task. Preserves untouched fields."""
    existing = await get_task(client, project_id, task_id)
    if not existing:
        raise APIError(f"Task not found: {task_id} in project {project_id}")

    payload = {k: v for k, v in existing.items() if k in TASK_FIELDS}
    payload["projectId"] = project_id

    if title is not None:
        payload["title"] = title
    if content is not None:
        payload["content"] = content
    if priority is not None:
        payload["priority"] = priority
    if due_date is not None:
        payload["dueDate"] = due_date
    if status is not None:
        payload["status"] = status
    if tags is not None:
        payload["tags"] = tags
    if reminders is not None:
        payload["reminders"] = reminders
    if completed_time is not None:
        payload["completedTime"] = completed_time

    return await client.post(f"task/{task_id}", payload)


async def complete_task(
    client: TickTickClient, project_id: str, task_id: str,
) -> dict[str, Any]:
    """Mark a task as completed (status=2)."""
    return await update_task(client, project_id, task_id, status=2)


async def delete_task(client: TickTickClient, project_id: str, task_id: str) -> None:
    """Permanently delete a task."""
    await client.delete(f"project/{project_id}/task/{task_id}")
