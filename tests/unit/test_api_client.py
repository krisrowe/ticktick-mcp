import json
import os
from unittest.mock import patch

import pytest
import respx
from httpx import Response

from ticktick.sdk.client import TICKTICK_API_BASE, USER_AGENT, request
from ticktick.sdk.projects import list_projects
from ticktick.sdk.tasks import list_tasks, update_task


@pytest.fixture
def mock_token():
    with patch("ticktick.sdk.client.get_access_token", return_value="test_token"):
        yield


@pytest.mark.asyncio
@respx.mock
async def test_ticktick_request_get_success(mock_token):
    """
    Tests that request successfully makes a GET request
    with the correct headers and returns the JSON response.
    """
    # Define the mock route
    mock_route = respx.get(f"{TICKTICK_API_BASE}/project").mock(
        return_value=Response(200, json=[{"id": "123", "name": "Test Project"}])
    )

    # Call the function under test
    response_data = await request(method="GET", endpoint="project")

    # Assertions
    assert mock_route.called
    assert response_data == [{"id": "123", "name": "Test Project"}]

    # Check that the correct headers were sent
    request_call = mock_route.calls.last.request
    assert request_call.headers["authorization"] == "Bearer test_token"
    assert request_call.headers["user-agent"] == USER_AGENT
    assert request_call.headers["content-type"] == "application/json"


@pytest.mark.asyncio
@respx.mock
async def test_ticktick_request_handle_error(mock_token):
    """
    Tests that request returns None when an HTTP error occurs.
    """
    # Define the mock route to return a 500 error
    mock_route = respx.get(f"{TICKTICK_API_BASE}/project").mock(return_value=Response(500))

    # Call the function under test
    response_data = await request(method="GET", endpoint="project")

    # Assertion
    assert mock_route.called
    assert response_data is None


@pytest.mark.asyncio
@respx.mock
async def test_ticktick_request_post_success(mock_token):
    """
    Tests that request successfully makes a POST request
    with a JSON payload.
    """
    post_data = {"name": "New Project"}

    # Define the mock route
    mock_route = respx.post(f"{TICKTICK_API_BASE}/project").mock(
        return_value=Response(201, json={"id": "456", "name": "New Project"})
    )

    # Call the function under test
    response_data = await request(
        method="POST", endpoint="project", data=post_data
    )

    # Assertions
    assert mock_route.called
    assert response_data == {"id": "456", "name": "New Project"}

    # Check the payload
    request_call = mock_route.calls.last.request
    request_payload = json.loads(request_call.content)
    assert request_payload == post_data


@pytest.mark.asyncio
@respx.mock
async def test_list_projects(mock_token):
    """
    Tests that list_projects successfully retrieves a list of projects.
    """
    mock_projects = [
        {"id": "proj1", "name": "Project 1", "sortOrder": 1},
        {"id": "proj2", "name": "Project 2", "sortOrder": 2},
    ]

    mock_route = respx.get(f"{TICKTICK_API_BASE}/project").mock(return_value=Response(200, json=mock_projects))

    result = await list_projects()

    assert mock_route.called
    assert result == mock_projects
    request_call = mock_route.calls.last.request
    assert request_call.headers["authorization"] == "Bearer test_token"


@pytest.mark.asyncio
@respx.mock
async def test_list_projects_error(mock_token):
    """
    Tests that list_projects returns empty list when an error occurs.
    """
    mock_route = respx.get(f"{TICKTICK_API_BASE}/project").mock(return_value=Response(500))

    result = await list_projects()

    assert mock_route.called
    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_list_tasks(mock_token):
    """
    Tests that list_tasks successfully retrieves tasks from a project.
    """
    mock_tasks_data = {
        "tasks": [
            {"id": "task1", "title": "Task 1", "projectId": "proj1", "status": 0},
            {"id": "task2", "title": "Task 2", "projectId": "proj1", "status": 2},
        ],
        "sprint": None,
    }

    mock_route = respx.get(f"{TICKTICK_API_BASE}/project/proj1/data").mock(
        return_value=Response(200, json=mock_tasks_data)
    )

    result = await list_tasks(project_id="proj1")

    assert mock_route.called
    assert result["project_id"] == "proj1"
    assert result["tasks"] == mock_tasks_data["tasks"]
    assert result["count"] == 2
    assert result["completed"] == 1
    assert result["incomplete"] == 1
    
    request_call = mock_route.calls.last.request
    assert request_call.headers["authorization"] == "Bearer test_token"


