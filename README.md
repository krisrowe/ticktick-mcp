# ticktick-access

CLI and MCP Server for TickTick task management. Integrates with Claude Code, Gemini CLI, and other MCP-compatible clients.

## Quick Start

```bash
# Install
pipx install git+https://github.com/USER/ticktick-access.git

# Setup credentials (one-time)
ticktick client set    # Enter client ID/secret from developer.ticktick.com
ticktick auth          # OAuth flow to get access token

# Configure MCP for Claude Code
claude mcp add --scope user ticktick -- ticktick-mcp --stdio

# Configure MCP for Gemini CLI
gemini mcp add ticktick ticktick-mcp --stdio --scope user
```

## Features

- **CLI Tool (`ticktick`)** - Manage authentication and credentials
- **MCP Server (`ticktick-mcp`)** - Task management for LLM clients
- **Central Config** - Credentials stored in `~/.ticktick-access/`
- **No Docker Required** - Native Python installation via pipx

## Prerequisites

- **Python 3.10+**
- **pipx** - For isolated installation ([install pipx](https://pipx.pypa.io/stable/installation/))
- **TickTick Developer Account** - Register at [developer.ticktick.com](https://developer.ticktick.com/)

## Installation

### Install via pipx (Recommended)

```bash
pipx install git+https://github.com/USER/ticktick-access.git
```

This installs both the `ticktick` CLI and `ticktick-mcp` server commands.

### Upgrade

```bash
pipx upgrade ticktick-access
```

### Uninstall

```bash
pipx uninstall ticktick-access
```

## Setup

### 1. Register Your Application with TickTick

1. Go to [developer.ticktick.com](https://developer.ticktick.com/) and sign in
2. Click **Manage Apps** and create a new application
3. Note your **Client ID** and **Client Secret**
4. Set the **OAuth redirect URL** to: `http://localhost:8080`

### 2. Configure Client Credentials

```bash
ticktick client set
```

Enter your Client ID and Client Secret when prompted. Credentials are saved to `~/.ticktick-access/config.yaml`.

### 3. Authenticate

```bash
ticktick auth
```

This opens your browser for OAuth authorization. After granting permission, the access token is saved to `~/.ticktick-access/token`.

### 4. Verify Setup

```bash
ticktick status
```

## MCP Client Configuration

### Claude Code CLI

```bash
claude mcp add --scope user ticktick -- ticktick-mcp --stdio
```

For detailed configuration options, see [docs/CLAUDE-CODE.md](./docs/CLAUDE-CODE.md).

### Gemini CLI

```bash
gemini mcp add ticktick --command ticktick-mcp --args "--stdio" --scope user
```

For detailed configuration options, see [docs/GEMINI-CLI.md](./docs/GEMINI-CLI.md).

## CLI Reference

| Command | Description |
|---------|-------------|
| `ticktick auth` | Run OAuth flow to get/refresh access token |
| `ticktick client set` | Set client credentials interactively |
| `ticktick client show` | Show current client config (redacted) |
| `ticktick status` | Show authentication status |
| `ticktick --version` | Show version |
| `ticktick --help` | Show help |

## MCP Server Tools

The MCP server exposes these tools for LLM clients:

| Tool | Description |
|------|-------------|
| `list_projects` | List all TickTick projects |
| `list_tasks` | List tasks in a specific project |
| `create_task` | Create a new task |
| `update_task` | Update an existing task |
| `complete_task` | Mark a task as complete |

## MCP Server Resources

| Resource | Description |
|----------|-------------|
| `ticktick://projects` | All projects as JSON |
| `ticktick://tasks/{list_id}` | Tasks in a specific project |

## Token Expiration

TickTick access tokens expire after approximately 24 hours. When your token expires:

```bash
ticktick auth
```

No reconfiguration of MCP clients is needed - they automatically read from `~/.ticktick-access/token`.

## Configuration Files

```
~/.ticktick-access/
├── config.yaml    # Client credentials (client_id, client_secret)
└── token          # Access token
```

Both files have restricted permissions (600) for security.

## Docker (Alternative)

Docker is available as an alternative deployment method. See the Docker section below.

### Build Docker Image

```bash
docker build -t ticktick-mcp-server:latest .
```

### Run with Docker

```bash
# HTTP transport (manual container management)
docker run -d --name ticktick-mcp-server -p 8000:8000 \
  -v ~/.ticktick-access:/root/.ticktick-access:ro \
  ticktick-mcp-server:latest

# Stdio transport (for MCP clients)
docker run -i --rm \
  -v ~/.ticktick-access:/root/.ticktick-access:ro \
  ticktick-mcp-server:latest python server-stdio.py
```

## Troubleshooting

### "No access token found"

Run `ticktick auth` to authenticate.

### "Client credentials not configured"

Run `ticktick client set` to configure your client ID and secret.

### Token expired (401 errors)

Run `ticktick auth` to refresh your token.

### Command not found after install

Ensure pipx's bin directory is in your PATH:
```bash
pipx ensurepath
# Then restart your shell
```

## Documentation

- [CLAUDE-CODE.md](./docs/CLAUDE-CODE.md) - Claude Code CLI configuration
- [GEMINI-CLI.md](./docs/GEMINI-CLI.md) - Gemini CLI configuration
- [CONTRIBUTING.md](./docs/CONTRIBUTING.md) - Development setup, version management, architecture
- [TOOLS.md](./docs/TOOLS.md) - Detailed tool and resource reference

## Contributing

See [docs/CONTRIBUTING.md](./docs/CONTRIBUTING.md) for development setup, version management, and the architecture roadmap.

## License

MIT
