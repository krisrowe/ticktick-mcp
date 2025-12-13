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
