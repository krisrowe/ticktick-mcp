import logging  # For proper logging to stderr
import os  # For environment variables like API keys
from typing import Any

import httpx  # Required for making HTTP requests to TickTick API
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from pydantic.fields import FieldInfo

# Initialize logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Initialize FastMCP server
mcp = FastMCP("ticktick")

# Constants
TICKTICK_API_BASE = "https://api.ticktick.com/open/v1"
# The actual auth flow for TickTick API is usually OAuth2, and initial authorization
# would happen out-of-band to get an access token. API calls then use this token.
# For simplicity, we'll assume an access token is available via environment variable.
# TICKTICK_AUTH_BASE = "https://ticktick.com/oauth/authorize" # Not directly used for API calls
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
            response.raise_for_status()  # Raise an exception for HTTP errors
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


# Placeholder for access token retrieval - will be implemented via OAuth later if required
# For now, assume TICKTICK_ACCESS_TOKEN is set in environment variables
def get_ticktick_access_token() -> str:
    token = os.getenv("TICKTICK_ACCESS_TOKEN")
    if not token:
        logger.error("TICKTICK_ACCESS_TOKEN environment variable not set.")
        raise ValueError("TickTick access token is required.")
    return token


TICKTICK_TASK_FIELDS = {  # Define the fields that are expected in a TickTick task payload for updates
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
    """
    Prepares the payload for updating a task by fetching existing details and merging new data.
    """
    # For make_ticktick_request, we pass the raw endpoint 'task/{task_id}'
    # The base_url from mcp.get_resource is for displaying to the user, not direct API endpoint construction.

    # Fetch existing task details to ensure we send all required fields for update
    existing_task_response = await make_ticktick_request("GET", f"task/{task_id}", access_token)
    if not existing_task_response:
        raise ValueError(f"Could not retrieve existing task {task_id}.")

    # Start with existing data, filtering to known TickTick task fields
    update_payload = {k: v for k, v in existing_task_response.items() if k in TICKTICK_TASK_FIELDS}

    # Merge new data, prioritizing new_task_data
    update_payload.update(new_task_data)

    # Ensure projectId is always present and correct, as per TickTick API requirements
    update_payload["projectId"] = project_id

    return update_payload


# TickTick API Interaction Functions (wrappers around make_ticktick_request)


async def get_ticktick_tasks(access_token: str, list_id: str) -> list[dict[str, Any]] | None:
    """Fetches tasks from a specific TickTick list (project)."""
    endpoint = f"project/{list_id}/data"
    tasks = await make_ticktick_request("GET", endpoint, access_token)
    return tasks


async def get_ticktick_projects(access_token: str) -> list[dict[str, Any]] | None:
    """Fetches all projects (lists) from TickTick."""
    endpoint = "project"
    projects = await make_ticktick_request("GET", endpoint, access_token)
    return projects


# --- Resource Definitions ---
# Resources provide read-only access to TickTick data


@mcp.resource("ticktick://tasks/{list_id}")
async def get_tasks_by_list_resource(list_id: str) -> str:
    """
    Get all tasks from a specific TickTick project (also called 'list' in the UI).

    Projects act like folders/containers - every task in TickTick must belong to
    exactly one project. The Inbox is a special project that is currently
    inaccessible via this MCP server.

    Args:
        list_id: The ID of the project/list to retrieve tasks from.
                 You can find project IDs by using the list_projects tool
                 or reading the ticktick://projects resource.

    Returns:
        JSON string containing task data including: task IDs, titles, content,
        status (0=incomplete, 1=completed), priority (0-5), due dates, timezone,
        tags, projectId, and other task metadata.
    """
    try:
        access_token = get_ticktick_access_token()
        tasks_data = await get_ticktick_tasks(access_token, list_id=list_id)
        if tasks_data and "tasks" in tasks_data:
            # The /project/{list_id}/data endpoint returns a dict with "tasks" and "sprint"
            import json

            return json.dumps(tasks_data["tasks"], indent=2)
        import json

        return json.dumps(tasks_data, indent=2) if tasks_data else "[]"
    except ValueError as e:
        logger.error(f"Error in get_tasks_by_list_resource: {e}")
        return f"Error: {e}. Please ensure TICKTICK_ACCESS_TOKEN is set."


@mcp.resource("ticktick://projects")
async def get_all_projects_resource() -> str:
    """
    Get all TickTick projects (also called 'lists' in the TickTick UI) available
    to the authenticated user.

    Projects act like folders/containers - every task in TickTick must belong to
    exactly one project. The Inbox is a special project that is currently
    inaccessible via this MCP server.

    Returns:
        JSON string containing project data including: project IDs, names,
        sortOrder, viewMode, permission, color, closed status, and other metadata.
        Project IDs can be used with other tools and resources to manage tasks
        within those projects.
    """
    try:
        access_token = get_ticktick_access_token()
        projects = await get_ticktick_projects(access_token)
        import json

        return json.dumps(projects, indent=2) if projects else "[]"
    except ValueError as e:
        logger.error(f"Error in get_all_projects_resource: {e}")
        return f"Error: {e}. Please ensure TICKTICK_ACCESS_TOKEN is set."


# --- Tool Definitions ---
# Tools allow LLMs to perform actions (create, update, complete tasks)


@mcp.tool(
    name="list_projects",
    description="List all TickTick projects (also called 'lists' in the TickTick UI). Projects act like folders/containers - every task in TickTick must belong to exactly one project. Returns project IDs, names, and metadata. Note: The Inbox is a special project that is currently inaccessible via this MCP server.",
)
async def list_projects() -> dict[str, Any]:
    """
    Retrieve all TickTick projects (also called 'lists' in the UI) for the authenticated user.

    Projects act like folders/containers - every task in TickTick must belong to exactly
    one project. The Inbox is a special project that is currently inaccessible via
    this MCP server.

    Returns:
        Dictionary containing a list of projects with their IDs, names, sortOrder,
        viewMode, permission, color, closed status, and other metadata. Each project
        can be used to create tasks or retrieve tasks via other tools.
    """
    try:
        access_token = get_ticktick_access_token()
        projects = await get_ticktick_projects(access_token)
        return {"projects": projects if projects else [], "count": len(projects) if projects else 0}
    except ValueError as e:
        logger.error(f"Error listing projects: {e}")
        return {"error": str(e), "projects": [], "count": 0}


@mcp.tool(
    name="list_tasks",
    description="List all tasks in a specific TickTick project (also called a 'list' in the UI). Projects act as containers - every task belongs to exactly one project. Returns task details including IDs, titles, status (0=incomplete, 1=completed), priority (0-5), due dates, content, tags, and other metadata.",
)
async def list_tasks(
    project_id: str = Field(
        description="The ID of the project (also called 'list' in UI) to retrieve tasks from. Projects act like folders - every task belongs to exactly one project. Use list_projects tool to find available project IDs. Note: The Inbox project is currently inaccessible via this MCP server."
    ),
) -> dict[str, Any]:
    """
    Retrieve all tasks from a specific TickTick project (also called 'list' in the UI).

    Projects act like folders/containers - every task belongs to exactly one project.
    The Inbox is a special project that is currently inaccessible via this MCP server.

    Args:
        project_id: The ID of the project/list to retrieve tasks from.
                   Use list_projects tool to find available project IDs.

    Returns:
        Dictionary containing:
        - project_id: The project ID queried
        - tasks: Array of task objects with details including:
          * id: Task ID (needed for updating/completing tasks)
          * title: Task title/name
          * content: Task description/content (can include markdown)
          * status: Task status (0=incomplete, 1=completed)
          * priority: Priority level (0-5, 0=normal, higher is more urgent)
          * dueDate: Due date if set (ISO 8601 format)
          * timeZone: Timezone for the task
          * isAllDay: Whether task is all-day
          * tags: Array of tag strings
          * projectId: The project this task belongs to
          * And other task metadata
        - count: Total number of tasks
        - completed: Number of completed tasks (status=1)
        - incomplete: Number of incomplete tasks (status=0)
    """
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
    description="Create a new task in a TickTick project (also called 'list' in the UI). Every task must belong to exactly one project - you cannot create a task without specifying a project. Returns the created task with its ID, title, projectId, status, priority, and other fields that can be used for updates or completion.",
)
async def create_task(
    project_id: str = Field(
        description="The ID of the project (also called 'list' in UI) where the task should be created. Every task must belong to exactly one project - this is required. Use list_projects tool to find available project IDs. Note: The Inbox project is currently inaccessible via this MCP server."
    ),
    title: str = Field(description="The title/name of the task (required)."),
    content: str = Field(
        default="", description="Optional description or content for the task. Can include markdown formatting."
    ),
    priority: int = Field(
        default=0,
        description="Priority level from 0-5 (default: 0). Higher numbers indicate higher priority. 0=normal, 1-5=increasing priority.",
    ),
    due_date: str | None = Field(
        default=None,
        description="Optional due date in ISO 8601 format (e.g., '2024-12-31T23:59:59Z'). Can include timezone information.",
    ),
) -> dict[str, Any]:
    """
    Create a new task in a TickTick project (also called 'list' in the UI).

    Every task must belong to exactly one project - you cannot create a task without
    specifying a project. The Inbox is a special project that is currently
    inaccessible via this MCP server.

    Args:
        project_id: The ID of the project/list where the task should be created.
                   Every task must belong to exactly one project - this is required.
                   Use list_projects tool to find available project IDs.
        title: The title/name of the task (required).
        content: Optional description or content for the task. Can include markdown formatting.
        priority: Priority level from 0-5 (default: 0). 0=normal, 1-5=increasing priority.
        due_date: Optional due date in ISO 8601 format (e.g., "2024-12-31T23:59:59Z").
                 Can include timezone information.

    Returns:
        Dictionary containing:
        - success: Boolean indicating if creation succeeded
        - task: The created task object with id, title, projectId, status (0=incomplete),
          priority, and other fields that can be used with complete_task tool
        - message: Success message with task title and project ID
    """
    try:
        access_token = get_ticktick_access_token()
        task_data = {
            "projectId": project_id,
            "title": title,
            "priority": max(0, min(5, priority)),  # Clamp between 0-5
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


@mcp.tool(
    name="update_task",
    description="Update an existing task in a TickTick project. This tool allows modification of a task's title, content, priority, due date, and other fields. Returns the updated task details.",
)
async def update_task(
    task_id: str = Field(description="The ID of the task to update. Obtain this from list_tasks."),
    project_id: str = Field(
        description="The ID of the project (also called 'list' in UI) containing the task. Obtain this from list_projects."
    ),
    title: str | None = Field(default=None, description="Optional new title/name for the task."),
    content: str | None = Field(
        default=None, description="Optional new description or content for the task. Can include markdown formatting."
    ),
    priority: int | None = Field(
        default=None, description="Optional new priority level from 0-5. Higher numbers indicate higher priority."
    ),
    due_date: str | None = Field(
        default=None,
        description="Optional new due date in ISO 8601 format (e.g., '2024-12-31T23:59:59Z'). Set to '' or None to clear.",
    ),
    status: int | None = Field(
        default=None,
        description="Optional new status for the task (0=incomplete, 1=completed). Use complete_task tool to mark as complete.",
    ),
    tags: list[str] | None = Field(default=None, description="Optional list of tags to associate with the task."),  # noqa: B008
) -> dict[str, Any]:
    """
    Update an existing task in a TickTick project.

    This tool allows modification of a task's title, content, priority, due date,
    and other fields. It's crucial to ensure all existing fields of the task are
    included in the update payload to prevent accidental data loss, as per TickTick API behavior.

    Args:
        task_id: The ID of the task to update.
        project_id: The ID of the project containing the task.
        title: Optional new title/name for the task.
        content: Optional new description or content for the task.
        priority: Optional new priority level (0-5).
        due_date: Optional new due date in ISO 8601 format.
        status: Optional new status (0=incomplete, 1=completed).
        tags: Optional list of tags.

    Returns:
        Dictionary containing:
        - success: Boolean indicating if the update succeeded
        - message: Success message
        - task: The updated task object
        - error: Error message if the update failed
    """
    try:
        access_token = get_ticktick_access_token()

        # Extract actual values from FieldInfo if needed (for direct function calls in tests)
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
    description="Mark a task as complete. Returns the updated task details.",
)
async def complete_task(
    task_id: str = Field(
        description="The ID of the task to complete. Every task belongs to exactly one project. Use list_tasks to find task IDs for tasks in a specific project."
    ),
    project_id: str = Field(
        description="The ID of the project (also called 'list' in UI) containing the task. Every task must belong to exactly one project. Use list_projects to find available project IDs."
    ),
) -> dict[str, Any]:
    """
    Mark a task as completed in TickTick by setting its status to 1 (completed).

    Every task belongs to exactly one project. You need both the task ID and project ID
    to complete a task. The Inbox is a special project that is currently inaccessible
    via this MCP server.

    Args:
        task_id: The ID of the task to complete. Every task belongs to exactly one project.
                Use list_tasks to find task IDs for tasks in a specific project.
        project_id: The ID of the project (also called 'list' in UI) containing the task.
                    Every task must belong to exactly one project.
                    Use list_projects to find available project IDs.

    Returns:
        Dictionary containing:
        - success: Boolean indicating if completion succeeded
        - message: Success message with task title
        - task: Updated task object with status=1 (completed)
        - error: Error message if the update failed
    """
    try:
        access_token = get_ticktick_access_token()

        new_task_data = {"status": 1}  # Set status to 1 for completion

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


# At the end of the file, create the ASGI application instance for HTTP mode
# This is used when running via uvicorn (Docker detached mode)
mcp_app = mcp.streamable_http_app()

# If run directly with --stdio flag, run in stdio mode instead
# This allows Gemini CLI to auto-start the server via Docker with stdio transport
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        mcp.run(transport="stdio")
