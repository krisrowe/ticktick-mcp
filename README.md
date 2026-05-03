# ticktick-access

CLI and MCP server for [TickTick](https://ticktick.com) task management.
Wraps the TickTick Open API as MCP tools so AI agents (Claude Code,
Gemini CLI, Claude.ai, and any MCP client) can read and modify your
projects and tasks.

The package installs three commands:

- `ticktick-mcp` — MCP server (HTTP and stdio transports)
- `ticktick-admin` — user and deployment management
- `ticktick` — small OAuth helper to obtain a TickTick access token

The MCP server runs locally over stdio for personal use, or over HTTP
for multi-user shared deployments. Per-user TickTick tokens live in
the user store, never in shared config files or environment variables.

Built on [mcp-app](https://github.com/echomodel/mcp-app).

## Install

Requires Python 3.11+ and [pipx](https://pipx.pypa.io/).

```bash
pipx install git+https://github.com/echomodel/ticktick-mcp.git
```

This installs `ticktick`, `ticktick-mcp`, and `ticktick-admin` on your
`PATH`.

## TickTick OAuth credentials (one-time)

Each user needs a TickTick access token. To get one:

1. Register an app at [developer.ticktick.com](https://developer.ticktick.com/).
2. Set the OAuth redirect URI to `http://localhost:8080`.
3. Note the **Client ID** and **Client Secret**.
4. Run the OAuth helper:

   ```bash
   ticktick auth login \
       --client-id <client-id> \
       --client-secret <client-secret>
   ```

   Or, to keep secrets off the command line:

   ```bash
   export TICKTICK_CLIENT_ID=<client-id>
   export TICKTICK_CLIENT_SECRET=<client-secret>
   ticktick auth login
   ```

   The browser opens, you authorize the app, and the access token
   prints to stdout. TickTick tokens currently expire after roughly
   24 hours, so you will repeat this when a token expires.

The token then goes into either a local user record (for stdio mode)
or a deployed user record (for HTTP mode) — see below.

## Run locally (stdio)

For personal use on a single machine.

### 1. Configure local mode and register the local user

```bash
ticktick-admin connect local
ticktick-admin users add local --access-token <ticktick-token>
```

`connect local` writes `~/.config/ticktick/setup.json` so subsequent
`ticktick-admin` commands target the local user store.
`users add local` writes the user record (with the TickTick token in
the profile) under `$XDG_DATA_HOME/ticktick/users/`.

When the TickTick token expires, rotate it without re-registering:

```bash
ticktick-admin users update-profile local access_token <new-token>
```

### 2. Register the MCP server with your client

**Claude Code:**

```bash
claude mcp add ticktick -- ticktick-mcp stdio --user local
```

**Gemini CLI:**

```bash
gemini mcp add ticktick --command ticktick-mcp --args "stdio --user local"
```

The `--user local` flag tells the MCP server which user record to
load when running over stdio.

### 3. Smoke test

In your MCP client, ask the agent to list your TickTick projects.
The server returns project IDs, names, and metadata via the
`list_projects` tool.

## Deploy (HTTP)

For shared, multi-user, always-on access — typically used with web
clients like [Claude.ai](https://claude.ai/) and remote agent
deployments.

### Runtime contract

Any HTTP deployment must provide:

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `SIGNING_KEY` | Yes | — startup fails | HMAC key for signing JWTs (32+ random chars) |
| `APP_USERS_PATH` | Yes for persistence | `~/.local/share/ticktick/users/` | Directory holding per-user JSON records (must be persistent storage) |
| `JWT_AUD` | No | unset | Expected JWT `aud` claim. If unset, audience is not validated |
| `TOKEN_DURATION_SECONDS` | No | ~10 years | Lifetime of newly issued user tokens |
| `LOG_LEVEL` | No | `INFO` | Standard Python log level |

The server:

- listens on `0.0.0.0:8080` (override with `--host` / `--port`)
- serves the MCP transport at `/`
- serves a `GET /health` endpoint (no auth) returning `{"status":"ok"}`
- serves `/admin/users`, `/admin/tokens`, `/admin/users/{email}/profile`
  (auth via JWT signed with `SIGNING_KEY`, `scope=admin`)
- handles its own auth — the platform must allow unauthenticated HTTP
  through to the app

Start command (any process supervisor, including a Dockerfile `CMD`):

```bash
ticktick-mcp serve --host 0.0.0.0 --port 8080
```

### Docker

A baseline Dockerfile ships in this repo. To build and run:

```bash
docker build -t ticktick-access .
docker run -p 8080:8080 \
    -e SIGNING_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" \
    -v $(pwd)/.users:/data/users \
    -e APP_USERS_PATH=/data/users \
    ticktick-access
```

The same image runs anywhere a Python container runs — Cloud Run,
Fly, Render, Heroku (via Buildpacks), Railway, Kubernetes, ECS,
bare metal.

### gapp (Cloud Run)

If you use [gapp](https://github.com/echomodel/gapp), `gapp.yaml`
describes the Cloud Run deployment with managed `SIGNING_KEY` and
`APP_USERS_PATH`. Deploy with:

```bash
gapp deploy
```

gapp generates and stores `SIGNING_KEY` in Secret Manager on first
deploy and provisions a persistent volume for `APP_USERS_PATH`.

This is one supported path among many — the runtime contract above
is what matters; gapp is convenience.

## Connect the admin CLI to a deployed instance

After deploying, `ticktick-admin` needs the deployment URL and the
`SIGNING_KEY` value to manage users.

```bash
ticktick-admin connect https://your-ticktick-mcp.example.com \
    --signing-key <signing-key>
```

Retrieve `<signing-key>` from wherever your deployment stored it:

- **gapp**: `gapp_secret_get(name="signing-key", plaintext=True)` via
  the gapp MCP, or `gcloud secrets versions access latest --secret=ticktick-mcp-signing-key`.
- **GCP Secret Manager directly**:
  `gcloud secrets versions access latest --secret=<your-secret-name>`.
- **GitHub Actions / CI secrets**: read from your CI provider's UI.
- **Other secret managers**: use that tool's read command.

`connect` saves the URL and signing key to
`~/.config/ticktick/setup.json` so subsequent admin commands run
without repeating the flags. Switch back to local at any time with
`ticktick-admin connect local`.

## Manage users on a deployed instance

```bash
# Register a new user. Their TickTick token goes in the profile.
ticktick-admin users add alice@example.com --access-token <token>

# List registered users.
ticktick-admin users list

# Read the current profile (which fields are set, which are missing).
ticktick-admin users get-profile alice@example.com

# Rotate a user's TickTick token after the old one expires.
ticktick-admin users update-profile alice@example.com access_token <new-token>

# Mint an additional MCP-server token for an existing user
# (e.g. to register the MCP server in another client).
ticktick-admin tokens create alice@example.com

# Revoke a user.
ticktick-admin users revoke alice@example.com
```

Run `ticktick-admin users add --help` to see the typed flags
generated from the `Profile` model — the `--access-token` flag's help
text describes what the token is and how to obtain one.

## Verify and register MCP clients

### Probe the deployment

```bash
ticktick-admin probe
```

`probe` checks `/health`, then opens an MCP session and round-trips
the tool list. Output names every registered tool — `list_projects`,
`count_projects`, `list_tasks`, `create_task`, `update_task`,
`complete_task`, `delete_task`. If the deployment is healthy and
tools are exposed, `probe` reports `MCP: ok`.

Add `--json` for structured output suitable for scripts and agents.

### Inspect tools on the running deployment

If `probe` reports an issue or you want a closer look at what the
deployment is exposing, the `tools` group invokes JSON-RPC against
the live MCP transport:

```bash
ticktick-admin tools list                       # enumerate tool names
ticktick-admin tools show list_projects         # show schema and example
ticktick-admin tools call list_projects         # invoke with no args
ticktick-admin tools call create_task --arg project_id=<id> --arg title='Hello'
```

`tools call` mints a short-lived user-scoped token (default: first
registered user; override with `--user <email>`) and round-trips
through the deployment's MCP layer the same way an MCP client would.

### End-to-end smoke test

```bash
ticktick-admin safe-tool --invoke
```

Invokes `count_projects` end-to-end through the deployment's MCP
transport — the full path from JWT validation through tool dispatch
to TickTick's API and back. The response is just a count, so it
exercises the full stack without surfacing any user-authored content
in the admin output.

### Generate MCP client registration commands

```bash
ticktick-admin register --user alice@example.com
```

Mints a fresh user-scoped token and emits ready-to-paste registration
commands for Claude Code, Gemini CLI, and the Claude.ai URL form,
each pre-filled with the deployment URL and the new token. Add
`--json` for structured output suitable for scripts and agents.

Limit to a specific client:

```bash
ticktick-admin register --user alice@example.com --client claude
ticktick-admin register --user alice@example.com --client gemini
ticktick-admin register --user alice@example.com --client claude.ai
```

### Manual MCP client registration

If you prefer not to use `register`, the patterns are:

**Claude Code:**

```bash
claude mcp add --scope user ticktick \
    --transport http \
    --url https://your-deployment/ \
    --header "Authorization: Bearer ${TICKTICK_TOKEN}"
```

**Gemini CLI:**

```bash
gemini mcp add ticktick \
    --transport http \
    --url https://your-deployment/ \
    --header "Authorization: Bearer ${TICKTICK_TOKEN}"
```

Both clients expand `${VAR}` in headers, so put the token in your
shell environment rather than in the registration command.

## MCP tools exposed

| Tool | Description |
|------|-------------|
| `list_projects` | List all TickTick projects (lists) |
| `count_projects` | Return the number of projects (safe smoke-test tool — see below) |
| `list_tasks` | List tasks in a project |
| `create_task` | Create a new task |
| `update_task` | Update an existing task |
| `complete_task` | Mark a task as completed |
| `delete_task` | Permanently delete a task |

## Troubleshooting

**"No TickTick access token" / 401 from TickTick** — the user's
token expired. Run `ticktick auth login`, then
`ticktick-admin users update-profile <email> access_token <new>`.

**"User not found" on the deployment** — register the user with
`ticktick-admin users add`.

**MCP client can't connect / 401 / 403 from your deployment** —
the user-scoped MCP token has expired or was revoked. Mint a new
one with `ticktick-admin tokens create <email>` and update the
client's registration.

**Admin commands fail with "Not configured"** — run
`ticktick-admin connect local` or
`ticktick-admin connect <url> --signing-key <key>`.

## Testing

Unit tests run offline with no credentials:

```bash
make test            # creates venv on first run, then runs all tests
```

The `tests/framework/` directory carries mcp-app's reusable
conformance suite — auth enforcement, admin endpoints, JWT handling,
CLI wiring, tool protocol, SDK coverage. Run it directly with:

```bash
make framework-test
```

## Further reading

- [CONTRIBUTING.md](CONTRIBUTING.md) — architecture, adding tools,
  profile fields, testing standards.
- [mcp-app](https://github.com/echomodel/mcp-app) — the framework
  this app is built on.

## License

MIT
