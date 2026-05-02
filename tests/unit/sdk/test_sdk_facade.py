"""Tests for the TickTickSDK classmethod facade.

Verifies the user-identity wiring: when current_user is set, the SDK
facade pulls the access_token from the user's profile and uses it
for outbound calls. This is the behavior MCP tools depend on.
"""

import httpx
import pytest
import respx

from mcp_app.context import current_user
from mcp_app.models import UserRecord

from ticktick.sdk.client import AuthenticationError, TickTickSDK


@respx.mock
async def test_facade_uses_token_from_current_user(authenticated_user):
    route = respx.get("https://api.ticktick.com/open/v1/project").mock(
        return_value=httpx.Response(200, json=[{"id": "p1", "name": "Work"}])
    )
    result = await TickTickSDK.list_projects()
    assert result == {"projects": [{"id": "p1", "name": "Work"}], "count": 1}
    assert route.calls[0].request.headers["Authorization"] == "Bearer test-ticktick-token"


@respx.mock
async def test_facade_isolates_users_by_distinct_tokens():
    """Two users hitting the SDK simultaneously do not share tokens."""
    route = respx.get("https://api.ticktick.com/open/v1/project").mock(
        return_value=httpx.Response(200, json=[])
    )

    alice = UserRecord(email="alice@example.com", profile={"access_token": "alice-token"})
    bob = UserRecord(email="bob@example.com", profile={"access_token": "bob-token"})

    tok_a = current_user.set(alice)
    try:
        await TickTickSDK.list_projects()
    finally:
        current_user.reset(tok_a)

    tok_b = current_user.set(bob)
    try:
        await TickTickSDK.list_projects()
    finally:
        current_user.reset(tok_b)

    assert route.calls[0].request.headers["Authorization"] == "Bearer alice-token"
    assert route.calls[1].request.headers["Authorization"] == "Bearer bob-token"


@respx.mock
async def test_facade_supports_dict_profile_for_unhydrated_records(monkeypatch):
    """If profile arrives as a raw dict (e.g. older record), SDK still extracts the token."""
    user = UserRecord(email="legacy@example.com", profile={"access_token": "raw-dict-token"})
    token = current_user.set(user)
    try:
        route = respx.get("https://api.ticktick.com/open/v1/project").mock(
            return_value=httpx.Response(200, json=[])
        )
        await TickTickSDK.list_projects()
        assert route.calls[0].request.headers["Authorization"] == "Bearer raw-dict-token"
    finally:
        current_user.reset(token)


async def test_facade_raises_when_profile_has_no_token():
    user = UserRecord(email="empty@example.com", profile={})
    token = current_user.set(user)
    try:
        with pytest.raises(AuthenticationError):
            await TickTickSDK.list_projects()
    finally:
        current_user.reset(token)


@respx.mock
async def test_facade_count_projects_returns_count_envelope(authenticated_user):
    respx.get("https://api.ticktick.com/open/v1/project").mock(
        return_value=httpx.Response(200, json=[
            {"id": "p1", "name": "Work"},
            {"id": "p2", "name": "Personal"},
        ])
    )
    assert await TickTickSDK.count_projects() == {"count": 2}


@respx.mock
async def test_facade_create_task_returns_success_envelope(authenticated_user):
    respx.post("https://api.ticktick.com/open/v1/task").mock(
        return_value=httpx.Response(200, json={"id": "new", "title": "Buy milk"})
    )
    result = await TickTickSDK.create_task("p1", "Buy milk", priority=1)
    assert result["success"] is True
    assert result["task"]["title"] == "Buy milk"
    assert "Buy milk" in result["message"]
