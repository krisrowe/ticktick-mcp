# Configuring TickTick MCP Server with Gemini CLI and Gemini Code Assist

This document outlines how to configure the TickTick MCP Server (developed in this repository) for use with Gemini CLI and Gemini Code Assist extension in VS Code. The same configuration works for both clients, as they share the same `settings.json` configuration system.

**Note:** IntelliJ's Gemini Code Assist plugin does not currently support MCP servers. This configuration only works with Gemini CLI and VS Code's Gemini Code Assist extension.

## Prerequisites

*   **Docker Setup Complete:** Follow the Docker setup steps in the main [README.md](./README.md) to build the Docker image and obtain your `TICKTICK_ACCESS_TOKEN`.
*   **Gemini CLI or Gemini Code Assist Installed:** 
    *   For Gemini CLI: Install and configure on your system. [Install Gemini CLI](https://google-gemini.github.io/gemini-cli/)
    *   For Gemini Code Assist: Install the extension in VS Code from the VS Code marketplace.

## Shared Configuration

**Important:** Gemini CLI and Gemini Code Assist extension in VS Code share the same configuration system. When you configure the MCP server using `gemini mcp add` (or by manually editing `settings.json`), the configuration is automatically available to:
- Gemini CLI (command-line interface)
- Gemini Code Assist in VS Code

Both clients read from the same `~/.gemini/settings.json` (user scope) or `.gemini/settings.json` (project scope) configuration files.

**Note:** IntelliJ's Gemini Code Assist plugin does not currently support MCP servers. See the [official documentation](https://developers.google.com/gemini-code-assist/docs/use-agentic-chat-pair-programmer#control-built-in-tool-use) for details.

## Configuration Options

This document provides two main ways to configure the TickTick MCP server for use with Gemini CLI and Gemini Code Assist (VS Code). The recommended approach uses a native Python installation via `pipx`, while a more advanced option utilizes Docker.

### Option 1: Native Installation (Recommended)

This is the simplest and recommended way to get started. After installing `ticktick-access` via `pipx` and authenticating (as described in the Prerequisites and main [README.md](../README.md)), you can register the MCP server with Gemini CLI.

**Key points:**
-   No Docker required.
-   Gemini CLI automatically starts and stops the `ticktick-mcp` process when needed.
-   Uses credentials from `~/.ticktick-access/` automatically.

#### Using `gemini mcp add` Command

```bash
# To ensure a clean setup, first remove any existing configuration for 'ticktick'
gemini mcp remove ticktick --scope user

# Then, add the TickTick MCP server
gemini mcp add ticktick ticktick-mcp --stdio --scope user
```

**Note:** Use `--scope user` to make the server available from any directory. If omitted, the server will be configured for `project` scope, meaning it only works when running Gemini CLI from the directory where you run the command (or its subdirectories).

#### Manual Configuration

For more control or to share configurations, you can manually edit your Gemini CLI `settings.json` file.

**User scope** (`~/.gemini/settings.json`):

```json
{
  "mcpServers": {
    "ticktick": {
      "command": "ticktick-mcp",
      "args": ["--stdio"]
    }
  }
}
```

**Project scope** (`.gemini/settings.json` in your project):

```json
{
  "mcpServers": {
    "ticktick": {
      "command": "ticktick-mcp",
      "args": ["--stdio"]
    }
  }
}
```

---

### Option 2: Advanced Configuration with Docker

For advanced use cases, or to run the MCP server in a containerized environment, you can use Docker. This is more complex to set up but provides greater isolation.

There are two ways to use Docker: with **HTTP transport** (where you manage the container manually) or with **stdio transport** (where Gemini CLI starts the container automatically). The stdio transport is recommended if you choose to use Docker.

#### A: Docker with HTTP Transport (Manual Container Management)

With HTTP transport, you must manually manage the Docker container lifecycle:
- Run `docker run -d` manually before using Gemini CLI
- Remember to start the container each time
- Manually stop/remove containers when done
- Container stays running until you stop it

**The Problem:** This requires manual container management, which can be inconvenient if you forget to start the container or need to manage it across sessions.

##### Using `gemini mcp add` Command

```bash
# From the ticktick-mcp directory (or your workspace root)
gemini mcp add ticktick \
  --transport http \
  --http-url "http://localhost:8000/mcp" \
  --scope user
```

##### Manual Configuration

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

**Important:** Before using Gemini CLI or Gemini Code Assist (VS Code), ensure the Docker container is running:
```bash
docker ps | grep ticktick-mcp-server
# If not running, start it:
source .env
docker run -d --name ticktick-mcp-server -p 8000:8000 -e TICKTICK_ACCESS_TOKEN="$TICKTICK_ACCESS_TOKEN" ticktick-mcp-server:latest
```

#### B: Docker with Stdio Transport (Auto-Start Container)

**The Solution:** Gemini CLI and Gemini Code Assist (VS Code) can automatically start Docker containers when using **stdio transport** instead of HTTP. This means:
- ✅ No need to run `docker run -d` manually
- ✅ Container starts automatically when Gemini CLI connects
- ✅ Container stops automatically when done (with `--rm` flag)

##### Using `gemini mcp add` Command

```bash
# Load token from .env
source .env

# Register with stdio transport (auto-starts container)
gemini mcp add ticktick \
  "docker run -i --rm -e TICKTICK_ACCESS_TOKEN=$TICKTICK_ACCESS_TOKEN ticktick-mcp-server:latest python server-stdio.py" \
  --env "TICKTICK_ACCESS_TOKEN=$TICKTICK_ACCESS_TOKEN" \
  --scope user
```

**Important:** The `$TICKTICK_ACCESS_TOKEN` in the command above is expanded by your shell to the actual token value before being passed to `gemini mcp add`. This means:
1. `source .env` loads the token into your shell's environment
2. The shell expands `$TICKTICK_ACCESS_TOKEN` to the actual token value from your `.env` file
3. Gemini CLI receives the actual token value via `--env`
4. Gemini CLI stores that actual token value in `settings.json` (not the variable reference)


##### Manual Configuration

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

**Important Security Note:** When you use `gemini mcp add` with `--env "TICKTICK_ACCESS_TOKEN=$TICKTICK_ACCESS_TOKEN"`, your shell expands `$TICKTICK_ACCESS_TOKEN` to the actual token value before passing it to Gemini CLI. Gemini CLI then stores that actual token value (not the variable reference) in plain text in your `settings.json` file. This file should have restricted permissions (600 recommended) and should never be committed to version control.

**Note:** The token is passed at registration time. If your token expires, you'll need to re-register with the new token.

## Switching from HTTP to Stdio Transport

If you're currently using the manual Docker HTTP transport and want to switch to the auto-start Docker stdio mode:

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
     "docker run -i --rm -e TICKTICK_ACCESS_TOKEN=$TICKTICK_ACCESS_TOKEN ticktick-mcp-server:latest python server-stdio.py" \
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

When you configure the TickTick MCP server using `gemini mcp add`, the configuration is written to `settings.json` files that are shared by Gemini CLI and Gemini Code Assist (VS Code):

1. **`.gemini/settings.json`** (project scope)
   - Created when running `gemini mcp add` from the `ticktick-mcp` directory (or without `--scope user`)
   - Only available when running Gemini CLI from that directory or subdirectories, or when opening that directory in VS Code with Gemini Code Assist
   - Example location: `~/your-workspace/ticktick-mcp/.gemini/settings.json`

2. **`~/.gemini/settings.json`** (user scope)
   - Created when running `gemini mcp add` with `--scope user`
   - Available when running Gemini CLI from any directory, or when using Gemini Code Assist in VS Code from any workspace
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

**For Gemini CLI:**
```bash
gemini mcp list
```

You should see output like this for a stdio connection:
```
Configured MCP servers:

✓ ticktick: ticktick-mcp --stdio (stdio) - Connected
```

**For Gemini Code Assist (VS Code):**
The MCP server should appear in the extension's MCP server list. Check the extension's status or settings panel to verify connectivity.

If you see "Disconnected" or the server doesn't appear, check:
1. For HTTP transport: Ensure the Docker container is running (`docker ps | grep ticktick-mcp-server`)
2. For stdio transport: The container will start automatically when Gemini CLI or Gemini Code Assist (VS Code) connects
3. Check container logs: `docker logs ticktick-mcp-server`
4. Verify the configuration file exists and contains the correct settings: `cat ~/.gemini/settings.json` (user scope) or `cat .gemini/settings.json` (project scope)

## Using with Gemini CLI and Gemini Code Assist

Once configured, Gemini CLI and Gemini Code Assist (VS Code) will automatically discover the tools and resources exposed by your TickTick MCP server. You can then interact with it naturally:

**With Gemini CLI:**
- "What tasks do I have for the work project?"
- "List all my projects"
- "Create a task to 'Plan vacation' for next Friday"
- "Mark the task about reviewing the pull request as completed"

**With Gemini Code Assist (VS Code):**
- Use natural language in the chat interface to interact with your tasks
- The extension will automatically use the configured MCP server when you ask about tasks or projects
- Example: "What tasks do I have for the work project?" or "Create a task to review the pull request" or "Mark the task about fixing the bug as completed"

For a complete reference of all available tools and resources, see [TOOLS.md](./TOOLS.md).

## Troubleshooting

**Server shows as "Disconnected":**
- For HTTP transport: Ensure Docker container is running (`docker start ticktick-mcp-server` if stopped)
- Check the `httpUrl` in your `settings.json` matches the container port
- Verify token hasn't expired (re-run `python get_token.py` if needed)
- For stdio transport: Check the "Debugging the Configuration" section below to ensure your `settings.json` is correct.

### Debugging the Configuration

If you're having issues, the first place to check is your `settings.json` file. This file is updated when you run `gemini mcp add`.

**File Locations:**
- **User Scope:** `~/.gemini/settings.json`
- **Project Scope:** `.gemini/settings.json` (in the directory where you ran the `add` command)

You can inspect the file with `cat`:
```bash
cat ~/.gemini/settings.json
```

For the recommended native `stdio` installation, the `mcpServers` section for `ticktick` should look like this:

```json
{
  "mcpServers": {
    "ticktick": {
      "command": "ticktick-mcp",
      "args": [
        "--stdio"
      ]
    }
  }
}
```

**Common Mistakes:**
- The `--stdio` flag is part of the `command` string instead of in the `args` array.
- There are extra characters or incorrect quoting.

If the file looks incorrect, the easiest way to fix it is to remove and re-add the server as described in the "Using `gemini mcp add` Command" section.


**"Connection refused" errors:**
- Ensure Docker is running: `docker ps`
- Verify container is listening on port 8000: `docker ps | grep 8000`
- Check container logs: `docker logs ticktick-mcp-server`

**Token expiration:**
- Tokens expire after ~24 hours
- Re-run `python scripts/get_token.py` to get a new token
- For HTTP transport: Restart container with new token
- For stdio transport: Re-register with `gemini mcp add` using new token (this will update the configuration for both Gemini CLI and Gemini Code Assist in VS Code)

## Configuration Scope Best Practices

- **Use `--scope user`** for MCP servers you want available from any directory
  - Saves to `~/.gemini/settings.json`
  - Available everywhere
  
- **Use `--scope project`** (default) for project-specific servers
  - Saves to `.gemini/settings.json` in current directory
  - Only available from that directory tree

For the TickTick server, **user scope is recommended** since you'll likely want to use it from various projects.

---

## Notes for VS Code Users

- **Configuration Sharing:** The configuration you create using `gemini mcp add` is automatically shared with Gemini Code Assist extension in VS Code. You don't need to configure them separately.

- **Restart Required:** After configuring or updating the MCP server configuration, you may need to restart VS Code for the changes to take effect in Gemini Code Assist.

- **Project vs User Scope:** 
  - **User scope** (`--scope user`): The MCP server will be available in all VS Code workspaces
  - **Project scope** (default): The MCP server will only be available when you open the specific directory containing `.gemini/settings.json` in VS Code

**Note:** IntelliJ's Gemini Code Assist plugin does not currently support MCP servers. See the [official documentation](https://developers.google.com/gemini-code-assist/docs/use-agentic-chat-pair-programmer#control-built-in-tool-use) for details.

For more details on Gemini CLI MCP server configuration, refer to the [official documentation](https://google-gemini.github.io/gemini-cli/docs/tools/mcp-server.html).