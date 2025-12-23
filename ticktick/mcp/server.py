"""MCP server implementation for TickTick task management.

This server provides a thin wrapper over the SDK, exposing TickTick
operations as MCP tools. All business logic lives in the SDK layer.
"""

import json
import logging
import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from ..sdk import projects as sdk_projects
from ..sdk import tasks as sdk_tasks

# Initialize logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("ticktick")


# --- Resource Definitions ---


@mcp.resource("ticktick://tasks/{project_id}")
async def get_tasks_by_project_resource(project_id: str) -> str:
    """Get all tasks from a specific TickTick project."""
    try:
        result = await sdk_tasks.list_tasks(project_id)
        return json.dumps(result.get("tasks", []), indent=2)
    except ValueError as e:
        logger.error(f"Error in get_tasks_by_project_resource: {e}")
        return f"Error: {e}"


@mcp.resource("ticktick://projects")
async def get_all_projects_resource() -> str:
    """Get all TickTick projects available to the authenticated user."""
    try:
        projects = await sdk_projects.list_projects()
        return json.dumps(projects, indent=2)
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
        projects = await sdk_projects.list_projects()
        return {"projects": projects, "count": len(projects)}
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
        return await sdk_tasks.list_tasks(project_id)
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
) -> dict[str, Any]:
    """Create a new task in a TickTick project."""
    try:
        return await sdk_tasks.create_task(
            project_id=project_id,
            title=title,
            content=content,
            priority=priority,
            due_date=due_date,
            reminders=reminders,
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
        return await sdk_tasks.update_task(
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
        return await sdk_tasks.complete_task(project_id=project_id, task_id=task_id)
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
