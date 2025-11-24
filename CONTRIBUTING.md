# Contributing to the TickTick Access MCP Server

This document outlines guidelines and best practices for contributors working on the `ticktick-access` MCP server. It covers setting up your development environment, testing changes, and adhering to documentation standards.

## 1. Development Setup

For local development without Docker, refer to the "Alternative: Local Development Setup" section in `README.md`.

## 2. Testing Tool Changes

When you make changes to existing tools (e.g., in `server.py`) or add new ones, you need to ensure these changes are properly tested within a consistent environment. The recommended approach for testing tool changes is by using Docker.

### Docker-based Testing Workflow

1.  **Modify Tool Code:** Make your changes to `server.py` or any other relevant Python files defining your tools.

2.  **Rebuild Docker Image:**
    ```bash
    cd ticktick-access # Navigate to the project root
    docker build -t ticktick-mcp-server:latest .
    ```
    This command rebuilds your Docker image, incorporating your latest code changes.

3.  **Stop and Remove Existing Container (if running):**
    ```bash
    docker stop ticktick-mcp-server || true # `|| true` prevents error if container isn't running
    docker rm ticktick-mcp-server || true # `|| true` prevents error if container isn't running
    ```
    These commands clear out any old running container instances to ensure a fresh start with your updated image.

4.  **Run a New Container:**
    ```bash
    source .env # Ensure your TICKTICK_ACCESS_TOKEN is loaded from your .env file
    docker run -d \
      --name ticktick-mcp-server \
      -p 8000:8000 \
      -e TICKTICK_ACCESS_TOKEN="$TICKTICK_ACCESS_TOKEN" \
      ticktick-mcp-server:latest
    ```
    This starts a fresh Docker container with your updated code. The `-d` flag runs it in detached mode.

5.  **Test with your MCP Client (e.g., Gemini CLI):**
    Once the container is running, use your MCP client to interact with the server and test your updated/new tools. For instance, to test an `update_task` tool:

    ```
    call:update_task(task_id="GENERIC_TASK_ID", project_id="GENERIC_PROJECT_ID", title="New Title", content="New Content")
    ```
    **Important:** Always use generic placeholders like `GENERIC_TASK_ID` or `GENERIC_PROJECT_ID` in your documentation and examples. **Never commit real task IDs, project IDs, or other sensitive personal information to the repository.**

### Troubleshooting Docker Testing

*   **Tool Not Found Error:** If your MCP client (e.g., Gemini CLI) reports a "Tool not found in registry" error after updating code and restarting the container, it might indicate that the client's internal tool registry has not refreshed. A full restart of your MCP client session might be necessary to force it to re-discover tools.

## 3. Documentation Standards

*   **`VENDOR-API.md`**: Strictly for raw API interaction documentation.
*   **`README.md`**: For usage and configuration of the MCP server.
*   **`CONTRIBUTING.md` (this file)**: For developer-specific guides and maintenance information.
*   **`GEMINI.md`**: For internal notes and guidelines for the Gemini CLI agent.

## 4. Handling Sensitive Information

*   **`TICKTICK_ACCESS_TOKEN`**: This token is sensitive and must always be loaded from a secure source (e.g., `.env` file or environment variables). It should never be hardcoded or committed to the repository.

By following these guidelines, we can ensure a consistent and secure development experience.
