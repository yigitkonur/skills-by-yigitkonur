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
| `--name <name>` | string | No | Deployment name (default: inferred from git) |
| `--branch <name>` | string | No | Git branch to deploy (default: current branch) |
| `--root-dir <path>` | string | No | Root dir to deploy (default: current directory) |
| `--region <region>` | string | No | Cloud region (default: us-east-1 or account default) |
| `--env <KEY=VALUE>` | string | Repeatable | Set env var (can repeat: `--env A=1 --env B=2`) |
| `--env-file <path>` | string | No | Load env vars from file (`.env` format) |
| `--build-command <cmd>` | string | No | Custom build command (overrides default) |
| `--no-github` | boolean | No | Skip GitHub URL detection; upload source instead |
| `--yes` | boolean | No | Skip confirmation prompt |

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

### Prerequisites

- Run `mcp-use login` first (one-time)
- Server must build successfully (`mcp-use build`)
- Archive size limit: 80 MB (excluding `.git`, `node_modules`, `.mcp-use/build`, `dist`, etc.)

## mcp-use login

Authenticate with Manufact Cloud via device code flow:

```bash
mcp-use login [options]
```

### Flags

| Flag | Type | Effect |
|------|------|--------|
| `--api-key <key>` | string | Authenticate with pre-generated API key |
| `--device-code <code>` | string | Redeem pre-approved device code |
| `--org <id-or-slug>` | string | Set active organization (required for headless) |
| `--no-open` | boolean | Do not open browser for auth |
| `--json` | boolean | Machine-readable output |

### Device code flow (default)

Initiates browser-based authentication:

1. `mcp-use login` → CLI displays a user code + verification URL
2. Browser opens automatically (unless `--no-open`)
3. Visit URL, enter user code, authorize
4. CLI polls for 30 minutes waiting for approval
5. On success, credentials stored locally

Example output:

```
To authenticate, visit:
  https://cloud.manufact.com/auth/device?user_code=ABC-123

Waiting for authorization... (30 minutes)
✓ Authorized as user@example.com
```

### Headless authentication

For CI/CD or headless environments:

```bash
# Option 1: Use API key
mcp-use login --api-key sk_live_...

# Option 2: Use pre-approved device code
mcp-use login --device-code DEV_CODE_HERE --org acme-corp
```

## mcp-use logout

Clear local cloud credentials:

```bash
mcp-use logout [options]
```

### Flags

| Flag | Type | Effect |
|------|------|--------|
| `--yes` | boolean | Skip confirmation (required in non-interactive mode) |
| `--json` | boolean | Machine-readable output |

## mcp-use whoami

Show authenticated user and active organization:

```bash
mcp-use whoami [options]
```

### Flags

| Flag | Type | Effect |
|------|------|--------|
| `--json` | boolean | Machine-readable output |

### Example output

```
Authenticated as: user@example.com
Active organization: acme-corp (id: org_abc123)
```

## mcp-use org

Manage active organization:

```bash
mcp-use org [subcommand] [options]
```

Subcommands and exact flags are implementation-specific. Use `mcp-use org --help` for current subcommands.

## mcp-use servers

Manage cloud servers and environment variables:

```bash
mcp-use servers [subcommand] [options]
```

Subcommands and exact flags are implementation-specific. Use `mcp-use servers --help` for current subcommands.

## mcp-use deployments

Manage active cloud deployments and view logs:

```bash
mcp-use deployments [subcommand] [options]
```

Subcommands and exact flags are implementation-specific. Use `mcp-use deployments --help` for current subcommands.

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
