"""TickTick SDK - Core library for TickTick API access.

This SDK provides programmatic access to the TickTick API. It can be used by:
- The ticktick CLI
- The ticktick MCP server
- Third-party applications

Example usage:
    from ticktick.sdk.client import TickTickClient
    from ticktick.sdk.projects import ProjectService
    from ticktick.sdk.tasks import TaskService

    # With a shared client
    client = TickTickClient(token="...")
    projects = ProjectService(client)
    tasks = TaskService(client)

    # Or directly with a token
    projects = ProjectService(token="...")
    tasks = TaskService(token="...")
"""

from .client import TickTickClient
from .projects import ProjectService
from .tasks import TaskService

__all__ = ["TickTickClient", "ProjectService", "TaskService"]
