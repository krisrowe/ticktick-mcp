"""Command-line interface for ticktick-access."""

import click

from . import __version__
from .auth import run_oauth_flow
from .config import (
    get_client_credentials,
    get_config_dir,
    load_token,
    save_client_credentials,
)


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
def status():
    """Show authentication status."""
    config_dir = get_config_dir()
    client_id, client_secret = get_client_credentials()
    token = load_token()

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


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
