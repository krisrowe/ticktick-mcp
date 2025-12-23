# Contributing to ticktick-access

This document outlines guidelines and best practices for contributors working on ticktick-access. It covers version management, development setup, testing, and documentation standards.

## Version Management

**Single source of truth:** `ticktick/__init__.py` contains `__version__`

**When to bump versions:**

| Change Type | Bump | Example |
|-------------|------|---------|
| Bug fix, minor tweak | Patch | 0.2.0 → 0.2.1 |
| New feature (backwards compatible) | Minor | 0.2.0 → 0.3.0 |
| Breaking change | Major | 0.2.0 → 1.0.0 |

**Release workflow:**

1. Make changes, commit normally
2. When ready to release:
   ```bash
   # Update version in ticktick/__init__.py
   # Commit the version bump
   git add ticktick/__init__.py
   git commit -m "chore: bump version to X.Y.Z"

   # Tag the release
   git tag vX.Y.Z

   # Push with tags
   git push && git push --tags
   ```

**Why version bumps matter:**

- `pip install --upgrade` only installs if version number is higher
- Same version number = pip thinks nothing changed, skips update
- Editable installs (`pip install -e .`) always use live code regardless of version

**For development:** Use editable install to avoid version concerns:
```bash
pipx install -e .   # or: pip install -e .
```

## Upgrading ticktick-access

To upgrade an existing installation:

```bash
# Upgrade via pipx
pipx upgrade ticktick-access

# Or reinstall from latest
pipx uninstall ticktick-access
pipx install git+https://github.com/USER/ticktick-access.git
```

## Architecture

### SDK-First Pattern (Required)

**All business logic must live in the SDK layer.** The MCP and CLI layers must remain thin wrappers that simply call SDK functions.

```
ticktick-access/
├── ticktick/
│   ├── __init__.py          # Package version
│   ├── config.py            # Config/credential management
│   ├── auth.py              # OAuth flow
│   ├── sdk/                 # Core SDK layer - ALL logic here
│   │   ├── __init__.py
│   │   ├── client.py        # TickTick API client (HTTP layer)
│   │   ├── projects.py      # Project operations
│   │   └── tasks.py         # Task operations
│   ├── cli.py               # CLI commands (thin, calls SDK)
│   └── mcp/
│       └── server.py        # MCP server (thin, calls SDK)
```

### Layer Responsibilities

| Layer | Responsibility | Example |
|-------|---------------|---------|
| **SDK** | All business logic, API calls, data transformation | `sdk.tasks.create_task(project_id, title, reminders=[...])` |
| **MCP** | Tool decorators, parameter descriptions, error wrapping | Wraps SDK call in `@mcp.tool()` |
| **CLI** | Argument parsing, user output formatting | Calls SDK, prints results |

### Adding New Features

When adding a new feature (e.g., reminders support):

1. **Implement in SDK first** - Add the logic to the appropriate SDK module
2. **Expose in MCP** - Add a thin tool wrapper that calls the SDK
3. **Expose in CLI** (optional) - Add a command that calls the SDK

**Example - Adding reminders:**

```python
# sdk/tasks.py - The actual implementation
async def create_task(project_id, title, reminders=None, ...):
    task_data = {"projectId": project_id, "title": title}
    if reminders:
        task_data["reminders"] = reminders
    return await client.post("task", task_data)

# mcp/server.py - Thin wrapper
@mcp.tool()
async def create_task(project_id: str, title: str, reminders: list[str] = None):
    """Create a new task."""  # MCP-specific description
    return await sdk.tasks.create_task(project_id, title, reminders=reminders)
```

### Benefits

- **Single source of truth** - Logic in one place, not duplicated
- **Testable** - Test SDK once, all clients benefit
- **Consistent** - CLI and MCP behave identically
- **Extensible** - Third-party apps can use the SDK directly

## 1. Development Setup

For local development, install in editable mode:

### Setting Up Development Dependencies

To run tests and linting, you'll need to install the development dependencies:

1. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install the project with development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

   This installs:
   - `pytest` and `pytest-asyncio` for running tests
   - `respx` for mocking HTTP requests in tests
   - `ruff` for linting and code formatting

## 1.1. Running Tests

The project includes a comprehensive test suite using `pytest`. All tests use mocked HTTP requests (via `respx`) so they run without network calls.

### Running All Tests

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Run all tests with verbose output
pytest tests/unit/test_server.py -v
```

### Running Specific Tests

```bash
# Run a specific test by name
pytest tests/unit/test_server.py::test_get_ticktick_projects -v

# Run tests matching a pattern
pytest tests/unit/test_server.py -k "update_task" -v
```

### Test Coverage

The test suite currently includes 11 tests covering:
- ✅ Core HTTP request functionality (`make_ticktick_request`)
- ✅ Getting list of projects (`get_ticktick_projects`)
- ✅ Getting list of tasks in a project (`get_ticktick_tasks`)
- ✅ Getting details of a task (via `make_ticktick_request` with GET `task/{task_id}`)
- ✅ Updating a task (`update_task`)
- ✅ Error handling for all operations
- ✅ Authorization header verification

## 1.2. Running Linting

The project uses `ruff` for linting and code formatting.

### Check for Linting Issues

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Check for linting errors
ruff check server.py tests/
```

### Auto-fix Linting Issues

```bash
# Fix auto-fixable linting issues
ruff check --fix server.py tests/
```

### Code Formatting

```bash
# Check if files need formatting
ruff format --check server.py tests/

# Format files automatically
ruff format server.py tests/
```

### Linting Configuration

Linting rules are configured in `pyproject.toml`:
- Line length: 120 characters
- Enabled checks: pycodestyle errors/warnings, pyflakes, isort, pep8-naming, pyupgrade, flake8-comprehensions, flake8-bugbear
- Complexity checks enabled (C901)

### Pre-commit Checklist

Before committing code, ensure:
1. ✅ All tests pass: `pytest tests/unit/test_server.py -v`
2. ✅ No linting errors: `ruff check server.py tests/`
3. ✅ Code is properly formatted: `ruff format --check server.py tests/`

## 1.3. Manual Integration Testing

For detailed instructions on manual functional integration testing, see [INTEGRATION-TESTING.md](./INTEGRATION-TESTING.md).

**Quick Start (Recommended):**
```bash
# Simple Python script that tests functions directly (no Docker/HTTP needed)
source venv/bin/activate
source .env
python test_integration_simple.py
```

This guide covers:
- **Simple Python script** - Direct function testing (recommended, no Docker/SSE complexity)
- Testing `list_projects` tool
- Testing `list_tasks` tool
- Testing getting task details
- Testing `update_task` tool
- Error case testing
- Docker + curl testing (advanced, requires SSE handling)

## 2. Testing Tool Changes

When you make changes to existing tools (e.g., in `server.py`) or add new ones, you need to ensure these changes are properly tested within a consistent environment. The recommended approach for testing tool changes is by using Docker.

### Docker-based Testing Workflow

1.  **Modify Tool Code:** Make your changes to `server.py` or any other relevant Python files defining your tools.

2.  **Rebuild Docker Image:**
    ```bash
    cd ticktick-mcp # Navigate to the project root
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
