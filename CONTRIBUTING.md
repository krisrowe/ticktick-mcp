# Contributing to ticktick-access

This guide covers the architecture, how to add tools and profile
fields, and the testing standards. For installation, deployment,
and operation, see [README.md](README.md).

## Architecture

```
ticktick/
├── __init__.py        # App composition root: name, Profile, mcp/admin CLIs
├── auth.py            # OAuth helper used by `ticktick auth login`
├── cli.py             # Click group for the `ticktick` command
├── mcp/
│   └── tools.py       # Plain async tool functions (discovered by mcp-app)
└── sdk/
    ├── client.py      # TickTickClient (HTTP) + TickTickSDK facade
    ├── projects.py    # Project operations (module-level async functions)
    └── tasks.py       # Task operations (module-level async functions)

tests/
├── unit/              # Sociable SDK + tool tests
│   ├── conftest.py    # XDG isolation, current_user fixture
│   ├── sdk/
│   └── test_*.py
└── framework/         # mcp-app conformance suite
    ├── conftest.py    # Provides the App fixture
    └── test_framework.py
```

### Layer rules

- **All business logic lives in `ticktick/sdk/`.** Tools and the
  CLI are thin wrappers.
- **MCP tools are plain async functions in `ticktick/mcp/tools.py`.**
  No decorators, no framework imports. mcp-app discovers public
  async functions in this module and registers them — function name
  becomes tool name, docstring becomes description, type hints
  become schema. Functions starting with `_` are skipped.
- **The SDK reads identity from `mcp_app.context.current_user`,**
  not from environment variables or config files. The
  `TickTickSDK` facade in `sdk/client.py` is where identity meets
  the SDK; module-level functions in `projects.py` and `tasks.py`
  take an explicit `TickTickClient` so they remain identity-free
  and easy to test in isolation.
- **The `ticktick` CLI is just an OAuth helper.** All user and
  task operations go through MCP tools (via `ticktick-mcp`) or
  user management (via `ticktick-admin`). Don't add task or
  project subcommands to `ticktick`.

### Composition root

`ticktick/__init__.py` declares the `App` object. mcp-app derives
two click groups from it (`app.mcp_cli`, `app.admin_cli`) which
are wired up as console scripts in `pyproject.toml`. To change
the app name, profile, or store backend, edit this file.

## Profile fields drive operator UX

The `Profile` Pydantic model in `ticktick/__init__.py` is the
**single source of truth** for what per-user credentials this app
needs. With `profile_expand=True`, mcp-app's admin CLI generates
typed flags for each field — `--access-token` for the current
field — and surfaces each field's `Field(description=...)` as the
flag's help text.

That help text is the re-discovery path for an operator returning
months later to rotate a credential. When you add or change a
profile field:

1. **Always include `Field(description=...)`** — it must say what
   the credential is, what system it authenticates to, and where
   to obtain a fresh one. Operators read this from
   `ticktick-admin users add --help`.
2. **Update the README** — the "TickTick OAuth credentials" section
   is the long-form version of the same information.
3. **Add or extend tests** under `tests/unit/sdk/` that cover any
   new SDK code paths reading the new field.

## Adding an MCP tool

