"""SDK task operation tests.

Sociable: tests run the actual SDK and httpx code paths. respx
intercepts only the outbound TickTick HTTPS calls.
"""

import httpx
import pytest
import respx

from ticktick.sdk import tasks
from ticktick.sdk.client import APIError, TickTickClient


@respx.mock
async def test_list_tasks_returns_tasks_with_status_summary():
    respx.get("https://api.ticktick.com/open/v1/project/p1/data").mock(
        return_value=httpx.Response(200, json={
            "tasks": [
                {"id": "t1", "title": "open one", "status": 0},
                {"id": "t2", "title": "done", "status": 2},
                {"id": "t3", "title": "open two", "status": 0},
            ]
        })
    )
    result = await tasks.list_tasks(TickTickClient(token="t"), "p1")
    assert result["count"] == 3
    assert result["completed"] == 1
    assert result["incomplete"] == 2
    assert result["project_id"] == "p1"


@respx.mock
async def test_list_tasks_handles_empty_project():
    respx.get("https://api.ticktick.com/open/v1/project/p1/data").mock(
        return_value=httpx.Response(200, json={"tasks": []})
    )
    result = await tasks.list_tasks(TickTickClient(token="t"), "p1")
    assert result == {"project_id": "p1", "tasks": [], "count": 0, "completed": 0, "incomplete": 0}


@respx.mock
async def test_get_task_returns_task_dict():
    respx.get("https://api.ticktick.com/open/v1/project/p1/task/t1").mock(
        return_value=httpx.Response(200, json={"id": "t1", "title": "X"})
    )
    result = await tasks.get_task(TickTickClient(token="t"), "p1", "t1")
    assert result == {"id": "t1", "title": "X"}


@respx.mock
async def test_create_task_posts_with_title_and_priority():
    route = respx.post("https://api.ticktick.com/open/v1/task").mock(
        return_value=httpx.Response(200, json={"id": "new", "title": "Buy milk"})
    )
    result = await tasks.create_task(
        TickTickClient(token="t"),
        project_id="p1",
        title="Buy milk",
        priority=3,
    )
    assert result["id"] == "new"
    body = route.calls[0].request.content
    assert b"Buy milk" in body
    assert b'"projectId":"p1"' in body
    assert b'"priority":3' in body


@respx.mock
async def test_create_task_clamps_priority_into_zero_to_five():
    route = respx.post("https://api.ticktick.com/open/v1/task").mock(
        return_value=httpx.Response(200, json={"id": "new"})
    )
    await tasks.create_task(
        TickTickClient(token="t"), project_id="p1", title="X", priority=99,
    )
    assert b'"priority":5' in route.calls[0].request.content

    await tasks.create_task(
        TickTickClient(token="t"), project_id="p1", title="X", priority=-3,
    )
    assert b'"priority":0' in route.calls[1].request.content


@respx.mock
async def test_create_task_omits_optional_fields_when_none():
    route = respx.post("https://api.ticktick.com/open/v1/task").mock(
        return_value=httpx.Response(200, json={"id": "new"})
    )
    await tasks.create_task(TickTickClient(token="t"), "p1", "X")
    body = route.calls[0].request.content
    assert b'"dueDate"' not in body
    assert b'"reminders"' not in body
    assert b'"completedTime"' not in body


@respx.mock
async def test_create_task_includes_reminders_when_provided():
    route = respx.post("https://api.ticktick.com/open/v1/task").mock(
        return_value=httpx.Response(200, json={"id": "new"})
    )
    await tasks.create_task(
        TickTickClient(token="t"), "p1", "X",
        reminders=["TRIGGER:-PT30M"],
    )
    assert b"TRIGGER:-PT30M" in route.calls[0].request.content


@respx.mock
async def test_update_task_preserves_untouched_fields():
    """Fetches existing task, merges new values, preserves old ones."""
    respx.get("https://api.ticktick.com/open/v1/project/p1/task/t1").mock(
        return_value=httpx.Response(200, json={
            "id": "t1",
            "projectId": "p1",
            "title": "Original",
            "content": "Original content",
            "priority": 3,
            "status": 0,
            "tags": ["work"],
        })
    )
    update = respx.post("https://api.ticktick.com/open/v1/task/t1").mock(
        return_value=httpx.Response(200, json={"id": "t1", "title": "New title"})
    )
    await tasks.update_task(
        TickTickClient(token="t"), "p1", "t1", title="New title",
    )
    body = update.calls[0].request.content
    assert b"New title" in body
    assert b"Original content" in body  # preserved
    assert b'"priority":3' in body  # preserved
    assert b"work" in body  # preserved tag


@respx.mock
async def test_update_task_raises_when_task_not_found():
    respx.get("https://api.ticktick.com/open/v1/project/p1/task/missing").mock(
        return_value=httpx.Response(200, json=None)
    )
    with pytest.raises(APIError):
        await tasks.update_task(TickTickClient(token="t"), "p1", "missing", title="X")


@respx.mock
async def test_complete_task_sets_status_to_2():
    respx.get("https://api.ticktick.com/open/v1/project/p1/task/t1").mock(
        return_value=httpx.Response(200, json={
            "id": "t1", "projectId": "p1", "title": "X", "status": 0,
        })
    )
    update = respx.post("https://api.ticktick.com/open/v1/task/t1").mock(
        return_value=httpx.Response(200, json={"id": "t1", "status": 2})
    )
    await tasks.complete_task(TickTickClient(token="t"), "p1", "t1")
    assert b'"status":2' in update.calls[0].request.content


@respx.mock
async def test_delete_task_calls_delete_endpoint():
    route = respx.delete("https://api.ticktick.com/open/v1/project/p1/task/t1").mock(
        return_value=httpx.Response(200)
    )
    await tasks.delete_task(TickTickClient(token="t"), "p1", "t1")
    assert route.called
