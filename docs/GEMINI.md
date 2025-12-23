# Gemini CLI Agent Notes for ticktick-mcp repository

This document provides guidelines and context for the Gemini CLI agent when working within the `ticktick-mcp` repository.

## Content Placement Guidelines

To maintain clarity and separation of concerns in documentation, please adhere to the following guidelines:

*   **`VENDOR-API.md`**: This file is strictly for documenting raw API interaction with the TickTick platform using generic `curl` commands. It should detail authentication flows, API endpoints, request/response formats, and any vendor-specific limitations. **It should NOT contain information about our internal MCP server product, Docker testing steps, or any other contributor-specific development process.**

*   **`README.md`**: This file serves as the primary user-facing documentation for setting up and running the `ticktick-mcp` MCP server. It should include quick start guides, Docker setup instructions for users, and configuration information. It focuses on **usage and configuration, not on maintenance or extension of the MCP server.**

*   **`CONTRIBUTING.md`**: This file is for contributors and developers. It includes guides on setting up a development environment, **how to build, run, and test changes to tools (including Docker-based testing steps)**, and other development-specific information.

*   **`GEMINI.md` (this file)**: This file is specifically for internal notes and instructions for the Gemini CLI agent. It captures meta-information about the repository's structure, conventions, and specific instructions for the agent's workflow.

## Sensitive Information Handling

*   **`TICKTICK_ACCESS_TOKEN`**: This token is sensitive and should **never** be hardcoded into any script, documentation, or committed to version control. It must always be loaded from a secure source, such as the `.env` file (which is `.gitignore`d) or environment variables. All examples and tool implementations should respect this. When testing, ensure that the token is passed securely (e.g., via Docker environment variables or loaded from a mounted `.env`).

### Pre-Commit Sensitive Information Check

Before committing any changes, especially to code, examples, or documentation, perform a thorough check for sensitive or personal information. This includes, but is not limited to:

*   **Developer-specific Paths:** Avoid including paths that reveal a developer's home directory or specific user names (e.g., `/home/developer/project` should be generalized to `/path/to/project`).
*   **Names and Emails:** Do not include anyone's real name, email address, or any other personally identifiable information. Use generic placeholders (e.g., "John Doe", "user [at] example [dot] com") instead.
*   **Real IDs/Secrets:** Ensure all task IDs, project IDs, client IDs/secrets, or any other API-related identifiers are generic placeholders in examples and documentation.
*   **Hardcoded Credentials:** Double-check that no API keys, tokens, or other credentials are hardcoded anywhere in the repository.

## Pre-Commit Checks

Before committing any changes, it is essential to run the following checks to maintain code quality and ensure tests are passing:

1.  **Run Tests:** Execute unit tests to ensure all functionality works as expected and no regressions have been introduced.
    ```bash
    PYTHONPATH=. ./.venv/bin/pytest
    ```
    All tests must pass.

2.  **Run Linter:** Check for code style and potential issues using Ruff.
    ```bash
    PYTHONPATH=. ./.venv/bin/ruff check .
    ```
    All checks must pass with no errors reported. If Ruff reports fixable issues, you can auto-fix them:
    ```bash
    PYTHONPATH=. ./.venv/bin/ruff check . --fix
    ```
    Then, it's good practice to run `ruff format .` to ensure consistent code formatting:
    ```bash
    PYTHONPATH=. ./.venv/bin/ruff format .
    ```

## Making and Testing Code Changes

When making changes to the MCP server code (e.g., in `server.py`), it is crucial to rebuild the Docker image and restart the Gemini CLI to ensure the changes are applied.

### Development Workflow

1.  **Make Code Changes:** Modify the server code as required (e.g., adding a new tool to `server.py`).
2.  **Rebuild the Docker Image:** After making changes, you must rebuild the `ticktick-mcp-server:latest` Docker image. Run the following command from the `ticktick-mcp` directory:
    ```bash
    docker build -t ticktick-mcp-server:latest .
    ```
    If you suspect that Docker's cache is preventing your changes from being included, use the `--no-cache` flag:
    ```bash
    docker build --no-cache -t ticktick-mcp-server:latest .
    ```
3.  **Restart the Gemini CLI:** The Gemini CLI starts the MCP server in a Docker container. To ensure the CLI uses the newly built image, you **must restart the Gemini CLI**.
4.  **Test the Changes:** After restarting the CLI, test your changes by invoking the relevant tools.

### Enabling Debug Logging

To help with troubleshooting, you can enable debug-level logging for the MCP server. This is controlled by the `LOG_LEVEL` environment variable.

To enable debug logging, you need to modify your `~/.gemini/settings.json` file to pass the `LOG_LEVEL` environment variable to the Docker container.

1.  **Add `LOG_LEVEL` to the `args` array:**
    ```json
    "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "TICKTICK_ACCESS_TOKEN",
        "-e", 
        "LOG_LEVEL", 
        "ticktick-mcp-server:latest",
        "python",
        "server-stdio.py"
    ],
    ```
2.  **Add `LOG_LEVEL` to the `env` dictionary:**
    ```json
    "env": {
        "TICKTICK_ACCESS_TOKEN": "YOUR_ACCESS_TOKEN",
        "LOG_LEVEL": "DEBUG" 
    }
    ```
3.  **Restart the Gemini CLI** for the new settings to take effect.