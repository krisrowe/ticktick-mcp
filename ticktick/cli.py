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


@cli.group()
def auth():
    """Manage authentication and security."""
    pass


@auth.command("login")
def auth_login():
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


@auth.command("generate-otp")
def auth_generate_otp():
    """Generate a temporary OTP for MCP tools requiring elevated access.

    The code is valid for 60 seconds and for one use only.
    """
    from .sdk.security import generate_otp
    otp = generate_otp()
    click.echo(f"OTP for mcp tool requiring elevated access: {otp}")
    click.echo("Valid for 60 seconds.")


@cli.group()
def settings():
    """Manage configuration settings."""
    pass


@settings.command("list")
def settings_list():
    """List all settings and their current values."""
    from .config import list_settings
    all_settings = list_settings()
    
    if not all_settings:
        click.echo("No settings defined in manifest.")
        return

    click.echo(f"{'SETTING':<30} {'VALUE':<15} {'DEFAULT':<15} {'DESCRIPTION'}")
    click.echo("-" * 100)
    for key, info in all_settings.items():
        val = str(info['value'])
        default = str(info['default'])
        desc = info['description']
        click.echo(f"{key:<30} {val:<15} {default:<15} {desc}")


@settings.group("set")
def settings_set():
    """Set a configuration value."""
    pass


@settings.group("clear")
def settings_clear():
    """Reset a configuration value to default."""
    pass


@settings.group("show")
def settings_show():
    """Show details of a configuration setting."""
    pass


# Dynamic Command Generation
def _register_settings_commands():
    from .config import list_settings, set_setting
    
    try:
        manifest = list_settings()
    except Exception:
        # If manifest fails to load (e.g. during install), skip
        return

    for key, meta in manifest.items():
        cmd_name = key
        help_text = meta.get("help") or meta.get("description")
        
        # --- SET Command ---
        @settings_set.command(name=cmd_name, help=help_text)
        @click.argument("value")
        def _set_cmd(value, k=key): # Closure on k
            try:
                set_setting(k, value)
                click.echo(f"Updated {k} to '{value}'")
            except Exception as e:
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)
        
        # --- CLEAR Command ---
        @settings_clear.command(name=cmd_name, help=f"Reset {key} to default.")
        def _clear_cmd(k=key):
            try:
                set_setting(k, None)
                click.echo(f"Reset {k} to default.")
            except Exception as e:
                click.echo(f"Error: {e}", err=True)

        # --- SHOW Command ---
        @settings_show.command(name=cmd_name, help=f"Show details for {key}.")
        def _show_cmd(k=key):
            from .config import list_settings
            s = list_settings().get(k)
            if s:
                click.echo(f"Setting:     {k}")
                click.echo(f"Description: {s['description']}")
                click.echo(f"Value:       {s['value']}")
                click.echo(f"Default:     {s['default']}")
                if s.get('options'):
                    click.echo(f"Options:     {', '.join(s['options'])}")
                if s.get('help'):
                    click.echo(f"\n{s['help']}")

# Register them immediately at module level
_register_settings_commands()


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
@click.option("--due", default=None, help="Due date in ISO 8601 format (e.g., 2025-01-15T00:00:00.000+0000).")
@click.option("--status", type=int, default=None, help="Status: 0=open, 2=completed, -1=won't do.")
@click.option("--completed-time", default=None, help="Completion time in ISO 8601 format (for status=2).")
def tasks_create(title, project, content, priority, due, status, completed_time):
    """Create a new task."""

    async def _create():
        pid = await _resolve_project_id(project)
        return await sdk_tasks.create_task(
            pid, title, content=content, priority=priority, due_date=due,
            status=status, completed_time=completed_time
        )

    result = run_async(_create())

    if result.get("success"):
        click.echo(f"Success: {result.get('message')}")
        click.echo(f"Task ID: {result.get('task', {}).get('id')}")
    else:
        click.echo(f"Error: {result.get('error')}", err=True)
        sys.exit(1)


@tasks.command("update")
@click.argument("task_id")
@click.option("--project", required=True, help="Project ID or name containing the task.")
@click.option("--title", default=None, help="New task title.")
@click.option("--content", default=None, help="New task description.")
@click.option("--priority", type=int, default=None, help="New priority 0-5.")
@click.option("--due", default=None, help="New due date in ISO 8601 format.")
@click.option("--status", type=int, default=None, help="New status: 0=open, 2=completed, -1=won't do.")
def tasks_update(task_id, project, title, content, priority, due, status):
    """Update an existing task."""

    async def _update():
        pid = await _resolve_project_id(project)
        return await sdk_tasks.update_task(
            project_id=pid,
            task_id=task_id,
            title=title,
            content=content,
            priority=priority,
            due_date=due,
            status=status,
        )

    result = run_async(_update())

    if result.get("success"):
        click.echo(f"Success: {result.get('message')}")
    else:
        click.echo(f"Error: {result.get('error')}", err=True)
        sys.exit(1)


@tasks.command("delete")
@click.argument("task_id")
@click.option("--project", default="Work", help="Project ID or name (default: 'Work').")
@click.option("--archive-path", default=None, help="Optional directory to save a snapshot of the task. Defaults to configured setting or XDG cache.")
def tasks_delete(task_id, project, archive_path):
    """Delete a task permanently."""

    async def _delete():
        pid = await _resolve_project_id(project)
        return await sdk_tasks.delete_task(pid, task_id, archive_path=archive_path)

    result = run_async(_delete())

    if result.get("success"):
        click.echo(f"Success: {result.get('message')}")
    else:
        click.echo(f"Error: {result.get('error')}", err=True)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
