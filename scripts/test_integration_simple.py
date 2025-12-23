#!/usr/bin/env python3
"""
Simple integration test script that tests MCP server functions directly
without needing to deal with HTTP/SSE complexity.
"""

import asyncio
import os
import sys

from server import (
    get_ticktick_projects,
    get_ticktick_tasks,
    make_ticktick_request,
    update_task,
)


async def test_list_projects():
    """Test getting list of projects."""
    print("Testing list_projects...")
    token = os.getenv("TICKTICK_ACCESS_TOKEN")
    if not token:
        print("❌ TICKTICK_ACCESS_TOKEN not set")
        return None

    projects = await get_ticktick_projects(token)
    if projects:
        print(f"✅ Found {len(projects)} projects")
        if projects:
            print(f"   First project: {projects[0].get('name', 'N/A')} (ID: {projects[0].get('id', 'N/A')})")
        return projects
    else:
        print("❌ Failed to get projects")
        return None


async def test_list_tasks(project_id: str):
    """Test getting list of tasks in a project."""
    print(f"\nTesting list_tasks for project {project_id}...")
    token = os.getenv("TICKTICK_ACCESS_TOKEN")
    if not token:
        print("❌ TICKTICK_ACCESS_TOKEN not set")
        return None

    tasks_data = await get_ticktick_tasks(token, project_id)
    if tasks_data and "tasks" in tasks_data:
        tasks = tasks_data["tasks"]
        print(f"✅ Found {len(tasks)} tasks")
        print(f"   Completed: {sum(1 for t in tasks if t.get('status') == 1)}")
        print(f"   Incomplete: {sum(1 for t in tasks if t.get('status') == 0)}")
        if tasks:
            print(f"   First task: {tasks[0].get('title', 'N/A')} (ID: {tasks[0].get('id', 'N/A')})")
        return tasks_data
    else:
        print("❌ Failed to get tasks")
        return None


async def test_get_task_details(task_id: str):
    """Test getting details of a single task."""
    print(f"\nTesting get_task_details for task {task_id}...")
    token = os.getenv("TICKTICK_ACCESS_TOKEN")
    if not token:
        print("❌ TICKTICK_ACCESS_TOKEN not set")
        return None

    task = await make_ticktick_request("GET", f"task/{task_id}", token)
    if task:
        print(f"✅ Retrieved task: {task.get('title', 'N/A')}")
        print(f"   Status: {'Completed' if task.get('status') == 1 else 'Incomplete'}")
        print(f"   Priority: {task.get('priority', 'N/A')}")
        return task
    else:
        print("❌ Failed to get task details")
        return None


async def test_update_task(task_id: str, project_id: str):
    """Test updating a task."""
    print(f"\nTesting update_task for task {task_id}...")
    token = os.getenv("TICKTICK_ACCESS_TOKEN")
    if not token:
        print("❌ TICKTICK_ACCESS_TOKEN not set")
        return None

    result = await update_task(
        task_id=task_id,
        project_id=project_id,
        title="Integration Test Update",
        priority=2,
    )

    if result and result.get("success"):
        print("✅ Task updated successfully")
        print(f"   Message: {result.get('message', 'N/A')}")
        return result
    else:
        print(f"❌ Failed to update task: {result.get('error', 'Unknown error')}")
        return None


async def main():
    """Run integration tests."""
    print("=" * 60)
    print("TickTick MCP Server Integration Tests")
    print("=" * 60)

    # Load token from .env if available
    if os.path.exists(".env"):
        from dotenv import load_dotenv

        load_dotenv()

    token = os.getenv("TICKTICK_ACCESS_TOKEN")
    if not token:
        print("\n❌ ERROR: TICKTICK_ACCESS_TOKEN not set")
        print("   Set it in your environment or .env file")
        sys.exit(1)

    # Test 1: List projects
    projects = await test_list_projects()
    if not projects:
        print("\n❌ Cannot continue without projects")
        sys.exit(1)

    # Test 2: List tasks (use first project)
    project_id = projects[0].get("id")
    if not project_id:
        print("\n❌ No project ID found")
        sys.exit(1)

    tasks_data = await test_list_tasks(project_id)
    if not tasks_data or not tasks_data.get("tasks"):
        print("\n⚠️  No tasks found, skipping task-specific tests")
        sys.exit(0)

    # Test 3: Get task details (use first task)
    task_id = tasks_data["tasks"][0].get("id")
    if task_id:
        await test_get_task_details(task_id)

        # Test 4: Update task (optional - comment out if you don't want to modify tasks)
        # Uncomment the next line to test task updates:
        # await test_update_task(task_id, project_id)

    print("\n" + "=" * 60)
    print("✅ Integration tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
