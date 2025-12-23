# Claude Code Instructions for ticktick-access

## Required Reading

Before making changes, read and follow:
- `docs/CONTRIBUTING.md` - Version management, release workflow, development setup, architecture roadmap

## Version Bumps

**Always bump the version when making code changes that will be pushed.**

See `docs/CONTRIBUTING.md` for details, but the key points:
- Version lives in `ticktick/__init__.py`
- Patch bump (0.2.0 → 0.2.1) for bug fixes
- Minor bump (0.2.0 → 0.3.0) for new features
- Tag releases: `git tag vX.Y.Z`

Without a version bump, `pip install --upgrade` will not pick up changes.

## Pre-Commit

Run `devws precommit` before committing.

## Architecture Notes

The current architecture has the CLI handling only authentication, with task operations only available through the MCP server. See `docs/CONTRIBUTING.md` for the SDK pattern roadmap that would enable CLI task operations.

## Key Files

| File | Purpose |
|------|---------|
| `ticktick/__init__.py` | Package version (bump here) |
| `ticktick/config.py` | Config management (~/.ticktick-access/) |
| `ticktick/auth.py` | OAuth flow |
| `ticktick/cli.py` | CLI commands |
| `ticktick/mcp/server.py` | MCP server with all task tools |

## Testing MCP Changes Within Claude

After making local changes to the MCP server, you can test them without exiting your current Claude session by spawning a separate Claude process:

```bash
echo "use list_projects to show my ticktick projects" | claude -p --allowedTools "mcp__ticktick__list_projects"
```

### Flags Explained

| Flag | Purpose |
|------|---------|
| `-p` / `--print` | Non-interactive mode - prints response and exits (no REPL) |
| `--allowedTools "pattern"` | Pre-approve tools matching the pattern (skips permission prompts) |

### Tool Patterns

- `mcp__ticktick__list_projects` - Allow only the specific tool
- `mcp__ticktick__*` - Allow all ticktick MCP tools
- `mcp__*` - Allow all MCP tools (use with caution)

### Why This Works

The spawned `claude -p` process:
1. Starts fresh and loads the current MCP server code
2. Connects to the MCP server (which runs your local changes)
3. Executes the tool and returns
4. Your main Claude session continues uninterrupted

### Full Test Example

```bash
# Test list_projects
echo "list my ticktick projects" | claude -p --allowedTools "mcp__ticktick__list_projects"

# Test multiple tools
echo "create a task called 'Test task' in my Work project" | claude -p --allowedTools "mcp__ticktick__*"
```

**Note:** Ensure the MCP server is registered with Claude (`claude mcp list`) and that you've installed locally with `pip install -e .` so changes are reflected immediately.
