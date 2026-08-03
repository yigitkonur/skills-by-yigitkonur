# Cloud Deployment and Management

*Read this to deploy to Manufact Cloud and manage cloud servers.*

## mcp-use deploy

Deploys your server to Manufact Cloud:

```bash
mcp-use deploy [options]
```

### Flags

| Flag | Type | Required | Effect |
|------|------|----------|--------|
| `--org <id-or-slug>` | string | No* | Organization ID or slug (*required if account has no default) |
| `--name <name>` | string | No | Cloud server/repository name (default: `package.json#name`, else the directory name) |
| `--branch <name>` | string | No | Branch (default: current Git branch on managed upload's first link; `main` on the GitHub-linked upload path) |
| `--root-dir <path>` | string | No | Project root inside the repository/upload directory |
| `--region <region>` | string | No | Cloud region identifier (no client-side default; server-side default applies if omitted) |
| `--env <KEY=VALUE>` | string | Repeatable | Set env var (can repeat: `--env A=1 --env B=2`) |
| `--env-file <path>` | string | No | Load env vars from file (`.env` format) |
| `--build-command <cmd>` | string | No | Override the build command |
| `--start-command <cmd>` | string | No | Override the start command |
| `--dockerfile <path>` | string | No | Dockerfile path relative to the selected source root |
| `--watch-paths <glob>` | string | Repeatable | GitHub auto-deploy path filter (GitHub-only) |
| `--wait-for-ci` | boolean | No | Wait for other GitHub checks before auto-deploy (GitHub-only) |
| `--no-github` | boolean | No | Skip GitHub URL detection; upload source instead |
| `--new` | boolean | No | Create a new server instead of using the local link (requires `--yes` in JSON/non-interactive runs) |
| `--open` | boolean | No | Open the server page after a successful deployment (cannot combine with `--json`) |
| `-y, --yes` | boolean | No | Authorize confirmations and Git/repository mutations |
| `--json` | boolean | No | Emit exactly one JSON result or error; never prompts (does not itself authorize mutations — pair with `--yes`) |
| `-h, --help` | boolean | No | Show help without Git, auth, or network access |

### Examples

**Deploy via GitHub (default):**
```bash
mcp-use deploy
# Uses current remote origin + branch
```

**Upload source directly (no GitHub):**
```bash
mcp-use deploy --no-github
# Archives and uploads local files (max 80 MB)
```

**Set environment variables:**
```bash
mcp-use deploy --env DATABASE_URL=postgres://... --env API_KEY=secret
```

**Load from .env file:**
```bash
mcp-use deploy --env-file .env.production
```

**Specific organization:**
```bash
mcp-use deploy --org acme-corp-staging
```

**Non-interactive automation (headless GitHub repo creation, or managed upload):**
```bash
mcp-use deploy --json --yes
mcp-use deploy --no-github --json
```

### Prerequisites

- Run `mcp-use login` first (one-time)
- Server must build successfully (`mcp-use build`)
- Archive size limit: 80 MB — the managed-upload archive excludes `.git`, `node_modules`, build output (`dist`, `build`, `.next`, `.turbo`, `.vercel`, `.output`, `out`, `target`), `.mcp-use`, `.env*`, caches (`.cache`, `.parcel-cache`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache`, `__pycache__`, `.venv`, `venv`), `coverage`, `.nyc_output`, OS metadata, and symbolic links

Deploy is a self-contained command — its `.mcp-use/cloud/link.json` local link file (see below) is written by `mcp-use deploy` itself; a prior `mcp-use build` output is not consumed by deploy (the cloud build runs its own build server-side).

## mcp-use login

Authenticate with Manufact Cloud via device code flow:

```bash
mcp-use login [options]
```

### Flags

| Flag | Type | Effect |
|------|------|--------|
| `--api-key <key>` | string | Authenticate with an API key (mutually exclusive with `--device-code`) |
| `--device-code <code>` | string | Redeem a pre-approved device code |
| `--org <id-or-slug>` | string | Select the active organization (required for headless login when the account has no default) |
| `--no-open` | boolean | Do not open the verification URL |
| `--json` | boolean | Emit machine-readable output |
| `-h, --help` | boolean | Show help |

### Device code flow (default)

Initiates browser-based authentication:

1. `mcp-use login` → CLI writes `Open <verification-url> and enter code <user-code>.` to stderr
2. Browser opens automatically (unless `--no-open`)
3. Visit the URL, enter the code, authorize
4. CLI polls for up to 30 minutes waiting for approval
5. On success, an API key is created and credentials are stored locally at `~/.mcp-use/config.json`; if the account has multiple organizations and none is selected via `--org`, an interactive TTY prompts for one (non-interactive/`--json` runs fail with an actionable "select an organization" error)

Example output (stderr):

```
Open https://cloud.manufact.com/auth/device?user_code=ABC-123 and enter code ABC-123.
```

Example success line (stdout, human mode):

```
Logged in as user@example.com (Acme Corp).
```

### Headless authentication

For CI/CD or headless environments:

```bash
# Option 1: Use an API key (also read from $MCP_USE_API_KEY if --api-key/--device-code omitted)
mcp-use login --api-key sk_live_...

# Option 2: Redeem a pre-approved device code
mcp-use login --device-code DEV_CODE_HERE --org acme-corp
```

`--no-open` (or a non-TTY stdout) also switches the device-code flow itself into headless polling mode without launching a browser.

## mcp-use logout

Clear local cloud credentials:

```bash
mcp-use logout [options]
```

### Flags

| Flag | Type | Effect |
|------|------|--------|
| `--yes` | boolean | Confirm without prompting (required in non-interactive mode; interactively skipping confirmation exits `0`) |
| `--json` | boolean | Emit `{"loggedOut":true}`; never prompts |

Deletes local cloud credentials only (`~/.mcp-use/config.json`); does not revoke the API key server-side.

## mcp-use whoami

Show authenticated user and active organization:

```bash
mcp-use whoami [options]
```

### Flags

| Flag | Type | Effect |
|------|------|--------|
| `--json` | boolean | Emit a machine-readable identity object |

### Example output (human mode)

```
user@example.com — Acme Corp
```

## mcp-use org

Manage the active cloud organization:

```bash
mcp-use org <command> [options]
```

| Subcommand | Effect |
|------------|--------|
| `list` | List memberships; active entry marked `*` in human output. Options: `--json`, `-h/--help` |
| `current` | Show the active organization. Options: `--json`, `-h/--help` |
| `use <id-or-slug>` | Save an active organization locally and best-effort update the account default. Options: `--json`, `-h/--help` |

There is no `switch` subcommand — use `mcp-use org use <id-or-slug>`.

Exit codes: `0` success/help, `2` invalid arguments or no active organization, `1` authentication/API failure.

## mcp-use servers

Manage cloud servers and their environment variables:

```bash
mcp-use servers <command> [options]
```

| Subcommand | Effect |
|------------|--------|
| `list` | List servers. Options: `--org <id-or-slug>`, `--limit <n>` (default 30, range 1-100), `--skip <n>` (default 0), `--json`, `-h/--help` |
| `get <id-or-slug>` | Show one server. Options: `--org <id-or-slug>`, `--json`, `-h/--help` |
| `update <id-or-slug>` | Update name/description/branch/root-dir/build-command/start-command/watch-paths/deploy-branches/wait-for-ci. Pass an empty value to clear a path/command/glob field. `--wait-for-ci` and `--no-wait-for-ci` are mutually exclusive |
| `delete <id-or-slug>` | Delete a server. Options: `--org <id-or-slug>`, `--yes`, `--json`, `-h/--help` |
| `env list <server>` | List env var keys/metadata (values never returned). Options: `--org`, `--branch <name>`, `--json`, `-h/--help` |
| `env set <server> <KEY=VALUE>` | Create/update a value. Options: `--org`, `--branch <name>` (default: production), `--secret`, `--json`, `-h/--help` |
| `env unset <server> <key>` | Delete a value. Options: `--org`, `--branch <name>`, `--yes`, `--json`, `-h/--help` |

## mcp-use deployments

Manage deployments and view logs:

```bash
mcp-use deployments <command> [options]
```

| Subcommand | Effect |
|------------|--------|
| `list` | List deployments. Options: `--org <id-or-slug>`, `--server <id>`, `--limit <n>` (default 30, range 1-100), `--skip <n>` (default 0), `--json`, `-h/--help` |
| `get <deployment-id>` | Show one deployment. Options: `--json`, `-h/--help` |
| `logs <deployment-id>` | Read logs. Options: `--build` (build logs instead of runtime), `--follow` (poll until terminal status), `--json` (with `--follow`, emitted only at completion), `-h/--help` |
| `restart <deployment-id>` | Restart. Options: `--branch <name>` (override source branch), `--follow`, `--json`, `-h/--help` |
| `stop <deployment-id>` | Stop. Options: `--yes`, `--json`, `-h/--help` |
| `delete <deployment-id>` | Delete. Options: `--yes`, `--json`, `-h/--help` |

## Typical workflow

```bash
# One-time setup
mcp-use login

# Local development
npm run dev
npm run build

# Deploy to cloud
mcp-use deploy --org my-org --env API_KEY=secret
```

## Environment variables in deployment

All `--env` vars are passed to your server at runtime and available via `process.env`. Common patterns:

```bash
mcp-use deploy \
  --env DATABASE_URL=postgres://... \
  --env OPENAI_API_KEY=sk-... \
  --env NODE_ENV=production
```

Or load from file:

```bash
mcp-use deploy --env-file .env.production
```
