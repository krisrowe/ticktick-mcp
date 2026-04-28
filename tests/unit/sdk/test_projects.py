"""SDK project operation tests.

Sociable: real httpx client, real SDK logic, real Pydantic Profile.
The only mocked boundary is the TickTick API itself (respx).
"""

import httpx
import pytest
import respx

from ticktick.sdk import projects
from ticktick.sdk.client import APIError, AuthenticationError, TickTickClient


@respx.mock
async def test_list_projects_returns_list_from_api():
    respx.get("https://api.ticktick.com/open/v1/project").mock(
        return_value=httpx.Response(200, json=[
            {"id": "p1", "name": "Work", "kind": "TASK"},
            {"id": "p2", "name": "Personal", "kind": "TASK"},
        ])
    )
    result = await projects.list_projects(TickTickClient(token="t"))
    assert [p["name"] for p in result] == ["Work", "Personal"]


@respx.mock
async def test_list_projects_returns_empty_when_api_returns_empty():
    respx.get("https://api.ticktick.com/open/v1/project").mock(
        return_value=httpx.Response(200, json=[])
    )
    result = await projects.list_projects(TickTickClient(token="t"))
    assert result == []


@respx.mock
async def test_list_projects_sends_bearer_token():
    route = respx.get("https://api.ticktick.com/open/v1/project").mock(
        return_value=httpx.Response(200, json=[])
    )
    await projects.list_projects(TickTickClient(token="my-secret-token"))
    assert route.calls[0].request.headers["Authorization"] == "Bearer my-secret-token"


@respx.mock
async def test_list_projects_raises_authentication_error_on_401():
    respx.get("https://api.ticktick.com/open/v1/project").mock(
        return_value=httpx.Response(401, json={"error": "unauthorized"})
    )
    with pytest.raises(AuthenticationError):
        await projects.list_projects(TickTickClient(token="bad"))


@respx.mock
async def test_get_project_data_returns_full_project_with_tasks():
    respx.get("https://api.ticktick.com/open/v1/project/p1/data").mock(
        return_value=httpx.Response(200, json={
            "project": {"id": "p1", "name": "Work"},
            "tasks": [{"id": "t1", "title": "first"}],
        })
    )
    result = await projects.get_project_data(TickTickClient(token="t"), "p1")
    assert result["project"]["name"] == "Work"
    assert len(result["tasks"]) == 1


def test_client_rejects_empty_token():
    with pytest.raises(AuthenticationError):
        TickTickClient(token="")


@respx.mock
async def test_client_raises_api_error_on_500():
    respx.get("https://api.ticktick.com/open/v1/project").mock(
        return_value=httpx.Response(500, text="server exploded")
    )
    with pytest.raises(APIError):
        await projects.list_projects(TickTickClient(token="t"))