@pytest.mark.asyncio
@respx.mock
async def test_get_task_details(mock_token):
    """
    Tests getting details of a single task by task ID using request().
    """
    mock_task = {
        "id": "task123",
        "title": "Test Task",
        "projectId": "proj1",
        "status": 0,
        "priority": 2,
        "content": "Task description",
    }

    mock_route = respx.get(f"{TICKTICK_API_BASE}/task/task123").mock(return_value=Response(200, json=mock_task))

    result = await request(method="GET", endpoint="task/task123")

    assert mock_route.called
    assert result == mock_task
    request_call = mock_route.calls.last.request
    assert request_call.headers["authorization"] == "Bearer test_token"


@pytest.mark.asyncio
@respx.mock
async def test_update_task(mock_token):
    """
    Tests that update_task successfully updates a task with new data.
    """
    # Mock the GET request to fetch existing task details
    existing_task = {
        "id": "task123",
        "title": "Original Title",
        "projectId": "proj1",
        "status": 0,
        "priority": 1,
        "content": "Original content",
    }

    # Mock the POST request to update the task
    updated_task = {
        "id": "task123",
        "title": "Updated Title",
        "projectId": "proj1",
        "status": 0,
        "priority": 2,
        "content": "Updated content",
    }

    # Note: update_task calls get_task which uses project/{project_id}/task/{task_id}
    get_route = respx.get(f"{TICKTICK_API_BASE}/project/proj1/task/task123").mock(return_value=Response(200, json=existing_task))

    post_route = respx.post(f"{TICKTICK_API_BASE}/task/task123").mock(return_value=Response(200, json=updated_task))

    result = await update_task(
        task_id="task123",
        project_id="proj1",
        title="Updated Title",
        content="Updated content",
        priority=2,
    )

    # Verify both requests were made
    assert get_route.called
    assert post_route.called

    # Verify the result
    assert result["success"] is True
    assert result["task"] == updated_task
    assert "updated successfully" in result["message"].lower()

    # Verify auth headers were sent
    get_request = get_route.calls.last.request
    post_request = post_route.calls.last.request
    assert get_request.headers["authorization"] == "Bearer test_token"
    assert post_request.headers["authorization"] == "Bearer test_token"

    # Verify the update payload includes merged data
    update_payload = json.loads(post_request.content)
    assert update_payload["title"] == "Updated Title"
    assert update_payload["content"] == "Updated content"
    assert update_payload["priority"] == 2
    assert update_payload["projectId"] == "proj1"


@pytest.mark.asyncio
@respx.mock
async def test_update_task_error_fetching_existing(mock_token):
    """
    Tests that update_task handles errors when fetching existing task details.
    """
    get_route = respx.get(f"{TICKTICK_API_BASE}/project/proj1/task/task123").mock(return_value=Response(404))

    result = await update_task(task_id="task123", project_id="proj1", title="New Title")

    assert get_route.called
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
@respx.mock
async def test_update_task_error_updating(mock_token):
    """
    Tests that update_task handles errors when updating the task.
    """
    existing_task = {
        "id": "task123",
        "title": "Original Title",
        "projectId": "proj1",
        "status": 0,
    }

    get_route = respx.get(f"{TICKTICK_API_BASE}/project/proj1/task/task123").mock(return_value=Response(200, json=existing_task))

    post_route = respx.post(f"{TICKTICK_API_BASE}/task/task123").mock(return_value=Response(500))

    result = await update_task(task_id="task123", project_id="proj1", title="New Title")

    assert get_route.called
    assert post_route.called
    assert result["success"] is False
    assert "error" in result