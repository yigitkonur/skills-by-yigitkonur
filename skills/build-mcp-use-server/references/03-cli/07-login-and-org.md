# Login and Organization

*Read this to authenticate with Manufact Cloud and manage your organization context.*

## mcp-use login

Authenticates the CLI with Manufact Cloud using a device code flow. This is a one-time setup before using cloud commands (`deploy`, `servers`, `deployments`).

```bash
mcp-use login [options]
```

### Default flow (device code)

By default, `login` initiates a browser-based authentication:

1. CLI generates a device code and verification URL
2. Browser opens automatically (unless `--no-open`)
3. You enter the user code and authorize
4. CLI polls for up to 30 minutes for approval
5. On success, an API key is created and credentials are stored in `~/.mcp-use/config.json` (local, not shared)

**Output example (stderr):**
```
Open https://cloud.manufact.com/auth/device?user_code=ABC-123 and enter code ABC-123.
```

**Success line (stdout, human mode):**
```
Logged in as user@example.com (Acme Corp).
```

### Flags

| Flag | Type | Effect |
|------|------|--------|
| `--api-key <key>` | string | Skip device flow; use a pre-generated API key instead (mutually exclusive with `--device-code`) |
| `--device-code <code>` | string | Redeem a pre-approved device code (CI/CD pattern) |
| `--org <id-or-slug>` | string | Set active org immediately (required for headless flows when the account has no default) |
| `--no-open` | boolean | Don't auto-open browser |
| `--json` | boolean | Output JSON instead of plain text |
| `-h, --help` | boolean | Show help |

If `--api-key`/`--device-code` are both omitted, an API key is also read from `$MCP_USE_API_KEY` before falling back to the device flow.

### API key authentication

For CI/CD or unattended environments:

```bash
mcp-use login --api-key sk_live_1234567890abcdef --org acme-corp
```

Generate API keys in your Manufact Cloud account settings.

### Device code with headless CI

Pre-authorize a device code in the web UI, then redeem it in CI:

```bash
mcp-use login --device-code DEV_CODE_HERE --org staging-env
```

This avoids browser dependency and long polling in CI runs.

## mcp-use logout

Clear local cloud credentials:

```bash
mcp-use logout [options]
```

### Flags

| Flag | Type | Effect |
|------|------|--------|
| `--yes` | boolean | Skip confirmation (required in non-interactive runs) |
| `--json` | boolean | Emit `{"loggedOut":true}`; never prompts |

Deletes local cloud credentials only (`~/.mcp-use/config.json`); does not revoke the API key server-side.

## mcp-use whoami

Show your authenticated identity and active organization:

```bash
mcp-use whoami [options]
```

### Flags

| Flag | Type | Effect |
|------|------|--------|
| `--json` | boolean | Output JSON |

### Example output (human mode)

```
user@example.com — Acme Corp
```

## mcp-use org

Manage your active organization:

```bash
mcp-use org <command> [options]
```

| Subcommand | Effect |
|------------|--------|
| `list` | List memberships; active entry marked `*` in human output |
| `current` | Show the active organization |
| `use <id-or-slug>` | Save an active organization locally and best-effort update the account default |

There is no `switch` subcommand — the real subcommand is `use`. All three accept `--json` and `-h/--help`.

## Credentials location

- **Local file:** `~/.mcp-use/config.json` (read on startup by deploy/servers/deployments commands)
- **Not stored:** Device code authorization tokens are runtime-only and never persisted
- **Scope:** User-level; shared by all projects on the machine

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success (authenticated, logged out, or help shown) |
| `1` | API or auth failure |
| `2` | Confirmation required in non-interactive run (e.g., logout without `--yes`) |

## Common workflow

```bash
# One-time: authenticate
mcp-use login
# → Opens browser, user authorizes

# Verify authentication
mcp-use whoami
# → Shows user + active org

# Deploy
mcp-use deploy --org acme-prod

# Later: change active org
mcp-use org use <new-org>

# Eventually: sign out
mcp-use logout --yes
```

## Headless deployment (CI/CD)

```bash
# In CI: use API key
mcp-use login --api-key "${MCP_USE_API_KEY}" --org "${ORG_NAME}"

# Then deploy
mcp-use deploy
```

Store `MCP_USE_API_KEY` in your CI secret manager (GitHub Actions, etc.) — the CLI also reads it automatically when `login` is run with neither `--api-key` nor `--device-code` set.
