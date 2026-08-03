# Flag Reference

*Read this for the comprehensive matrix of all CLI flags and their defaults.*

Two distinct dispatch groups exist in `bin/main.ts`: `dev`/`build`/`typecheck`/`start` share one hand-rolled parser (`bin/args.ts`) with a common flag set; `login`/`logout`/`whoami`/`org`/`servers`/`deployments`/`deploy`/`client`/`screenshot` each own a separate `node:util` `parseArgs` call with their own flag set. Flags do not carry across groups — e.g. `--path` (project root) is dev/build/typecheck/start only; `deploy` takes an optional `[path]` **positional**, not a `--path` flag; the cloud commands have no `--path`/`--entry`/`--mcp-dir`/`--views-dir` at all.

## Command × Flag Matrix — dev / build / typecheck / start

| Flag | dev | build | typecheck | start |
|------|-----|-------|-----------|-------|
| `-p, --port <n>` | ✓ | | | ✓ |
| `--host <host>` | ✓ | | | ✓ |
| `--entry <path>` | ✓ | ✓ | ✓ | |
| `--mcp-dir <dir>` | ✓ | ✓ | ✓ | |
| `--views-dir <dir>` | ✓ | ✓ | | |
| `--path <dir>` | ✓ | ✓ | ✓ | ✓ |
| `--tunnel` | ✓ | | | ✓ |
| `--no-open` | ✓ | | | |
| `--no-inspector` | ✓ | | | |
| `--with-inspector` | | | | ✓ |
| `--source-maps` | | ✓ | | |
| `--inline` | | ✓ | | |
| `--` (tsc args) | | | ✓ | |
| `--help, -h` | ✓ | ✓ | ✓ | ✓ |
| `--version, -v` | ✓ | ✓ | ✓ | ✓ |

## Command × Flag Matrix — cloud and testing commands

`--version`/`-v` does not apply to these; each has its own `--help`/`-h`.

| Flag | deploy | login | logout | whoami | org | servers | deployments | client | screenshot |
|------|--------|-------|--------|--------|-----|---------|--------------|--------|------------|
| `[path]` (positional) | ✓ | | | | | | | | |
| `--org <id-or-slug>` | ✓ | ✓ | | | | ✓ | ✓ | | |
| `--name <name>` | ✓ | | | | | | | | |
| `--branch <name>` | ✓ | | | | | | ✓ (restart) | | |
| `--root-dir <path>` | ✓ | | | | | | | | |
| `--region <region>` | ✓ | | | | | | | | |
| `--env <KEY=VALUE>` | ✓ | | | | | | | | |
| `--env-file <path>` | ✓ | | | | | | | | |
| `--build-command <cmd>` | ✓ | | | | | | | | |
| `--start-command <cmd>` | ✓ | | | | | | | | |
| `--dockerfile <path>` | ✓ | | | | | | | | |
| `--watch-paths <glob>` | ✓ | | | | | | | | |
| `--wait-for-ci` | ✓ | | | | | | | | |
| `--no-github` | ✓ | | | | | | | | |
| `--new` | ✓ | | | | | | | | |
| `--open` | ✓ | | | | | | | | |
| `-y, --yes` | ✓ | | ✓ | | | ✓ (delete/unset) | ✓ (stop/delete) | | |
| `--api-key <key>` | | ✓ | | | | | | | |
| `--device-code <code>` | | ✓ | | | | | | | |
| `--no-open` | | ✓ | | | | | | ✓ (connect) | |
| `--server <name>` | | | | | | | | | ✓ |
| `--mcp <url>` | | | | | | | | | ✓ |
| `-H, --header <"K: V">` | | | | | | | | ✓ (connect) | ✓ (with `--mcp` only) |
| `--tool <name>` | | | | | | | | | ✓ |
| `--output <path>` | | | | | | | | | ✓ |
| `--width <px>` | | | | | | | | | ✓ |
| `--height <px>` | | | | | | | | | ✓ |
| `--json` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `--help, -h` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

`client` and `screenshot` also have their own flags not shown here in full — see `08-client-and-screenshot.md`.

## Global Defaults

