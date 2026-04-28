"""TickTick Access — CLI and MCP server for TickTick task management."""

from pydantic import BaseModel, Field
from mcp_app import App

import ticktick as _self
from ticktick.mcp import tools


__version__ = "0.5.0"


class Profile(BaseModel):
    """Per-user profile holding the TickTick OAuth access token.

    Field descriptions drive ``ticktick-admin users add --help`` output —
    they are the re-discovery path for operators who need to know what
    each field is for months after initial setup. Always include a
    ``Field(description=...)`` that states what the credential is and
    how to obtain it.
    """

    access_token: str = Field(
        description=(
            "TickTick OAuth access token. Obtain by running "
            "`ticktick auth login` locally — it walks the OAuth flow and "
            "prints the token. Or generate one yourself by registering an "
            "app at https://developer.ticktick.com/, setting the redirect "
            "URI to http://localhost:8080, and exchanging an authorization "
            "code for an access token. Tokens currently expire after "
            "approximately 24 hours."
        )
    )


app = App(
    name="ticktick",
    tools_module=tools,
    sdk_package=_self,
    profile_model=Profile,
    profile_expand=True,
)


__all__ = ["app", "Profile", "__version__"]
