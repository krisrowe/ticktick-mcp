"""TickTick SDK - Core library for TickTick API access.

This SDK provides programmatic access to the TickTick API. It can be used by:
- The ticktick CLI
- The ticktick MCP server
- Third-party applications

Example usage:
    from ticktick.sdk import projects, tasks

    # List all projects
    project_list = await projects.list_projects()

    # Create a task
    task = await tasks.create_task(project_id="abc123", title="My Task")
"""

from . import client
from . import projects
from . import tasks

__all__ = ["client", "projects", "tasks"]