| Variable | Default | Precedence |
|----------|---------|-----------|
| **Port** | `3000` | flag `--port` > env `$PORT` > configured value (`start` only) > `3000` |
| **Host** | `127.0.0.1` | flag `--host` > env `$HOST` > configured value (`start` only) > `127.0.0.1` |
| **Entry** | `package.json#main` | flag `--entry` > auto-detect |
| **Views dir** | `views/` or `<mcp-dir>/views/` | flag `--views-dir` > auto-detect |
| **MCP dir** | project root | flag `--mcp-dir` > auto-detect |
| **Project path** | current dir | flag `--path` (dev/build/typecheck/start) or positional `[path]` (deploy) > current dir |

## Notable flag behaviors

### dev / start

- `--port` and `--host` respect env vars (`$PORT`, `$HOST`) for containerized deployments
- `--tunnel` exposes a public HTTPS URL (see `03-mcp-use-dev.md` for the exact console output)
- `--no-open` (dev only) useful for headless/CI environments; auto-open already skips outside a TTY
- `--no-inspector` (dev) / `--with-inspector` (start) toggle Inspector mounting; default is on for dev, off for start

### build

- `--source-maps` emits `.js.map` files for debugging minified code
- `--inline` embeds view JS/CSS in MCP resources (larger payload, no asset downloads)
- **Build is transpile-only — it never typechecks.** There is no `--no-typecheck` flag because there is nothing to disable; run `mcp-use typecheck` as a separate step

### deploy

- `--env` repeatable; `--env A=1 --env B=2` sets multiple vars
- `--env-file` reads `.env` format
- `--no-github` uploads local source to a managed private repository instead of using/creating a GitHub-linked one
- `--json` alone does not authorize mutations — pair with `--yes` for headless GitHub repo creation, or with `--no-github` for a managed upload
- `--open` cannot combine with `--json` (JSON mode never opens a browser)
- `--watch-paths`/`--wait-for-ci` are GitHub-only
- Archive size limit: 80 MB; the managed-upload archive excludes `.git`, `node_modules`, build output, `.mcp-use`, `.env*`, caches, coverage, OS metadata, and symlinks

### login / logout / whoami

- `--json` outputs machine-readable format (useful in scripts); `logout --json` never prompts, `login`'s device flow still authenticates but skips organization-selection prompts (failing instead if ambiguous)
- `--api-key` skips device flow (for CI/CD); also read from `$MCP_USE_API_KEY` if neither `--api-key` nor `--device-code` is passed
- `--device-code` redeems pre-approved codes (CI-friendly)
- `--org` required for headless `login` when the account has no default organization
- `logout --yes` skips confirmation (required in non-interactive runs); `whoami` has no `--yes` (nothing to confirm)

## Environment variable overrides

These take effect when the corresponding flag is not passed:

- `$PORT` — used by dev/start if `--port` not specified
- `$HOST` — used by dev/start if `--host` not specified
- `$NODE_ENV` — set to `production` by `start` only if not already set (`process.env.NODE_ENV ??= "production"`); never overrides an explicit value
- `$MCP_URL` — **not** the tunnel URL mechanism. `dev` sets a temporary `http://localhost:${port}` fallback into `process.env.MCP_URL` only when unset and the bind host is localhost-class, restored after the server entry module loads. The public tunnel URL (from `--tunnel`) is reported separately via the console `➜ Tunnel:` line and the Inspector's dev-info API — never through `$MCP_URL`. See `10-environment-variables.md` for the full picture.
- `$MCP_USE_API_KEY` — read by `login` as a fallback API key when `--api-key`/`--device-code` are both omitted

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success (or help/version shown) |
| `1` | Runtime error (build failure, server startup error, auth/API failure) |
| `2` | Invalid arguments, missing required flag, or (deploy) an explicit headless choice is required |

## Repeatable flags

- `--env <KEY=VALUE>` (deploy) — can repeat for multiple env vars
- `--watch-paths <glob>` (deploy) — can repeat for multiple path filters (max 32)
- `-H, --header <"Key: Value">` (client `connect`, screenshot with `--mcp`) — can repeat for multiple custom headers
