from mcp.server.fastmcp import FastMCP
import httpx # Required for making HTTP requests to TickTick API
import os # For environment variables like API keys
import logging # For proper logging to stderr
from typing import Any, Dict, List, Optional
from pydantic import Field

# Initialize logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
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
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any] | List[Dict[str, Any]] | None:
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
            response.raise_for_status() # Raise an exception for HTTP errors
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


# TickTick API Interaction Functions (wrappers around make_ticktick_request)

async def get_ticktick_tasks(access_token: str, list_id: str) -> List[Dict[str, Any]] | None:
    """Fetches tasks from a specific TickTick list (project)."""
    endpoint = f"project/{list_id}/data"
    tasks = await make_ticktick_request("GET", endpoint, access_token)
    return tasks

async def get_ticktick_projects(access_token: str) -> List[Dict[str, Any]] | None:
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
async def list_projects() -> Dict[str, Any]:
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
        return {
            "projects": projects if projects else [],
            "count": len(projects) if projects else 0
        }
    except ValueError as e:
        logger.error(f"Error listing projects: {e}")
        return {"error": str(e), "projects": [], "count": 0}

@mcp.tool(
    name="list_tasks",
    description="List all tasks in a specific TickTick project (also called a 'list' in the UI). Projects act as containers - every task belongs to exactly one project. Returns task details including IDs, titles, status (0=incomplete, 1=completed), priority (0-5), due dates, content, tags, and other metadata.",
)
async def list_tasks(
    project_id: str = Field(description="The ID of the project (also called 'list' in UI) to retrieve tasks from. Projects act like folders - every task belongs to exactly one project. Use list_projects tool to find available project IDs. Note: The Inbox project is currently inaccessible via this MCP server.")
) -> Dict[str, Any]:
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
                "incomplete": sum(1 for t in tasks if t.get("status") == 0)
            }
        return {
            "project_id": project_id,
            "tasks": [],
            "count": 0,
            "completed": 0,
            "incomplete": 0
        }
    except ValueError as e:
        logger.error(f"Error listing tasks: {e}")
        return {"error": str(e), "project_id": project_id, "tasks": [], "count": 0}

@mcp.tool(
    name="create_task",
    description="Create a new task in a TickTick project (also called 'list' in the UI). Every task must belong to exactly one project - you cannot create a task without specifying a project. Returns the created task with its ID, title, projectId, status, priority, and other fields that can be used for updates or completion.",
)
async def create_task(
    project_id: str = Field(description="The ID of the project (also called 'list' in UI) where the task should be created. Every task must belong to exactly one project - this is required. Use list_projects tool to find available project IDs. Note: The Inbox project is currently inaccessible via this MCP server."),
    title: str = Field(description="The title/name of the task (required)."),
    content: str = Field(default="", description="Optional description or content for the task. Can include markdown formatting."),
    priority: int = Field(default=0, description="Priority level from 0-5 (default: 0). Higher numbers indicate higher priority. 0=normal, 1-5=increasing priority."),
    due_date: Optional[str] = Field(default=None, description="Optional due date in ISO 8601 format (e.g., '2024-12-31T23:59:59Z'). Can include timezone information.")
) -> Dict[str, Any]:
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
            "priority": max(0, min(5, priority))  # Clamp between 0-5
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
                "message": f"Task '{title}' created successfully in project {project_id}"
            }
        return {
            "success": False,
            "error": "Failed to create task",
            "task": None
        }
    except ValueError as e:
        logger.error(f"Error creating task: {e}")
        return {"success": False, "error": str(e), "task": None}

