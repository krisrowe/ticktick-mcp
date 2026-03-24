"""MCP server implementation for TickTick task management.

This server provides a thin wrapper over the SDK, exposing TickTick
operations as MCP tools. All business logic lives in the SDK layer.
"""

from __future__ import annotations

import json
import logging
import os
from contextvars import ContextVar
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import Field
from starlette.types import ASGIApp, Receive, Scope, Send

from ..config import get_single_user_access_token
from ..sdk.client import TickTickClient
from ..sdk.projects import ProjectService
from ..sdk.tasks import TaskService

# Initialize logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Contextvar holds the per-request token for HTTP mode
_request_token: ContextVar[str | None] = ContextVar("_request_token", default=None)

# On Cloud Run, disable MCP's DNS rebinding protection — the load balancer
# and gapp's auth middleware handle host validation. Locally, use the
# default FastMCP constructor which enables localhost-only protection.
if os.environ.get("K_SERVICE"):
    from mcp.server.transport_security import TransportSecuritySettings
    mcp = FastMCP("ticktick", transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ))
else:
    mcp = FastMCP("ticktick")


def _resolve_token() -> str:
    """Resolve the token for the current request.

    HTTP mode: uses token from the request's Authorization header.
    stdio mode: falls back to local single-user token.
    """
    token = _request_token.get()
    if token:
        return token
    return get_single_user_access_token()


class _TokenExtractMiddleware:
    """ASGI middleware that extracts Bearer token into a contextvar."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            auth = headers.get(b"authorization", b"").decode()
            if auth.lower().startswith("bearer "):
                _request_token.set(auth[7:])
        await self.app(scope, receive, send)


# --- Resource Definitions ---


@mcp.resource("ticktick://tasks/{project_id}")
async def get_tasks_by_project_resource(project_id: str) -> str:
    """Get all tasks from a specific TickTick project."""
    try:
        tasks = TaskService(token=_resolve_token())
        result = await tasks.list(project_id)
        return json.dumps(result.get("tasks", []), indent=2)
    except ValueError as e:
        logger.error(f"Error in get_tasks_by_project_resource: {e}")
        return f"Error: {e}"


@mcp.resource("ticktick://projects")
async def get_all_projects_resource() -> str:
    """Get all TickTick projects available to the authenticated user."""
    try:
        projects = ProjectService(token=_resolve_token())
        result = await projects.list()
        return json.dumps(result, indent=2)
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
        projects = ProjectService(token=_resolve_token())
        result = await projects.list()
        return {"projects": result, "count": len(result)}
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
        tasks = TaskService(token=_resolve_token())
        return await tasks.list(project_id)
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
    priority: int = Field(default=0, description="Priority level from 0-5 (0=none, 1=low, 3=medium, 5=high)."),
    due_date: str | None = Field(default=None, description="Optional due date in ISO 8601 format."),
    reminders: list[str] | None = Field(  # noqa: B008
        default=None,
        description=(
            "Optional list of reminder triggers in ISO 8601 duration format. "
            "Examples: ['TRIGGER:PT0S'] (at due time), ['TRIGGER:-PT30M'] (30 min before), "
            "['TRIGGER:-PT1H'] (1 hour before), ['TRIGGER:-P1D'] (1 day before)."
        ),
    ),
    status: int | None = Field(
        default=None,
        description="Optional status: 0=open (default), 2=completed, -1=won't do.",
    ),
    completed_time: str | None = Field(
        default=None,
        description=(
            "Optional completion timestamp in ISO 8601 format. "
            "Only meaningful when status=2. Example: '2025-01-15T10:30:00+0000'."
        ),
    ),
) -> dict[str, Any]:
    """Create a new task in a TickTick project."""
    try:
        tasks = TaskService(token=_resolve_token())
        return await tasks.create(
            project_id=project_id,
            title=title,
            content=content,
            priority=priority,
            due_date=due_date,
            reminders=reminders,
            status=status,
            completed_time=completed_time,
        )
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
    status: int | None = Field(default=None, description="Optional new status (0=open, 2=completed, -1=won't do)."),
    tags: list[str] | None = Field(default=None, description="Optional list of tags."),  # noqa: B008
    reminders: list[str] | None = Field(  # noqa: B008
        default=None,
        description=(
            "Optional list of reminder triggers in ISO 8601 duration format. "
            "Examples: ['TRIGGER:PT0S'] (at due time), ['TRIGGER:-PT30M'] (30 min before)."
        ),
    ),
) -> dict[str, Any]:
    """Update an existing task in a TickTick project."""
    try:
        tasks = TaskService(token=_resolve_token())
        return await tasks.update(
            project_id=project_id,
            task_id=task_id,
            title=title,
            content=content,
            priority=priority,
            due_date=due_date,
            status=status,
            tags=tags,
            reminders=reminders,
        )
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
        tasks = TaskService(token=_resolve_token())
        return await tasks.complete(project_id=project_id, task_id=task_id)
    except ValueError as e:
        logger.error(f"Error completing task: {e}")
        return {"success": False, "error": str(e), "task": None}


@mcp.tool(
    name="delete_task",
    description="Permanently delete a task. Security level controlled by settings.",
)
async def delete_task(
    task_id: str = Field(description="The ID of the task to delete."),
    project_id: str = Field(description="The ID of the project containing the task."),
    otp: str = Field(description="One-time password generated via 'ticktick auth generate-otp' CLI. Required if deletion.access is 'elevated'."),
    archive_path: str | None = Field(default=None, description="Optional directory to save a local snapshot of the deleted task. Defaults to configured 'deletion.archive' setting or XDG cache."),
) -> dict[str, Any]:
    """
    Permanently delete a task from TickTick.

    WARNING: This action is irreversible.
    Depending on the 'deletion.access' setting, this may require an OTP from the CLI.
    """
    try:
        tasks = TaskService(token=_resolve_token())
        return await tasks.delete(
            project_id=project_id,
            task_id=task_id,
            archive_path=archive_path,
            otp=otp,
            elevated=True,
        )
    except Exception as e:
        logger.error(f"Error in delete_task tool: {e}")
        return {"success": False, "error": str(e)}


# ASGI application for HTTP mode (Docker/Cloud Run)
_inner_app = mcp.streamable_http_app()
mcp_app = _TokenExtractMiddleware(_inner_app)


def run_server():
    """Run the MCP server in stdio mode.

    This is the entry point for the ticktick-mcp command.
    """
    mcp.run(transport="stdio")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        mcp.run(transport="stdio")
