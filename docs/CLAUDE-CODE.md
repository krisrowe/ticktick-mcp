# Configuring TickTick MCP Server with Claude Code

This document outlines how to configure the TickTick MCP Server for use with Claude Code (the CLI tool).

## Prerequisites

- **ticktick-access Installed:** Install via pipx (see main [README.md](../README.md))
- **TickTick Authentication Complete:** Run `ticktick client set` and `ticktick auth`
- **Claude Code Installed:** [Install Claude Code](https://docs.anthropic.com/en/docs/claude-code)

## Quick Start

```bash
claude mcp add --scope user ticktick -- ticktick-mcp --stdio
```

This adds the TickTick MCP server to your user scope so it's available in all projects.

## Configuration Options

### Option A: Native Install (Recommended)

After installing ticktick-access via pipx:

```bash
claude mcp add --scope user ticktick -- ticktick-mcp --stdio
```

**Key points:**
- `--scope user` makes the server available across all projects
- `--` separates Claude's flags from the server command
- Uses credentials from `~/.ticktick-access/` automatically

### Option B: Manual Configuration

For team sharing or more control, edit your Claude config file directly.

**User scope** (`~/.claude.json`):

```json
{
  "mcpServers": {
    "ticktick": {
      "type": "stdio",
      "command": "ticktick-mcp",
      "args": ["--stdio"]
    }
  }
}
```

### Option C: Docker (Alternative)

If you prefer containerized deployment:

```bash
claude mcp add --scope user ticktick -- docker run -i --rm \
  -v ~/.ticktick-access:/root/.ticktick-access:ro \
  ticktick-mcp-server:latest python server-stdio.py
```

Or in JSON:

```json
{
  "mcpServers": {
    "ticktick": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "~/.ticktick-access:/root/.ticktick-access:ro",
        "ticktick-mcp-server:latest",
        "python", "server-stdio.py"
      ]
    }
  }
}
```

## Configuration Scope

| Scope | Location | Use Case |
|-------|----------|----------|
| `user` | `~/.claude.json` | Personal use across all projects (recommended) |
| `project` | `.mcp.json` in project root | Team sharing |
| `local` | Local to current session | Temporary testing |

For TickTick, **user scope is recommended** since you'll want task access from various projects.

## Verifying Configuration

```bash
# List all configured MCP servers
claude mcp list

# Get details for the ticktick server
claude mcp get ticktick
```

Within a Claude Code session, use the `/mcp` command to check server status.

## Using with Claude Code

Once configured, interact naturally:

- "What are my TickTick projects?"
- "Show me tasks in my Work project"
- "Create a task to review the pull request"
- "Mark the deployment task as complete"

## Managing Servers

```bash
# Remove the server
claude mcp remove ticktick --scope user

# Update by removing and re-adding
claude mcp remove ticktick --scope user
claude mcp add --scope user ticktick -- ticktick-mcp --stdio
```

## Troubleshooting

**Server not connecting:**
- Ensure ticktick-access is installed: `ticktick --version`
- Check authentication: `ticktick status`
- Re-authenticate if needed: `ticktick auth`

**Token expiration:**
- TickTick tokens expire after ~24 hours
- Run `ticktick auth` to refresh
- No reconfiguration needed - server reads from `~/.ticktick-access/token`

**Permission errors:**
- Claude Code prompts for approval on project-scoped servers from `.mcp.json`
- User-scoped servers in `~/.claude.json` don't require approval

**Debug mode:**
For detailed server logs, run the server manually:
```bash
LOG_LEVEL=DEBUG ticktick-mcp --stdio
```

## Security Considerations

**Token Storage:**
- Tokens are stored in `~/.ticktick-access/token`
- File permissions are set to 600 (owner read/write only)
- Never commit token files to version control

**File Permissions:**
```bash
chmod 600 ~/.ticktick-access/token
chmod 600 ~/.ticktick-access/config.yaml
```

## Comparison with Other Clients

| Feature | Claude Code | Claude Desktop | Gemini CLI |
|---------|-------------|----------------|------------|
| Config file | `~/.claude.json` or `.mcp.json` | Platform-specific | `~/.gemini/settings.json` |
| Add command | `claude mcp add` | Manual JSON edit | `gemini mcp add` |
| Transport | stdio | stdio or HTTP | stdio or HTTP |
| Scope levels | user, project, local | N/A | user, project |

---

For more details on Claude Code MCP server configuration, see the [official documentation](https://docs.anthropic.com/en/docs/claude-code/mcp).
