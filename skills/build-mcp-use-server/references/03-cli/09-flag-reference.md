# Flag Reference

*Read this for the comprehensive matrix of all CLI flags and their defaults.*

## Command × Flag Matrix

| Flag | dev | build | typecheck | start | deploy | login | logout | whoami |
|------|-----|-------|-----------|-------|--------|-------|--------|--------|
| `-p, --port <n>` | ✓ | | | ✓ | | | | |
| `--host <host>` | ✓ | | | ✓ | | | | |
| `--entry <path>` | ✓ | ✓ | ✓ | | | | | |
| `--mcp-dir <dir>` | ✓ | ✓ | ✓ | | | | | |
| `--views-dir <dir>` | ✓ | ✓ | | | | | | |
| `--path <dir>` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `--tunnel` | ✓ | | | ✓ | | | | |
| `--no-open` | ✓ | | | | | | | |
| `--no-inspector` | ✓ | | | | | | | |
| `--source-maps` | | ✓ | | | | | | |
| `--inline` | | ✓ | | | | | | |
| `--with-inspector` | | | | ✓ | | | | |
| `--` (tsc args) | | | ✓ | | | | | |
| `--org <id-or-slug>` | | | | | ✓ | ✓ | | |
| `--name <name>` | | | | | ✓ | | | |
| `--branch <name>` | | | | | ✓ | | | |
| `--root-dir <path>` | | | | | ✓ | | | |
| `--region <region>` | | | | | ✓ | | | |
| `--env <KEY=VALUE>` | | | | | ✓ | | | |
| `--env-file <path>` | | | | | ✓ | | | |
| `--build-command <cmd>` | | | | | ✓ | | | |
| `--no-github` | | | | | ✓ | | | |
| `--yes` | | | | | ✓ | | | ✓ |
| `--api-key <key>` | | | | | | ✓ | | |
| `--device-code <code>` | | | | | | ✓ | | |
| `--no-open` | | | | | | ✓ | | |
| `--json` | | | | | | ✓ | ✓ | ✓ |
| `--help, -h` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `--version, -v` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## Global Defaults

| Variable | Default | Precedence |
|----------|---------|-----------|
| **Port** | `3000` | flag `--port` > env `$PORT` > `3000` |
| **Host** | `127.0.0.1` | flag `--host` > env `$HOST` > `127.0.0.1` |
| **Entry** | `package.json#main` | flag `--entry` > auto-detect |
| **Views dir** | `views/` or `<mcp-dir>/views/` | flag `--views-dir` > auto-detect |
| **MCP dir** | project root | flag `--mcp-dir` > auto-detect |
| **Project path** | current dir | flag `--path` > current dir |

## Notable flag behaviors

### dev / start

- `--port` and `--host` respect env vars (`$PORT`, `$HOST`) for containerized deployments
- `--tunnel` exposes `https://<subdomain>.local.mcp-use.run/mcp` (24h expiry, 5 tunnels per IP)
- `--no-open` useful for headless/CI environments
- `--no-inspector` skips Inspector; useful for resource-constrained environments

### build

- `--source-maps` emits `.js.map` files for debugging minified code
- `--inline` embeds view JS/CSS in MCP resources (larger payload, no asset downloads)
- Typecheck always runs; no `--no-typecheck` flag

### deploy

- `--env` repeatable; `--env A=1 --env B=2` sets multiple vars
- `--env-file` reads `.env` format
- `--no-github` required if GitHub origin is unavailable or you want to upload source directly
- Archive size limit: 80 MB (`.git`, `node_modules`, `.mcp-use/build`, `dist` are auto-excluded)

### login / logout / whoami

- `--json` outputs machine-readable format (useful in scripts)
- `--api-key` skips device flow (for CI/CD)
- `--device-code` redeems pre-approved codes (CI-friendly)
- `--org` required for headless flows (no default org)

## Environment variable overrides

These take effect when the corresponding flag is not passed:

- `$PORT` — used by dev/start if `--port` not specified
- `$HOST` — used by dev/start if `--host` not specified
- `$NODE_ENV` — forced to `production` by start command
- `$MCP_URL` — set automatically by dev if `--tunnel` used; can override

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success (or help/version shown) |
| `1` | Runtime error (build failure, server startup error, auth failure) |
| `2` | Invalid arguments or missing required flag |

## Repeatable flags

- `--env <KEY=VALUE>` — can repeat for multiple env vars
- `-H <header>` (screenshot only) — can repeat for multiple custom headers
