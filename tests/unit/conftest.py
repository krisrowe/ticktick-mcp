"""Shared fixtures for unit tests.

Tests run with the real SDK code paths against the real httpx client.
The TickTick API is the only system boundary we mock — via respx —
because it's external. Everything inside the SDK runs unmodified.

User identity is set by establishing a UserRecord in the
``current_user`` ContextVar; the SDK reads its ``access_token`` from
``user.profile.access_token`` exactly as it does in production.

XDG paths (``XDG_DATA_HOME``, ``APP_USERS_PATH``, etc.) are pinned
to a per-test temp directory so no test reads or writes any real
filesystem state.
"""

from __future__ import annotations

import pytest

from mcp_app.context import current_user
from mcp_app.models import UserRecord

from ticktick import Profile  # noqa: F401  — kept for tests that import the model


@pytest.fixture(autouse=True)
def isolate_xdg(tmp_path, monkeypatch):
    """Redirect every XDG/data path the framework or SDK might read."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("APP_USERS_PATH", str(tmp_path / "users"))
    for sub in ("home", "config", "data", "cache", "users"):
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)


@pytest.fixture
def authenticated_user():
    """Set current_user to a test user with a valid TickTick token.

    Tests that exercise SDK methods or MCP tools rely on this fixture
    to satisfy the identity gate that mcp-app enforces in production.
    """
    # mcp-app stores the profile as a dict; the SDK reads access_token
    # from it directly. (In production, App.stdio()/middleware hydrate
    # this into a Profile instance via mcp_app.context.hydrate_profile,
    # but that's not required for SDK lookups.)
    user = UserRecord(
        email="alice@example.com",
        profile={"access_token": "test-ticktick-token"},
    )
    token = current_user.set(user)
    yield user
    current_user.reset(token)
