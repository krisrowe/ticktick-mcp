import asyncio
import json
import sys
import click

from . import __version__
from .auth import run_oauth_flow
from .config import (
    get_client_credentials,
    get_config_dir,
    load_token,
    save_client_credentials,
)
from .sdk import projects as sdk_projects
from .sdk import tasks as sdk_tasks


def run_async(coro):
    """Helper to run async coroutines from sync CLI."""
    try:
        return asyncio.run(coro)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.group()
@click.version_option(version=__version__, prog_name="ticktick")
def cli():
    """TickTick Access - CLI for TickTick task management.

    Manage authentication and credentials for the TickTick MCP server.
    """
    pass


@cli.command()
def auth():
    """Authenticate with TickTick (OAuth flow).

    Opens your browser to authorize access to your TickTick account.
    The access token is saved to ~/.ticktick-access/token.
    """
    client_id, client_secret = get_client_credentials()

    if not client_id or not client_secret:
        click.echo("Error: Client credentials not configured.", err=True)
        click.echo("Run 'ticktick client set' first to configure your client ID and secret.", err=True)
        raise SystemExit(1)

    try:
        run_oauth_flow(client_id, client_secret)
        click.echo("\nAuthentication successful!")
    except Exception as e:
        click.echo(f"\nAuthentication failed: {e}", err=True)
        raise SystemExit(1)


@cli.group()
def client():
    """Manage TickTick OAuth client credentials."""
    pass


@client.command("set")
def client_set():
    """Set client credentials interactively.

    You'll need to register an app at https://developer.ticktick.com/
    to get your client ID and client secret.
    """
    click.echo("Configure TickTick OAuth credentials")
    click.echo("Register your app at: https://developer.ticktick.com/")
    click.echo("Set OAuth redirect URL to: http://localhost:8080")
    click.echo()

    client_id = click.prompt("Client ID")
    client_secret = click.prompt("Client Secret")

    save_client_credentials(client_id, client_secret)

    config_dir = get_config_dir()
    click.echo(f"\nCredentials saved to {config_dir}/config.yaml")
    click.echo("Run 'ticktick auth' to authenticate.")


@client.command("show")
def client_show():
    """Show current client configuration (redacted)."""
    client_id, client_secret = get_client_credentials()

    if not client_id:
        click.echo("No client credentials configured.")
        click.echo("Run 'ticktick client set' to configure.")
        return

    # Redact secrets for display
    redacted_id = client_id[:4] + "..." + client_id[-4:] if len(client_id) > 8 else "****"
    redacted_secret = client_secret[:4] + "..." if client_secret else "Not set"

    click.echo(f"Client ID:     {redacted_id}")
    click.echo(f"Client Secret: {redacted_secret}")
    click.echo(f"Config dir:    {get_config_dir()}")


@cli.command()
@click.option("--format", type=click.Choice(["table", "json"]), default="table")
def status(format):
    """Show authentication status."""
    config_dir = get_config_dir()
    client_id, client_secret = get_client_credentials()
    token = load_token()

    if format == "json":
        status_data = {
            "config_directory": str(config_dir),
            "client_credentials": {
                "configured": bool(client_id and client_secret),
            },
            "access_token": {
                "found": bool(token),
                "status": "Ready" if token else "Not found"
            }
        }
        click.echo(json.dumps(status_data, indent=2))
        return

    click.echo(f"Config directory: {config_dir}")
    click.echo()

    # Client credentials status
    if client_id and client_secret:
        click.echo("Client credentials: Configured")
    else:
        click.echo("Client credentials: Not configured")
        click.echo("  Run 'ticktick client set' to configure")

    # Token status
    click.echo()
    if token:
        # Show redacted token
        redacted = token[:8] + "..." + token[-4:] if len(token) > 12 else "****"
        click.echo(f"Access token: {redacted}")
        click.echo("  Status: Ready")
    else:
        click.echo("Access token: Not found")
        click.echo("  Run 'ticktick auth' to authenticate")


@cli.group()
def projects():
    """Manage TickTick projects (lists)."""
    pass


@projects.command("list")
@click.option("--format", type=click.Choice(["table", "json"]), default="table")
def projects_list(format):
    """List all TickTick projects."""
    project_list = run_async(sdk_projects.list_projects())

    if format == "json":
        click.echo(json.dumps(project_list, indent=2))
    else:
        if not project_list:
            click.echo("No projects found.")
            return

        click.echo(f"{'ID':<24} {'NAME':<30} {'KIND'}")
        click.echo("-" * 70)
        for p in project_list:
            click.echo(f"{p.get('id', ''):<24} {p.get('name', ''):<30} {p.get('kind', '')}")


@cli.group()
def tasks():
    """Manage TickTick tasks."""
    pass


async def _resolve_project_id(project_id_or_name: str) -> str:
    """Helper to resolve project name to ID if needed."""
    if len(project_id_or_name) == 24:  # Likely an ID
        return project_id_or_name

    project_list = await sdk_projects.list_projects()
    for p in project_list:
        if p.get("name") == project_id_or_name:
            return p.get("id")

    return project_id_or_name  # Fallback to original


@tasks.command("list")
@click.argument("project", required=False, default="Work")
@click.option("--format", type=click.Choice(["table", "json"]), default="table")
def tasks_list(project, format):
    """List tasks in a project.

    PROJECT can be a project ID or name (default: 'Work').
    """

    async def _list():
        pid = await _resolve_project_id(project)
        return await sdk_tasks.list_tasks(pid)

    result = run_async(_list())

    if format == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        tasks = result.get("tasks", [])
        if not tasks:
            click.echo(f"No tasks found in project '{project}'.")
            return

        click.echo(f"Project: {project} ({result.get('count')} tasks, {result.get('incomplete')} incomplete)")
        click.echo()
        click.echo(f"{'ID':<24} {'STATUS':<10} {'TITLE'}")
        click.echo("-" * 70)
        for t in tasks:
            status = "OPEN" if t.get("status") == 0 else "DONE" if t.get("status") == 2 else str(t.get("status"))
            click.echo(f"{t.get('id', ''):<24} {status:<10} {t.get('title', '')}")


@tasks.command("create")
@click.argument("title")
@click.option("--project", default="Work", help="Project ID or name (default: 'Work').")
@click.option("--content", default="", help="Task description.")
@click.option("--priority", type=int, default=0, help="Priority 0-5 (0=none, 1=low, 3=medium, 5=high).")
def tasks_create(title, project, content, priority):
    """Create a new task."""

    async def _create():
        pid = await _resolve_project_id(project)
        return await sdk_tasks.create_task(pid, title, content=content, priority=priority)

    result = run_async(_create())

    if result.get("success"):
        click.echo(f"Success: {result.get('message')}")
        click.echo(f"Task ID: {result.get('task', {}).get('id')}")
    else:
        click.echo(f"Error: {result.get('error')}", err=True)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
