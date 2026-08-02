# CLI Overview

*Read this to understand the command inventory and which command to use for each task.*

The `mcp-use` CLI (v4.x beta) provides commands for local development, cloud authentication, deployment, and client testing. The binary is installed via:

```bash
npm install -g @mcp-use/cli@4.0.0-beta.15
# or invoked directly:
npx @mcp-use/cli@4.0.0-beta.15 dev
```

## Command Inventory

| Command | Purpose | When to use |
|---------|---------|------------|
| **`dev`** | Start dev server with HMR, Inspector, tunnel | Active development; testing tools/views locally |
| **`build`** | Build server + views into `.mcp-use/build/` | Before production deployment or local testing of prod build |
| **`typecheck`** | Refresh `.mcp-use/mcp-env.d.ts`, run TypeScript | CI/CD or local type safety check |
| **`start`** | Serve production build from `.mcp-use/build/` | Production testing or local start after build |
| **`login`** | Authenticate with Manufact Cloud | Enable cloud deploy/org/servers commands |
| **`logout`** | Clear local cloud credentials | Sign out of cloud CLI |
| **`whoami`** | Show authenticated user and active org | Verify login status |
| **`org`** | Manage active organization | Select/list orgs (exact subcommands vary) |
| **`servers`** | Manage cloud servers and env vars | Configure cloud deployments |
| **`deployments`** | Manage cloud deployments and logs | View/manage active deployments |
| **`deploy`** | Deploy to Manufact Cloud | Ship server to cloud (GitHub or upload) |
| **`client`** | Connect to and invoke MCP servers | Test server from CLI; save connections; run tools/prompts |
| **`screenshot`** | Capture view screenshot | Test MCP Apps widgets without browser |

## Global Flags

- `--help, -h` — Show help for any command
- `--version, -v` — Print CLI version
- `--path <directory>` — Project root (default: current directory)

## Key Defaults

- **Port:** `$PORT` env var, then flag `--port`, then fallback `3000`
- **Host:** `$HOST` env var, then flag `--host`, then fallback `127.0.0.1` (localhost-only by default for security)
- **Views directory:** `views/` or `<mcp-dir>/views/`
- **Build output:** `.mcp-use/build/`
- **Inspector mount (dev):** Automatically at `/mcp/inspector`; disable with `--no-inspector`

## Removed in v4.x (v2 CLI)

These commands do **not** exist in v4.0.0-beta.15. Files `04-07` and `09-13` below document why they are absent and point to migration paths:

- `mcp-use generate-types` — merged into `typecheck`
- `mcp-use introspect` — use Inspector instead
- `mcp-use serve` — use `start` instead
- `mcp-use generate-docs` — not shipped

## Next Steps

- **Local development:** read `03-mcp-use-dev.md`
- **Production build:** read `04-mcp-use-build-and-typecheck.md`
- **Cloud deployment:** read `06-mcp-use-deploy-and-cloud.md`
- **All flags reference:** read `09-flag-reference.md`
