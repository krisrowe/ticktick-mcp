# Configuring TickTick MCP Server with Gemini CLI

This document outlines how to configure the TickTick MCP Server (developed in this repository) for use with the Gemini CLI. This will allow you to leverage Gemini CLI's capabilities to interact with your TickTick tasks and projects.

## Prerequisites

*   **Docker Setup Complete:** Follow the Docker setup steps in the main [README.md](./README.md) to build the Docker image and obtain your `TICKTICK_ACCESS_TOKEN`.
*   **Gemini CLI Installed:** You need to have the Gemini CLI installed and configured on your system. [Install Gemini CLI](https://google-gemini.github.io/gemini-cli/)

## Configuration Options

You have two options for configuring the TickTick MCP server with Gemini CLI:

### Option A: HTTP Transport (Manual Container Management)

With HTTP transport, you must manually manage the Docker container lifecycle:
- Run `docker run -d` manually before using Gemini CLI
- Remember to start the container each time
- Manually stop/remove containers when done
- Container stays running until you stop it

**The Problem:** This requires manual container management, which can be inconvenient if you forget to start the container or need to manage it across sessions.

#### Using `gemini mcp add` Command

```bash
# From the ticktick-mcp directory (or your workspace root)
gemini mcp add ticktick \
  --transport http \
  --http-url "http://localhost:8000/mcp" \
  --scope user
```

**Note:** Use `--scope user` to make it available from any directory, or omit it for project scope (only works from the directory where you run the command).

#### Manual Configuration

You can also manually edit your Gemini CLI `settings.json` file. Here are example configurations:

**User scope** (`~/.gemini/settings.json`):
```json
{
  "mcpServers": {
    "ticktick": {
      "httpUrl": "http://localhost:8000/mcp"
    }
  }
}
```

**Project scope** (`.gemini/settings.json` in your project):
```json
{
  "mcpServers": {
    "ticktick": {
      "httpUrl": "http://localhost:8000/mcp"
    }
  }
}
```

**Important:** Before using Gemini CLI, ensure the Docker container is running:
```bash
docker ps | grep ticktick-mcp-server
# If not running, start it:
source .env
docker run -d --name ticktick-mcp-server -p 8000:8000 -e TICKTICK_ACCESS_TOKEN="$TICKTICK_ACCESS_TOKEN" ticktick-mcp-server:latest
```

### Option B: Stdio Transport (Auto-Start Container) - Recommended

**The Solution:** Gemini CLI can automatically start Docker containers when using **stdio transport** instead of HTTP. This means:
- ✅ No need to run `docker run -d` manually
- ✅ Container starts automatically when Gemini CLI connects
- ✅ Container stops automatically when done (with `--rm` flag)

**How It Works:**

**HTTP Transport (Manual):**
- Server must be running at `http://localhost:8000/mcp`
- You manage the container lifecycle manually
- Container persists until you stop it

**Stdio Transport (Auto-Start):**
- Gemini CLI runs the `docker` command when connecting
- Container starts automatically
- Container stops automatically when Gemini CLI disconnects

#### Using `gemini mcp add` Command

```bash
# Load token from .env
source .env

# Register with stdio transport (auto-starts container)
gemini mcp add ticktick \
  --command "docker" \
  --args "run" "-i" "--rm" \
  "-e" "TICKTICK_ACCESS_TOKEN=$TICKTICK_ACCESS_TOKEN" \
  "ticktick-mcp-server:latest" \
  "python" "server-stdio.py" \
  --env "TICKTICK_ACCESS_TOKEN=$TICKTICK_ACCESS_TOKEN" \
  --scope user
```

**Important:** The `$TICKTICK_ACCESS_TOKEN` in the command above is expanded by your shell to the actual token value before being passed to `gemini mcp add`. This means:
1. `source .env` loads the token into your shell's environment
2. The shell expands `$TICKTICK_ACCESS_TOKEN` to the actual token value from your `.env` file
3. Gemini CLI receives the actual token value via `--env`
4. Gemini CLI stores that actual token value in `settings.json` (not the variable reference)

**Note:** With stdio transport, Gemini CLI will:
- Start the container automatically when connecting
- Stop and remove the container when done (due to `--rm` flag)
- You don't need to manually manage the container lifecycle

#### Manual Configuration

**User scope** (`~/.gemini/settings.json`):
```json
{
  "mcpServers": {
    "ticktick": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "TICKTICK_ACCESS_TOKEN",
        "ticktick-mcp-server:latest",
        "python",
        "server-stdio.py"
      ],
      "env": {
        "TICKTICK_ACCESS_TOKEN": "${TICKTICK_ACCESS_TOKEN}"
      }
    }
  }
}
```

**Project scope** (`.gemini/settings.json` in your project):
```json
{
  "mcpServers": {
    "ticktick": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "TICKTICK_ACCESS_TOKEN",
        "ticktick-mcp-server:latest",
        "python",
        "server-stdio.py"
      ],
      "env": {
        "TICKTICK_ACCESS_TOKEN": "${TICKTICK_ACCESS_TOKEN}"
      }
    }
  }
}
```

**Important Security Note:** When you use `gemini mcp add` with `--env "TICKTICK_ACCESS_TOKEN=$TICKTICK_ACCESS_TOKEN"`, your shell expands `$TICKTICK_ACCESS_TOKEN` to the actual token value before passing it to Gemini CLI. Gemini CLI then stores that actual token value (not the variable reference) in plain text in your `settings.json` file (either `~/.gemini/settings.json` for user scope or `.gemini/settings.json` for project scope). This file should have restricted permissions (600 recommended) and should never be committed to version control.

**Note:** The token is passed at registration time. If your token expires, you'll need to re-register with the new token.

## Switching from HTTP to Stdio Transport

If you're currently using HTTP transport and want to switch to auto-start mode:

1. **Remove the old HTTP configuration:**
   ```bash
   gemini mcp remove ticktick --scope user  # or --scope project
   ```

2. **Rebuild the Docker image** (to ensure stdio support is available):
   ```bash
   cd ticktick-mcp
   docker build -t ticktick-mcp-server:latest .
   ```

3. **Add with stdio transport:**
   ```bash
   source .env
   gemini mcp add ticktick \
     --command "docker" \
     --args "run" "-i" "--rm" \
     "-e" "TICKTICK_ACCESS_TOKEN=$TICKTICK_ACCESS_TOKEN" \
     "ticktick-mcp-server:latest" \
     "python" "server-stdio.py" \
     --env "TICKTICK_ACCESS_TOKEN=$TICKTICK_ACCESS_TOKEN" \
     --scope user
   ```
   
   **Note:** The shell expands `$TICKTICK_ACCESS_TOKEN` to the actual token value before passing it to `gemini mcp add`, so the actual token value gets stored in `settings.json`.

4. **Verify it works:**
   ```bash
   gemini mcp list
   ```
   The container will start automatically when Gemini CLI connects!

## Configuration File Locations

When you configure the TickTick MCP server, Gemini CLI creates `settings.json` files in these locations:

1. **`.gemini/settings.json`** (project scope)
   - Created when running `gemini mcp add` from the `ticktick-mcp` directory (or without `--scope user`)
   - Only available when running Gemini CLI from that directory or subdirectories
   - Example location: `~/your-workspace/ticktick-mcp/.gemini/settings.json`

2. **`~/.gemini/settings.json`** (user scope)
   - Created when running `gemini mcp add` with `--scope user`
   - Available when running Gemini CLI from any directory
   - Example location: `~/.gemini/settings.json` (in your home directory)

See the configuration examples above for both HTTP and stdio transport options.

**Important Security:** 

- **Token Storage:** When you use `gemini mcp add` with `--env`, the actual token value is stored in plain text in your `settings.json` file. This is the expected behavior for local development.

- **File Permissions:** Ensure your `settings.json` file has restricted permissions:
  ```bash
  chmod 600 ~/.gemini/settings.json  # User scope
  # or
  chmod 600 .gemini/settings.json    # Project scope
  ```

- **Version Control:** Never commit `settings.json` files containing actual tokens to version control. The `.gemini/` directory should be in your `.gitignore`. If you need to share configuration, use environment variable references like `${TICKTICK_ACCESS_TOKEN}` in the `env` section, but note that Gemini CLI may still store the resolved value when using `gemini mcp add`.

## Verifying Configuration

After configuring, verify the server is connected:

```bash
gemini mcp list
```

You should see output like:
```
Configured MCP servers:

✓ ticktick: http://localhost:8000/mcp (http) - Connected
```

If you see "Disconnected", check:
1. For HTTP transport: Ensure the Docker container is running (`docker ps | grep ticktick-mcp-server`)
2. For stdio transport: The container will start automatically when Gemini CLI connects
3. Check container logs: `docker logs ticktick-mcp-server`

## Using with Gemini CLI

Once configured, the Gemini CLI will automatically discover the tools and resources exposed by your TickTick MCP server. You can then interact with it naturally:

- "What are my current TickTick tasks?"
- "List all my TickTick projects"
- "Create a TickTick task to 'Plan vacation' for next Friday"
- "Complete the TickTick task with ID [task_id_here]"

For a complete reference of all available tools and resources, see [TOOLS.md](./TOOLS.md).

## Troubleshooting

**Server shows as "Disconnected":**
- For HTTP transport: Ensure Docker container is running (`docker start ticktick-mcp-server` if stopped)
- Check the `httpUrl` in your `settings.json` matches the container port
- Verify token hasn't expired (re-run `python get_token.py` if needed)

**"Connection refused" errors:**
- Ensure Docker is running: `docker ps`
- Verify container is listening on port 8000: `docker ps | grep 8000`
- Check container logs: `docker logs ticktick-mcp-server`

**Token expiration:**
- Tokens expire after ~24 hours
- Re-run `python get_token.py` to get a new token
- For HTTP transport: Restart container with new token
- For stdio transport: Re-register with `gemini mcp add` using new token

## Configuration Scope Best Practices

- **Use `--scope user`** for MCP servers you want available from any directory
  - Saves to `~/.gemini/settings.json`
  - Available everywhere
  
- **Use `--scope project`** (default) for project-specific servers
  - Saves to `.gemini/settings.json` in current directory
  - Only available from that directory tree

For the TickTick server, **user scope is recommended** since you'll likely want to use it from various projects.

---
For more details on Gemini CLI MCP server configuration, refer to the [official documentation](https://google-gemini.github.io/gemini-cli/docs/tools/mcp-server.html).
