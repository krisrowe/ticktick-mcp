# MCP Server for Task Management using TickTick

This project provides tools and examples for personal agentic access to the TickTick task platform's API. It now includes a **Model Context Protocol (MCP) server** to provide a unified interface for managing tasks and other data, making it easily consumable by LLMs like Gemini CLI, Gemini Code Assist (VS Code), and Claude Desktop.

TickTick is a robust task management platform, ideal for anyone looking to efficiently track their tasks. It's particularly well-suited for engineers juggling multiple projects and seeking to automate their workflow across various platforms.

## Features

*   **MCP Server:** Exposes TickTick functionalities as Resources and Tools for LLMs with comprehensive documentation.
*   **OAuth 2.0 Integration:** Uses `scripts/get_token.py` to facilitate OAuth 2.0 authorization for secure API access.
*   **Task Management:** MCP Tools for creating, listing, and completing tasks with full input/output schemas.
*   **Data Retrieval:** MCP Resources for listing projects and tasks with detailed descriptions.
*   **Auto-Discovery:** Tools and resources are automatically discovered by MCP clients with descriptions, schemas, and metadata.

For detailed documentation of all available tools and resources, see [docs/TOOLS.md](./docs/TOOLS.md).

## Setup

### Prerequisites

*   **Docker**: Docker must be installed and running on your system. [Install Docker](https://www.docker.com/get-started)
*   **MCP Client**: An MCP-compatible client such as Gemini CLI, Gemini Code Assist (VS Code), Claude Desktop, or MCP Inspector
*   **TickTick Developer Account**: You'll need to register an application on the TickTick Developer Portal (see Authentication section below)

> **For Gemini CLI and Gemini Code Assist users:** See [docs/GEMINI-CLI.md](./docs/GEMINI-CLI.md) for detailed configuration instructions. The same configuration works for both Gemini CLI and Gemini Code Assist extension in VS Code. Note: IntelliJ's Gemini Code Assist plugin does not currently support MCP servers.

## Quick Start: Docker Setup (Recommended)

This is the recommended way to run the TickTick MCP Server. The Docker setup ensures consistent environments and easy deployment.

### Step 1: Authentication Setup

Before building and running the Docker container, you need to set up authentication:

1.  **Register Your Application with TickTick:**
    *   Go to [developer.ticktick.com](https://developer.ticktick.com/) and sign in.
    *   Click on **Manage Apps**.
    *   Create a new application or edit an existing one.
    *   Note down your **"Client ID"** and **"Client Secret"**.
    *   Set the **"OAuth redirect URL"** to exactly: `http://localhost:8080`

2.  **Configure `.env` File:**
    Create a file named `.env` in the root of your `ticktick-mcp` directory:
    ```bash
    cd ticktick-mcp
    ```
    
    Create `.env` with your credentials:
    ```
    TICKTICK_CLIENT_ID="your_client_id_from_ticktick"
    TICKTICK_CLIENT_SECRET="your_client_secret_from_ticktick"
    ```

3.  **Obtain `TICKTICK_ACCESS_TOKEN`:**
    ```bash
    python scripts/get_token.py
    ```
    This script will:
    *   Open your web browser for authorization.
    *   After you grant permission, it will exchange the authorization code for an `access_token`.
    *   It will print the `access_token` and automatically save/update it in your `.env` file as `TICKTICK_ACCESS_TOKEN`.

    **Note:** TickTick API access tokens typically expire after a certain period (e.g., 24 hours). When a token expires, API calls will start to fail with authentication errors (e.g., HTTP 401 Unauthorized). To update your token:
    1. Re-run `python scripts/get_token.py` to get a new token
    2. For HTTP transport: Stop and restart the Docker container with the new token (see Step 3)
    3. For stdio transport (auto-start): Re-register your MCP client with the new token (see [docs/GEMINI-CLI.md](./docs/GEMINI-CLI.md) for Gemini CLI/Code Assist instructions)

### Step 2: Build the Docker Image

Navigate to the project directory and build the Docker image:

```bash
cd ticktick-mcp
docker build -t ticktick-mcp-server:latest .
```

This will create a Docker image named `ticktick-mcp-server:latest` with all dependencies installed.

### Step 3: Run the Docker Container

Run the container in detached mode (`-d`) with the access token from your `.env` file:

```bash
# Load the token from .env and run the container
source .env
docker run -d \
  --name ticktick-mcp-server \
  -p 8000:8000 \
  -e TICKTICK_ACCESS_TOKEN="$TICKTICK_ACCESS_TOKEN" \
  ticktick-mcp-server:latest
```

**Explanation of flags:**
- `-d`: Run container in detached mode (background)
- `--name ticktick-mcp-server`: Give the container a friendly name
- `-p 8000:8000`: Map container port 8000 to host port 8000
- `-e TICKTICK_ACCESS_TOKEN`: Pass the access token as an environment variable

### Step 4: Verify Server is Running

Check that the container is running:

```bash
docker ps | grep ticktick-mcp-server
```

You should see output showing the container is `Up` and port `8000` is mapped.

Check the container logs to ensure the server started successfully:

```bash
docker logs ticktick-mcp-server
```

You should see output like:
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Test Server Response

Verify the server is responding correctly:

```bash
# Test that the server endpoint is accessible
curl -s http://localhost:8000/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | head -c 500
```

**Expected results:**
- **Success:** You should see a JSON response with `"result"` containing server capabilities. This confirms the server is working correctly!
- **406 Error:** If you see a 406 "Not Acceptable" error, it means the server is running but requires proper MCP protocol headers. This is expected - MCP clients will provide these automatically.
- **Connection refused:** If you see connection refused errors, check that the container is running with `docker ps` and that port 8000 is not already in use.

### Managing the Docker Container

**Stop the container:**
```bash
docker stop ticktick-mcp-server
```

**Start the container:**
```bash
docker start ticktick-mcp-server
```

**View logs:**
```bash
docker logs ticktick-mcp-server
# Or follow logs in real-time:
docker logs -f ticktick-mcp-server
```

**Remove the container:**
```bash
docker rm -f ticktick-mcp-server
```

**Optional: Using the convenience script** (`scripts/start-server.sh`):
For HTTP transport users who want a convenience wrapper, you can use the provided `scripts/start-server.sh` script:
```bash
./scripts/start-server.sh
```
This script automatically checks if the container is running, starts it if stopped, or creates it if it doesn't exist. It handles loading the token from `.env` and building the image if needed.

**Note:** For stdio transport (recommended), this script is not needed as Gemini CLI and Gemini Code Assist handle container lifecycle automatically. See [docs/GEMINI-CLI.md](./docs/GEMINI-CLI.md) for stdio transport setup.

---

## Alternative: Local Development Setup

If you prefer to run the server locally without Docker (useful for development):

### Prerequisites

*   **Python 3.10** or higher.
*   **`uv`**: A fast Python package installer and resolver.

### Install `uv`

If you don't have `uv` installed, use the following command (for macOS/Linux):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
(For Windows, refer to the official `uv` installation guide: https://astral.sh/uv/install)

### Project Setup

1.  **Navigate to the project directory:**
    ```bash
    cd ticktick-mcp
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```

3.  **Install project dependencies:**
    ```bash
    uv pip install "mcp[cli]" httpx
    ```

### Running the MCP Server Locally

Once your environment is set up and you have a valid `TICKTICK_ACCESS_TOKEN` in your `.env` file (or set as an environment variable), you can run the MCP server:

1.  **Ensure virtual environment is activated:**
    ```bash
    source .venv/bin/activate
    ```
2.  **Run the server:**
    ```bash
    uv run server.py
    ```
    The server will start and listen for connections on `http://127.0.0.1:8000/mcp`. Keep this terminal window open while using the server.

## Configuring MCP Clients

This MCP server can be used with various MCP-compatible clients, such as Gemini CLI, Claude Desktop, or the MCP Inspector.

### Transport Options

The server supports two transport modes:

1. **HTTP Transport**: The server runs as a persistent HTTP service (as set up in Step 3). Clients connect to `http://localhost:8000/mcp`. The container must be running before clients connect.

2. **Stdio Transport**: The server runs as a subprocess, communicating via standard input/output. This allows clients to automatically start and stop the server. Use `server-stdio.py` for this mode.

### Client-Specific Configuration

*   **Gemini CLI and Gemini Code Assist (VS Code)**: See [docs/GEMINI-CLI.md](./docs/GEMINI-CLI.md) for detailed configuration instructions, including both HTTP and stdio transport options. The same configuration works for both Gemini CLI and Gemini Code Assist extension in VS Code. Note: IntelliJ's Gemini Code Assist plugin does not currently support MCP servers.

*   **Other MCP Clients** (Claude Desktop, MCP Inspector, etc.):
    *   For HTTP transport: Configure the client to connect to `http://localhost:8000/mcp` and ensure the Docker container is running (see Step 3).
    *   For stdio transport: Configure the client to run `docker run -i --rm -e TICKTICK_ACCESS_TOKEN="$TICKTICK_ACCESS_TOKEN" ticktick-mcp-server:latest python server-stdio.py` with the token set in the environment.
    *   Refer to your client's documentation for MCP server configuration details.

## Troubleshooting

### Docker Container Issues

**Container won't start:**
```bash
# Check if port 8000 is already in use
lsof -i :8000
# Or on Linux:
netstat -tulpn | grep 8000

# If port is in use, either stop the conflicting service or use a different port:
docker run -d --name ticktick-mcp-server -p 8001:8000 -e TICKTICK_ACCESS_TOKEN="$TICKTICK_ACCESS_TOKEN" ticktick-mcp-server:latest
# Then update your MCP client configuration to use http://localhost:8001/mcp
```

**Container exits immediately:**
```bash
# Check logs for errors
docker logs ticktick-mcp-server

# Common issues:
# - Missing TICKTICK_ACCESS_TOKEN: Ensure you've sourced .env before running docker run
# - Invalid token: Re-run python scripts/get_token.py to get a fresh token
```

**"Container name already in use" error:**
```bash
# Remove the existing container first
docker rm -f ticktick-mcp-server
# Then run again
```

### MCP Client Connection Issues

**Client cannot connect to server:**
1. Verify the container is running: `docker ps | grep ticktick-mcp-server`
2. For HTTP transport: Ensure the client is configured to connect to `http://localhost:8000/mcp`
3. Test the endpoint manually with the curl command from Step 5
4. Check container logs for errors: `docker logs ticktick-mcp-server`
5. Ensure Docker is running: `docker ps`
6. Verify the container is listening on port 8000: `docker ps | grep 8000`
7. Check firewall settings if using a remote Docker host

**For Gemini CLI and Gemini Code Assist troubleshooting:** See [docs/GEMINI-CLI.md](./docs/GEMINI-CLI.md#troubleshooting)

### Authentication Issues

**401 Unauthorized errors:**
- Your `TICKTICK_ACCESS_TOKEN` has likely expired. Re-run `python scripts/get_token.py` to get a new token, then restart the container.

**Token not found errors:**
- Ensure you've run `source .env` before the `docker run` command
- Verify your `.env` file contains `TICKTICK_ACCESS_TOKEN=...`
- Check that the token is being passed correctly: `docker inspect ticktick-mcp-server | grep -A 5 Env`

## MCP Discovery and Documentation

This MCP server provides comprehensive tool and resource discovery:

- **Tools:** All tools include detailed descriptions, input schemas (with parameter descriptions), and output schemas
- **Resources:** All resources include descriptions explaining their purpose and usage
- **Auto-Discovery:** MCP clients automatically discover available tools and resources with full metadata

When using an MCP client like Gemini CLI, Gemini Code Assist, or the MCP Inspector, you should see:
- Tool names with descriptions
- Input parameter details (names, types, descriptions, required/optional)
- Output structure information
- Resource URI patterns and descriptions

For a complete reference of all tools and resources, see [docs/TOOLS.md](./docs/TOOLS.md).

## Limitations (MCP Server)

*   **Inbox List:** This MCP server currently does not provide direct tools or resources for accessing the "Inbox" as a named list or project. Tasks created without a specified project may default to the Inbox depending on TickTick's API behavior.
*   *(Add other MCP server limitations as they are discovered or become relevant.)*

---

### Appendix: Direct TickTick V1 API Usage

For detailed instructions on how to authenticate with the TickTick API and for `curl` examples of common operations, please see the **[Vendor API Guide](./docs/VENDOR-API.md)**.