@mcp.tool(
    name="update_task",
    description="Update an existing task in a TickTick project. This tool allows modification of a task's title, content, priority, due date, and other fields. Returns the updated task details.",
)
async def update_task(
    task_id: str = Field(description="The ID of the task to update. Obtain this from list_tasks."),
    project_id: str = Field(description="The ID of the project (also called 'list' in UI) containing the task. Obtain this from list_projects."),
    title: Optional[str] = Field(default=None, description="Optional new title/name for the task."),
    content: Optional[str] = Field(default=None, description="Optional new description or content for the task. Can include markdown formatting."),
    priority: Optional[int] = Field(default=None, description="Optional new priority level from 0-5. Higher numbers indicate higher priority."),
    due_date: Optional[str] = Field(default=None, description="Optional new due date in ISO 8601 format (e.g., '2024-12-31T23:59:59Z'). Set to '' or None to clear."),
    status: Optional[int] = Field(default=None, description="Optional new status for the task (0=incomplete, 1=completed). Use complete_task tool to mark as complete."),
    tags: Optional[List[str]] = Field(default=None, description="Optional list of tags to associate with the task.")
) -> Dict[str, Any]:
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
        
        # 1. Retrieve the existing task to preserve all fields
        tasks_data = await get_ticktick_tasks(access_token, list_id=project_id)
        if not tasks_data or "tasks" not in tasks_data:
            return {"success": False, "error": f"Could not retrieve tasks for project {project_id}"}
        
        existing_task = next((t for t in tasks_data["tasks"] if t.get("id") == task_id), None)
        if not existing_task:
            return {"success": False, "error": f"Task {task_id} not found in project {project_id}"}
        
        # 2. Prepare the update payload, preserving existing fields and updating specified ones
        update_payload = existing_task.copy()
        
        if title is not None:
            update_payload["title"] = title
        if content is not None:
            update_payload["content"] = content
        if priority is not None:
            update_payload["priority"] = max(0, min(5, priority)) # Clamp between 0-5
        if due_date is not None:
            update_payload["dueDate"] = due_date
        if status is not None:
            update_payload["status"] = status
        if tags is not None:
            update_payload["tags"] = tags
        
        # The API requires id and projectId in the payload as well
        update_payload["id"] = task_id
        update_payload["projectId"] = project_id

        # 3. Make the API request
        result = await make_ticktick_request("POST", f"task/{task_id}", access_token, data=update_payload)
        
        if result:
            return {
                "success": True,
                "message": f"Task '{update_payload.get('title', task_id)}' updated successfully",
                "task": result
            }
        return {"success": False, "error": "Failed to update task", "task": None}
    except ValueError as e:
        logger.error(f"Error updating task: {e}")
        return {"success": False, "error": str(e), "task": None}


async def complete_task(
    task_id: str = Field(description="The ID of the task to complete. Every task belongs to exactly one project. Use list_tasks to find task IDs for tasks in a specific project."),
    project_id: str = Field(description="The ID of the project (also called 'list' in UI) containing the task. Every task must belong to exactly one project. Use list_projects to find available project IDs.")
) -> Dict[str, Any]:
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
        - task: Updated task object with status=1 (completed) and other fields
    """
    try:
        access_token = get_ticktick_access_token()
        # First get the current task to preserve all fields
        tasks_data = await get_ticktick_tasks(access_token, list_id=project_id)
        if not tasks_data or "tasks" not in tasks_data:
            return {"success": False, "error": "Could not retrieve task data"}
        
        task = next((t for t in tasks_data["tasks"] if t.get("id") == task_id), None)
        if not task:
            return {"success": False, "error": f"Task {task_id} not found in project {project_id}"}
        
        # Update task with status=1 (completed), preserving all other fields
        task["status"] = 1
        result = await make_ticktick_request("POST", f"task/{task_id}", access_token, data=task)
        
        if result:
            return {
                "success": True,
                "message": f"Task '{task.get('title', task_id)}' marked as completed",
                "task": result
            }
        return {"success": False, "error": "Failed to update task"}
    except ValueError as e:
        logger.error(f"Error completing task: {e}")
        return {"success": False, "error": str(e)}

# At the end of the file, create the ASGI application instance for HTTP mode
# This is used when running via uvicorn (Docker detached mode)
mcp_app = mcp.streamable_http_app()

# If run directly with --stdio flag, run in stdio mode instead
# This allows Gemini CLI to auto-start the server via Docker with stdio transport
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        mcp.run(transport="stdio")


