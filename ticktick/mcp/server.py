"""MCP server implementation for TickTick task management."""

import json
import logging
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from pydantic.fields import FieldInfo

from ..config import get_token

# Initialize logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("ticktick")

# Constants
TICKTICK_API_BASE = "https://api.ticktick.com/open/v1"
USER_AGENT = "ticktick-mcp-server/1.0"


# Helper function for making authenticated TickTick API requests
async def make_ticktick_request(
    method: str,
    endpoint: str,
    access_token: str,
    data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any] | list[dict[str, Any]] | None:
    """Make an authenticated request to the TickTick API."""
    headers = {
        "User-Agent": USER_AGENT,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    url = f"{TICKTICK_API_BASE}/{endpoint}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, url, headers=headers, json=data, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {url}: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred for {url}: {e}")
            return None


def get_ticktick_access_token() -> str:
    """Get TickTick access token from config or environment.

    Priority:
    1. TICKTICK_ACCESS_TOKEN environment variable (Docker/container usage)
    2. ~/.ticktick-access/token file
    """
    return get_token()


TICKTICK_TASK_FIELDS = {
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


def _extract_field_value(val):
    """Extract actual values from FieldInfo if needed (for direct function calls in tests)."""
    if isinstance(val, FieldInfo):
        return val.default if val.default is not ... else None
    return val


def _build_task_update_data(title, content, priority, due_date, status, tags):
    """Build the task update data dictionary from optional parameters."""
    new_task_data = {}
    if title is not None:
        new_task_data["title"] = title
    if content is not None:
        new_task_data["content"] = content
    if priority is not None:
        new_task_data["priority"] = priority
    if due_date is not None:
        new_task_data["dueDate"] = due_date
    if status is not None:
        new_task_data["status"] = status
    if tags is not None:
        new_task_data["tags"] = tags
    return new_task_data


async def _prepare_task_update_payload(
    task_id: str,
    project_id: str,
    new_task_data: dict,
    access_token: str,
) -> dict:
    """Prepare the payload for updating a task by fetching existing details and merging new data."""
    existing_task_response = await make_ticktick_request(
        "GET", f"project/{project_id}/task/{task_id}", access_token
    )
    if not existing_task_response:
        raise ValueError(f"Could not retrieve existing task {task_id}.")

    update_payload = {k: v for k, v in existing_task_response.items() if k in TICKTICK_TASK_FIELDS}
    update_payload.update(new_task_data)
    update_payload["projectId"] = project_id

    return update_payload


async def get_ticktick_tasks(access_token: str, list_id: str) -> list[dict[str, Any]] | None:
    """Fetch tasks from a specific TickTick list (project)."""
    endpoint = f"project/{list_id}/data"
    tasks = await make_ticktick_request("GET", endpoint, access_token)
    return tasks


async def get_ticktick_projects(access_token: str) -> list[dict[str, Any]] | None:
    """Fetch all projects (lists) from TickTick."""
    endpoint = "project"
    projects = await make_ticktick_request("GET", endpoint, access_token)
    return projects


# --- Resource Definitions ---


@mcp.resource("ticktick://tasks/{list_id}")
async def get_tasks_by_list_resource(list_id: str) -> str:
    """Get all tasks from a specific TickTick project."""
    try:
        access_token = get_ticktick_access_token()
        tasks_data = await get_ticktick_tasks(access_token, list_id=list_id)
        if tasks_data and "tasks" in tasks_data:
            return json.dumps(tasks_data["tasks"], indent=2)
        return json.dumps(tasks_data, indent=2) if tasks_data else "[]"
    except ValueError as e:
        logger.error(f"Error in get_tasks_by_list_resource: {e}")
        return f"Error: {e}"


@mcp.resource("ticktick://projects")
async def get_all_projects_resource() -> str:
    """Get all TickTick projects available to the authenticated user."""
    try:
        access_token = get_ticktick_access_token()
        projects = await get_ticktick_projects(access_token)
        return json.dumps(projects, indent=2) if projects else "[]"
    except ValueError as e:
        logger.error(f"Error in get_all_projects_resource: {e}")
        return f"Error: {e}"


# --- Tool Definitions ---


@mcp.tool(
    name="list_projects",
    description="List all TickTick projects. Returns project IDs, names, and metadata.",
)
async def list_projects() -> dict[str, Any]:
    """Retrieve all TickTick projects for the authenticated user."""
    try:
        access_token = get_ticktick_access_token()
        projects = await get_ticktick_projects(access_token)
        return {"projects": projects if projects else [], "count": len(projects) if projects else 0}
    except ValueError as e:
        logger.error(f"Error listing projects: {e}")
        return {"error": str(e), "projects": [], "count": 0}


@mcp.tool(
    name="list_tasks",
    description="List all tasks in a specific TickTick project.",
)
async def list_tasks(
    project_id: str = Field(description="The ID of the project to retrieve tasks from."),
) -> dict[str, Any]:
    """Retrieve all tasks from a specific TickTick project."""
    try:
        access_token = get_ticktick_access_token()
        tasks_data = await get_ticktick_tasks(access_token, list_id=project_id)
        if tasks_data and "tasks" in tasks_data:
            tasks = tasks_data["tasks"]
            return {
                "project_id": project_id,
                "tasks": tasks,
                "count": len(tasks),
                "completed": sum(1 for t in tasks if t.get("status") == 1),
                "incomplete": sum(1 for t in tasks if t.get("status") == 0),
            }
        return {"project_id": project_id, "tasks": [], "count": 0, "completed": 0, "incomplete": 0}
    except ValueError as e:
        logger.error(f"Error listing tasks: {e}")
        return {"error": str(e), "project_id": project_id, "tasks": [], "count": 0}


@mcp.tool(
    name="create_task",
    description="Create a new task in a TickTick project.",
)
async def create_task(
    project_id: str = Field(description="The ID of the project where the task should be created."),
    title: str = Field(description="The title of the task."),
    content: str = Field(default="", description="Optional description for the task."),
    priority: int = Field(default=0, description="Priority level from 0-5 (0=normal)."),
    due_date: str | None = Field(default=None, description="Optional due date in ISO 8601 format."),
) -> dict[str, Any]:
    """Create a new task in a TickTick project."""
    try:
        access_token = get_ticktick_access_token()
        task_data = {
            "projectId": project_id,
            "title": title,
            "priority": max(0, min(5, priority)),
        }
        if content:
            task_data["content"] = content
        if due_date:
            task_data["dueDate"] = due_date

        result = await make_ticktick_request("POST", "task", access_token, data=task_data)
        if result:
            return {
                "success": True,
                "task": result,
                "message": f"Task '{title}' created successfully in project {project_id}",
            }
        return {"success": False, "error": "Failed to create task", "task": None}
    except ValueError as e:
        logger.error(f"Error creating task: {e}")
        return {"success": False, "error": str(e), "task": None}


@mcp.tool(
    name="update_task",
    description="Update an existing task in a TickTick project.",
)
async def update_task(
    task_id: str = Field(description="The ID of the task to update."),
    project_id: str = Field(description="The ID of the project containing the task."),
    title: str | None = Field(default=None, description="Optional new title for the task."),
    content: str | None = Field(default=None, description="Optional new description for the task."),
    priority: int | None = Field(default=None, description="Optional new priority level from 0-5."),
    due_date: str | None = Field(default=None, description="Optional new due date in ISO 8601 format."),
    status: int | None = Field(default=None, description="Optional new status (0=incomplete, 1=completed)."),
    tags: list[str] | None = Field(default=None, description="Optional list of tags."),  # noqa: B008
) -> dict[str, Any]:
    """Update an existing task in a TickTick project."""
    try:
        access_token = get_ticktick_access_token()

        title = _extract_field_value(title)
        content = _extract_field_value(content)
        priority = _extract_field_value(priority)
        due_date = _extract_field_value(due_date)
        status = _extract_field_value(status)
        tags = _extract_field_value(tags)

        new_task_data = _build_task_update_data(title, content, priority, due_date, status, tags)
        update_payload = await _prepare_task_update_payload(task_id, project_id, new_task_data, access_token)
        result = await make_ticktick_request("POST", f"task/{task_id}", access_token, data=update_payload)

        if result:
            return {
                "success": True,
                "message": f"Task '{update_payload.get('title', task_id)}' updated successfully",
                "task": result,
            }
        return {"success": False, "error": "Failed to update task", "task": None}
    except ValueError as e:
        logger.error(f"Error updating task: {e}")
        return {"success": False, "error": str(e), "task": None}


@mcp.tool(
    name="complete_task",
    description="Mark a task as complete.",
)
async def complete_task(
    task_id: str = Field(description="The ID of the task to complete."),
    project_id: str = Field(description="The ID of the project containing the task."),
) -> dict[str, Any]:
    """Mark a task as completed in TickTick."""
    try:
        access_token = get_ticktick_access_token()
        new_task_data = {"status": 1}
        update_payload = await _prepare_task_update_payload(task_id, project_id, new_task_data, access_token)
        result = await make_ticktick_request("POST", f"task/{task_id}", access_token, data=update_payload)

        if result:
            return {
                "success": True,
                "message": f"Task '{update_payload.get('title', task_id)}' marked as completed",
                "task": result,
            }
        return {"success": False, "error": "Failed to update task"}
    except ValueError as e:
        logger.error(f"Error completing task: {e}")
        return {"success": False, "error": str(e), "task": None}


# ASGI application for HTTP mode (Docker)
mcp_app = mcp.streamable_http_app()


def run_server():
    """Run the MCP server in stdio mode.

    This is the entry point for the ticktick-mcp command.
    """
    mcp.run(transport="stdio")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        mcp.run(transport="stdio")
