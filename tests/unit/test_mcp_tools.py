"""Tests for the MCP tools layer.

Tools are thin wrappers over the SDK facade. These tests verify the
wiring (each tool calls the right SDK method) and the error envelope
shape (auth/API errors come back as success=False rather than raising
out of the tool).
"""

import httpx
import respx

from ticktick.mcp import tools


@respx.mock
async def test_list_projects_returns_data_envelope(authenticated_user):
    respx.get("https://api.ticktick.com/open/v1/project").mock(
        return_value=httpx.Response(200, json=[{"id": "p1", "name": "Work"}])
    )
    result = await tools.list_projects()
    assert result["count"] == 1
    assert result["projects"][0]["name"] == "Work"


@respx.mock
async def test_list_projects_returns_error_envelope_on_auth_failure(authenticated_user):
    respx.get("https://api.ticktick.com/open/v1/project").mock(
        return_value=httpx.Response(401, json={"error": "unauthorized"})
    )
    result = await tools.list_projects()
    assert result["projects"] == []
    assert "error" in result


@respx.mock
async def test_create_task_round_trip(authenticated_user):
    respx.post("https://api.ticktick.com/open/v1/task").mock(
        return_value=httpx.Response(200, json={"id": "new", "title": "T"})
    )
    result = await tools.create_task(project_id="p1", title="T")
    assert result["success"] is True
    assert result["task"]["id"] == "new"


@respx.mock
async def test_create_task_returns_error_envelope_on_api_failure(authenticated_user):
    respx.post("https://api.ticktick.com/open/v1/task").mock(
        return_value=httpx.Response(500, text="server error")
    )
    result = await tools.create_task(project_id="p1", title="T")
    assert result["success"] is False
    assert result["task"] is None
    assert "error" in result


@respx.mock
async def test_delete_task_round_trip(authenticated_user):
    route = respx.delete("https://api.ticktick.com/open/v1/project/p1/task/t1").mock(
        return_value=httpx.Response(200)
    )
    result = await tools.delete_task("p1", "t1")
    assert result["success"] is True
    assert route.called


@respx.mock
async def test_complete_task_marks_status_2(authenticated_user):
    respx.get("https://api.ticktick.com/open/v1/project/p1/task/t1").mock(
        return_value=httpx.Response(200, json={
            "id": "t1", "projectId": "p1", "title": "X", "status": 0,
        })
    )
    update = respx.post("https://api.ticktick.com/open/v1/task/t1").mock(
        return_value=httpx.Response(200, json={"id": "t1", "status": 2})
    )
    result = await tools.complete_task("p1", "t1")
    assert result["success"] is True
    assert b'"status":2' in update.calls[0].request.content


@respx.mock
async def test_update_task_round_trip(authenticated_user):
    respx.get("https://api.ticktick.com/open/v1/project/p1/task/t1").mock(
        return_value=httpx.Response(200, json={
            "id": "t1", "projectId": "p1", "title": "Old", "status": 0,
        })
    )
    respx.post("https://api.ticktick.com/open/v1/task/t1").mock(
        return_value=httpx.Response(200, json={"id": "t1", "title": "New"})
    )
    result = await tools.update_task(project_id="p1", task_id="t1", title="New")
    assert result["success"] is True
    assert result["task"]["title"] == "New"