1. Add an async method to `TickTickSDK` in `sdk/client.py` that
   returns a serializable dict and delegates to a module-level
   function in `sdk/projects.py` or `sdk/tasks.py` (or a new SDK
   module if it's a new domain).
2. Add the underlying module-level function with `client` as its
   first argument.
3. Add a public `async def` to `ticktick/mcp/tools.py` with a
   clear docstring (becomes the MCP tool description) and full
   type hints (become the schema). Wrap calls to the SDK in a
   try/except for `AuthenticationError` and `APIError` so the
   tool returns an error envelope instead of raising — MCP
   clients handle envelopes more gracefully than exceptions.
4. Add SDK tests in `tests/unit/sdk/`. The `test_every_tool_has_sdk_test_coverage`
   conformance test in `tests/framework/` will fail if a tool's
   SDK methods don't appear in the SDK test files.

## Testing

Sociable unit tests by policy: minimal mocking, full code paths,
isolation through env vars and temp directories. See
[the sociable-unit-tests skill](https://github.com/echo-skill/echoskill/tree/main/coding/sociable-unit-tests)
for the full philosophy.

### Boundary strategy

ticktick-access uses **Option A** — mock at the network call. The
TickTick API is the only system boundary; everything inside the
SDK runs unmodified in tests. [respx](https://lundberg.github.io/respx/)
intercepts outbound `httpx` requests, returns canned responses, and
asserts on outgoing payloads. No internal collaborators are mocked.

### Test layout

- `tests/unit/conftest.py` — XDG isolation (autouse) and the
  `authenticated_user` fixture that sets `current_user`.
- `tests/unit/sdk/test_projects.py`,
  `tests/unit/sdk/test_tasks.py` — module-level SDK functions.
- `tests/unit/sdk/test_sdk_facade.py` — `TickTickSDK` classmethods,
  including multi-user isolation.
- `tests/unit/test_mcp_tools.py` — MCP tool wrappers with their
  error-envelope contracts.
- `tests/unit/test_cli.py` — `ticktick auth login` via Click's
  in-process `CliRunner`.
- `tests/framework/test_framework.py` — re-exports mcp-app's
  conformance suite. It runs against the `app` fixture from
  `tests/framework/conftest.py`. This file is identical across
  every mcp-app solution.

### Run tests

```bash
make test              # unit + framework, auto-creates .venv on first run
make framework-test    # only the mcp-app conformance suite
pytest tests/unit/sdk/test_projects.py -v   # one file
```

The default `pytest` invocation excludes `tests/integration/`
(see `[tool.pytest.ini_options]` in `pyproject.toml`).

## Environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `SIGNING_KEY` | HMAC key for JWTs (required for HTTP serve) | none — startup fails |
| `JWT_AUD` | Expected JWT audience | unset (audience not validated) |
| `APP_USERS_PATH` | Per-user data root | `$XDG_DATA_HOME/ticktick/users/` |
| `TOKEN_DURATION_SECONDS` | New-token lifetime | ~10 years |
| `TICKTICK_CLIENT_ID` | Default for `ticktick auth login --client-id` | none |
| `TICKTICK_CLIENT_SECRET` | Default for `ticktick auth login --client-secret` | none |
| `LOG_LEVEL` | Standard Python log level | `INFO` |

The OAuth helper (`ticktick auth login`) uses `TICKTICK_CLIENT_ID`
and `TICKTICK_CLIENT_SECRET` so secrets stay out of shell history.

## Releasing and local verification

Use this checklist before pushing a runtime-touching change, and
again before redeploying. Skip steps that don't apply (the bullets
say when each one matters).

### 1. Bump the version (runtime-touching changes only)

`__version__` lives in **two** places that must move together:

- `ticktick/__init__.py` — `__version__ = "X.Y.Z"`
- `pyproject.toml` — `[project] version = "X.Y.Z"`

Bump both in the same commit as the change. `pipx install --upgrade`
only re-installs when the version number rises, so without a bump
downstream installs stay on the old code.

| Change type | Bump |
|-------------|------|
| Bug fix, internal cleanup | patch (0.5.0 → 0.5.1) |
| New tool, new profile field, new flag | minor (0.5.0 → 0.6.0) |
| Removed tool, renamed CLI, profile schema break | major (0.5.0 → 1.0.0) |

Documentation-only changes don't need a bump.

### 2. Refresh the locally-installed CLIs

If you installed via `pipx install -e .`, the `ticktick`,
`ticktick-mcp`, and `ticktick-admin` entry points already track
the working tree — no action needed for source edits inside
existing modules.

Reinstall is only required when:

- `pyproject.toml` `[project.scripts]` or `[project.entry-points]`
  changed (new CLI, renamed CLI, new entry point group)
- The package wasn't installed editable in the first place

```bash
pipx install -e . --force
```

Confirm:

```bash
ticktick --version          # should print the new version
which ticktick-admin         # should resolve to ~/.local/bin/ticktick-admin
```

### 3. Run the test suites

```bash
make test                    # unit + framework conformance
```

Both must be green before push. If only the framework suite needs
re-running (e.g., after upgrading mcp-app):

```bash
make framework-test
```

### 4. Live local validation (stdio)

Unit and conformance tests don't exercise the real MCP transport.
Register the server with a real client and invoke at least one
tool:

```bash
claude mcp add ticktick -- ticktick-mcp stdio --user local
```

Then ask Claude to list your TickTick projects. A read-only call
like `list_projects` is the right smoke test — no mutation, no
cost beyond the API roundtrip.

### 5. Optional: scripted smoke test via `claude -p`

For a fast, repeatable, non-interactive check that exercises a
read-only tool end-to-end through the MCP protocol:

```bash
claude -p "List my ticktick projects and report how many you found" \
    --allowedTools "mcp__ticktick__list_projects"
```

Pick a prompt that's cheap, fast, and safe (read-only tool, no
mutation). Skip this if `claude` CLI isn't available in your
environment.

### 6. Tag and push

```bash
git tag vX.Y.Z
git push origin main --tags
```

### 7. After cloud redeploy (HTTP deployments only)

When you've redeployed the HTTP server (e.g. via `gapp deploy`),
verify the running instance:

```bash
ticktick-admin probe
```

`probe` checks `/health` and round-trips the MCP tool list. If it
reports `MCP: ok` and lists every expected tool, the deploy is
serving the new code.
