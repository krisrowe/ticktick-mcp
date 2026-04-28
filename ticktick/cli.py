"""ticktick CLI — OAuth helper to obtain a TickTick access token.

Most user-facing operations live in two other commands installed by
this package:

* ``ticktick-mcp serve|stdio`` — the MCP server (mcp-app generated).
* ``ticktick-admin connect|users|tokens|probe|register|health`` —
  user and deployment management (mcp-app generated).

The ``ticktick`` command itself is a thin OAuth helper. Run it once to
walk the TickTick OAuth flow and print an access token, then feed
that token into ``ticktick-admin users add ... --access-token <token>``
to register a user against your deployment.
"""

from __future__ import annotations

import sys

import click

from ticktick import __version__
from ticktick.auth import run_oauth_flow


@click.group()
@click.version_option(version=__version__, prog_name="ticktick")
def cli():
    """TickTick OAuth helper.

    Walks the OAuth flow and prints an access token. The token then goes
    into a user profile via ticktick-admin.
    """


@cli.group()
def auth():
    """Authentication commands."""


@auth.command("login")
@click.option(
    "--client-id",
    envvar="TICKTICK_CLIENT_ID",
    required=True,
    help="TickTick OAuth client ID. Register at https://developer.ticktick.com/.",
)
@click.option(
    "--client-secret",
    envvar="TICKTICK_CLIENT_SECRET",
    required=True,
    help="TickTick OAuth client secret.",
)
def auth_login(client_id, client_secret):
    """Run the OAuth flow and print an access token to stdout.

    Set the OAuth redirect URL of your TickTick app to
    http://localhost:8080. The token printed here goes into a user
    profile:

    \b
        ticktick-admin users add you@example.com --access-token <token>
    """
    try:
        token = run_oauth_flow(client_id, client_secret)
    except Exception as e:  # noqa: BLE001 — surface error to user
        click.echo(f"Authentication failed: {e}", err=True)
        sys.exit(1)

    click.echo(token)


def main():
    """Entry point used by the ``ticktick`` console script."""
    cli()


if __name__ == "__main__":
    main()
