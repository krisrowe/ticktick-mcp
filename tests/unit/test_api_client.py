import json

import pytest
import respx
from httpx import Response

from ticktick.sdk.client import TICKTICK_API_BASE, USER_AGENT, TickTickClient
from ticktick.sdk.projects import ProjectService
from ticktick.sdk.tasks import TaskService

TEST_TOKEN = "test_token"


@pytest.fixture
def client():
    return TickTickClient(TEST_TOKEN)


@pytest.fixture
def project_svc(client):
    return ProjectService(client)


@pytest.fixture
def task_svc(client):
    return TaskService(client)


@pytest.mark.asyncio
@respx.mock
async def test_ticktick_request_get_success(client):
    """
    Tests that request successfully makes a GET request
    with the correct headers and returns the JSON response.
    """
    mock_route = respx.get(f"{TICKTICK_API_BASE}/project").mock(
        return_value=Response(200, json=[{"id": "123", "name": "Test Project"}])
    )

    response_data = await client.request(method="GET", endpoint="project")

    assert mock_route.called
    assert response_data == [{"id": "123", "name": "Test Project"}]

    request_call = mock_route.calls.last.request
    assert request_call.headers["authorization"] == f"Bearer {TEST_TOKEN}"
    assert request_call.headers["user-agent"] == USER_AGENT
    assert request_call.headers["content-type"] == "application/json"


@pytest.mark.asyncio
@respx.mock
async def test_ticktick_request_handle_error(client):
    """
    Tests that request returns None when an HTTP error occurs.
    """
    mock_route = respx.get(f"{TICKTICK_API_BASE}/project").mock(return_value=Response(500))

    response_data = await client.request(method="GET", endpoint="project")

    assert mock_route.called
    assert response_data is None


@pytest.mark.asyncio
@respx.mock
async def test_ticktick_request_post_success(client):
    """
    Tests that request successfully makes a POST request
    with a JSON payload.
    """
    post_data = {"name": "New Project"}

    mock_route = respx.post(f"{TICKTICK_API_BASE}/project").mock(
        return_value=Response(201, json={"id": "456", "name": "New Project"})
    )

    response_data = await client.request(
        method="POST", endpoint="project", data=post_data
    )

    assert mock_route.called
    assert response_data == {"id": "456", "name": "New Project"}

    request_call = mock_route.calls.last.request
    request_payload = json.loads(request_call.content)
    assert request_payload == post_data


@pytest.mark.asyncio
@respx.mock
async def test_list_projects(project_svc):
    """
    Tests that list successfully retrieves a list of projects.
    """
    mock_projects = [
        {"id": "proj1", "name": "Project 1", "sortOrder": 1},
        {"id": "proj2", "name": "Project 2", "sortOrder": 2},
    ]

    mock_route = respx.get(f"{TICKTICK_API_BASE}/project").mock(return_value=Response(200, json=mock_projects))

    result = await project_svc.list()

    assert mock_route.called
    assert result == mock_projects
    request_call = mock_route.calls.last.request
    assert request_call.headers["authorization"] == f"Bearer {TEST_TOKEN}"


@pytest.mark.asyncio
@respx.mock
async def test_list_projects_error(project_svc):
    """
    Tests that list returns empty list when an error occurs.
    """
    mock_route = respx.get(f"{TICKTICK_API_BASE}/project").mock(return_value=Response(500))

    result = await project_svc.list()

    assert mock_route.called
    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_list_tasks(task_svc):
    """
    Tests that list successfully retrieves tasks from a project.
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

    result = await task_svc.list(project_id="proj1")

    assert mock_route.called
    assert result["project_id"] == "proj1"
    assert result["tasks"] == mock_tasks_data["tasks"]
    assert result["count"] == 2
    assert result["completed"] == 1
    assert result["incomplete"] == 1

    request_call = mock_route.calls.last.request
    assert request_call.headers["authorization"] == f"Bearer {TEST_TOKEN}"


@pytest.mark.asyncio
@respx.mock
async def test_get_task_details(client):
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

    result = await client.request(method="GET", endpoint="task/task123")

    assert mock_route.called
    assert result == mock_task
    request_call = mock_route.calls.last.request
    assert request_call.headers["authorization"] == f"Bearer {TEST_TOKEN}"


@pytest.mark.asyncio
@respx.mock
async def test_update_task(task_svc):
    """
    Tests that update successfully updates a task with new data.
    """
    existing_task = {
        "id": "task123",
        "title": "Original Title",
        "projectId": "proj1",
        "status": 0,
        "priority": 1,
        "content": "Original content",
    }

    updated_task = {
        "id": "task123",
        "title": "Updated Title",
        "projectId": "proj1",
        "status": 0,
        "priority": 2,
        "content": "Updated content",
    }

    get_route = respx.get(f"{TICKTICK_API_BASE}/project/proj1/task/task123").mock(return_value=Response(200, json=existing_task))
    post_route = respx.post(f"{TICKTICK_API_BASE}/task/task123").mock(return_value=Response(200, json=updated_task))

    result = await task_svc.update(
        task_id="task123",
        project_id="proj1",
        title="Updated Title",
        content="Updated content",
        priority=2,
    )

    assert get_route.called
    assert post_route.called

    assert result["success"] is True
    assert result["task"] == updated_task
    assert "updated successfully" in result["message"].lower()

    get_request = get_route.calls.last.request
    post_request = post_route.calls.last.request
    assert get_request.headers["authorization"] == f"Bearer {TEST_TOKEN}"
    assert post_request.headers["authorization"] == f"Bearer {TEST_TOKEN}"

    update_payload = json.loads(post_request.content)
    assert update_payload["title"] == "Updated Title"
    assert update_payload["content"] == "Updated content"
    assert update_payload["priority"] == 2
    assert update_payload["projectId"] == "proj1"


@pytest.mark.asyncio
@respx.mock
async def test_update_task_error_fetching_existing(task_svc):
    """
    Tests that update handles errors when fetching existing task details.
    """
    get_route = respx.get(f"{TICKTICK_API_BASE}/project/proj1/task/task123").mock(return_value=Response(404))

    result = await task_svc.update(task_id="task123", project_id="proj1", title="New Title")

    assert get_route.called
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
@respx.mock
async def test_update_task_error_updating(task_svc):
    """
    Tests that update handles errors when updating the task.
    """
    existing_task = {
        "id": "task123",
        "title": "Original Title",
        "projectId": "proj1",
        "status": 0,
    }

    get_route = respx.get(f"{TICKTICK_API_BASE}/project/proj1/task/task123").mock(return_value=Response(200, json=existing_task))
    post_route = respx.post(f"{TICKTICK_API_BASE}/task/task123").mock(return_value=Response(500))

    result = await task_svc.update(task_id="task123", project_id="proj1", title="New Title")

    assert get_route.called
    assert post_route.called
    assert result["success"] is False
    assert "error" in result
