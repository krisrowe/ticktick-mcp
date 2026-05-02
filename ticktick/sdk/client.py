"""TickTick API HTTP client and SDK facade.

:class:`TickTickClient` is the low-level authenticated HTTP client.
:class:`TickTickSDK` is a stateless classmethod facade for MCP tools
— it reads the access token from mcp-app's ``current_user`` context
and delegates to the SDK modules.
"""

from __future__ import annotations

import logging
from importlib.metadata import version
from typing import Any

import httpx

logger = logging.getLogger(__name__)

TICKTICK_API_BASE = "https://api.ticktick.com/open/v1"
USER_AGENT = f"ticktick-access/{version('ticktick-access')}"


class TickTickError(Exception):
    """Base exception for TickTick API errors."""


class AuthenticationError(TickTickError):
    """Raised when the TickTick token is missing or rejected."""


class APIError(TickTickError):
    """Raised when the TickTick API returns a non-success status."""


class TickTickClient:
    """Authenticated HTTP client for the TickTick Open API."""

    def __init__(self, token: str):
        if not token:
            raise AuthenticationError(
                "No TickTick access token. Set the user's profile.access_token via:\n"
                "  ticktick-admin users add <email> --access-token <token>\n"
                "  ticktick-admin users update-profile <email> access_token <token>"
            )
        self._token = token

    async def request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Make an authenticated request. Returns parsed JSON or None.

        Raises :class:`AuthenticationError` on 401, :class:`APIError`
        on other non-success statuses.
        """
        headers = {
            "User-Agent": USER_AGENT,
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        url = f"{TICKTICK_API_BASE}/{endpoint}"

        async with httpx.AsyncClient() as http:
            response = await http.request(
                method, url, headers=headers, json=data, params=params, timeout=30.0,
            )

        if response.status_code == 401:
            raise AuthenticationError("TickTick rejected the access token (401)")
        if response.status_code >= 400:
            raise APIError(
                f"TickTick API {method} {endpoint} -> {response.status_code}: "
                f"{response.text[:200]}"
            )
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    async def get(self, endpoint: str, params: dict[str, Any] | None = None):
        return await self.request("GET", endpoint, params=params)

    async def post(self, endpoint: str, data: dict[str, Any] | None = None):
        return await self.request("POST", endpoint, data=data)

    async def delete(self, endpoint: str):
        return await self.request("DELETE", endpoint)


class TickTickSDK:
    """Stateless facade for MCP tools.

    Each classmethod resolves the current user's TickTick access token
    from mcp-app's ``current_user`` ContextVar, builds a fresh client,
    and delegates to a module-level SDK function. Tools call these
    methods; SDK modules stay free of identity concerns.
    """

    @classmethod
    def _client(cls) -> TickTickClient:
        from mcp_app.context import current_user

        user = current_user.get()
        profile = user.profile
        token = getattr(profile, "access_token", None) if profile else None
        if not token and isinstance(profile, dict):
            token = profile.get("access_token")
        return TickTickClient(token=token or "")

    @classmethod
    async def list_projects(cls) -> dict[str, Any]:
        from ticktick.sdk import projects

        items = await projects.list_projects(cls._client())
        return {"projects": items, "count": len(items)}

    @classmethod
    async def count_projects(cls) -> dict[str, Any]:
        from ticktick.sdk import projects

        return {"count": await projects.count_projects(cls._client())}

    @classmethod
    async def list_tasks(cls, project_id: str) -> dict[str, Any]:
        from ticktick.sdk import tasks

        return await tasks.list_tasks(cls._client(), project_id)

    @classmethod
    async def create_task(cls, project_id: str, title: str, **kwargs) -> dict[str, Any]:
        from ticktick.sdk import tasks

        result = await tasks.create_task(cls._client(), project_id, title, **kwargs)
        return {"success": True, "task": result, "message": f"Task '{title}' created"}

    @classmethod
    async def update_task(cls, project_id: str, task_id: str, **kwargs) -> dict[str, Any]:
        from ticktick.sdk import tasks

        result = await tasks.update_task(cls._client(), project_id, task_id, **kwargs)
        return {
            "success": True,
            "task": result,
            "message": f"Task {task_id} updated",
        }

    @classmethod
    async def complete_task(cls, project_id: str, task_id: str) -> dict[str, Any]:
        from ticktick.sdk import tasks

        result = await tasks.complete_task(cls._client(), project_id, task_id)
        title = (result or {}).get("title", task_id)
        return {
            "success": True,
            "task": result,
            "message": f"Task '{title}' marked completed",
        }

    @classmethod
    async def delete_task(cls, project_id: str, task_id: str) -> dict[str, Any]:
        from ticktick.sdk import tasks

        await tasks.delete_task(cls._client(), project_id, task_id)
        return {"success": True, "message": f"Task {task_id} deleted"}
