# Login and Organization

*Read this to authenticate with Manufact Cloud and manage your organization context.*

## mcp-use login

Authenticates the CLI with Manufact Cloud using a device code flow. This is a one-time setup before using cloud commands (`deploy`, `servers`, `deployments`).

```bash
mcp-use login [options]
```

### Default flow (device code)

By default, `login` initiates a browser-based authentication:

1. CLI generates a user code and verification URL
2. Browser opens automatically
3. You enter the user code and authorize
4. CLI polls for up to 30 minutes for approval
5. Credentials are stored in `~/.mcp-use/config.json` (local, not shared)

**Output example:**
```
To authenticate, visit:
  https://cloud.manufact.com/auth/device?user_code=ABC-123

Waiting for authorization... (30 minutes)
✓ Authenticated as user@example.com
```

### Flags

| Flag | Type | Effect |
|------|------|--------|
| `--api-key <key>` | string | Skip device flow; use a pre-generated API key instead |
| `--device-code <code>` | string | Redeem a pre-approved device code (CI/CD pattern) |
| `--org <id-or-slug>` | string | Set active org immediately (required for headless flows) |
| `--no-open` | boolean | Don't auto-open browser |
| `--json` | boolean | Output JSON instead of plain text |

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
| `--json` | boolean | Output JSON |

## mcp-use whoami

Show your authenticated identity and active organization:

```bash
mcp-use whoami [options]
```

### Flags

| Flag | Type | Effect |
|------|------|--------|
| `--json` | boolean | Output JSON |

### Example output

```
Authenticated as: user@example.com
Active organization: acme-prod (id: org_abc123)
```

## mcp-use org

Manage your active organization (exact subcommands vary; use `mcp-use org --help`):

```bash
mcp-use org <subcommand> [options]
```

Used to switch between organizations or list your memberships. Consult your CLI's help text for current subcommands.

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

# Later: switch org
mcp-use org <new-org>

# Eventually: sign out
mcp-use logout --yes
```

## Headless deployment (CI/CD)

```bash
# In CI: use API key
mcp-use login --api-key "${MANUFACT_API_KEY}" --org "${ORG_NAME}"

# Then deploy
mcp-use deploy
```

Store `MANUFACT_API_KEY` in your CI secret manager (GitHub Actions, etc.).
