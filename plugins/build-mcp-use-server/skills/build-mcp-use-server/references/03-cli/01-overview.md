# CLI Overview

*Read this to understand the command inventory and which command to use for each task.*

The `mcp-use` CLI (v4.x, currently `4.3.1` on npm `latest`) provides commands for local development, cloud authentication, deployment, and client testing.

**Which binary ships the CLI — the classic confusion point:** three separate npm packages are involved. `mcp-use` (the framework, currently `2.8.1`) declares `@mcp-use/cli` as a dependency and ships a `bin/mcp-use` entry point. `@mcp-use/cli` (`4.3.1`) is the actual CLI implementation and ships its own `bin/mcp-use` entry point too — either package alone provides a working `mcp-use` command. `create-mcp-use-app` is a *third*, unrelated package: a one-shot scaffolder invoked via `npx create-mcp-use-app@latest`, not a `mcp-use` subcommand.

In a normal project (scaffolded via `create-mcp-use-app`), `mcp-use` is already a `package.json` dependency, so `npx mcp-use dev` / `npm run dev` works with no separate install. To install the CLI standalone:

```bash
npm install -g @mcp-use/cli@latest
# or invoked directly:
npx @mcp-use/cli@latest dev
```

## Command Inventory

| Command | Purpose | When to use |
|---------|---------|------------|
| **`dev`** | Start dev server with HMR, Inspector, tunnel | Active development; testing tools/views locally |
| **`build`** | Build server + views into `.mcp-use/build/` | Before production deployment or local testing of prod build |
| **`typecheck`** | Refresh project-root `mcp-env.d.ts`, run TypeScript | CI/CD or local type safety check |
| **`start`** | Serve production build from `.mcp-use/build/` | Production testing or local start after build |
| **`login`** | Authenticate with Manufact Cloud | Enable cloud deploy/org/servers commands |
| **`logout`** | Clear local cloud credentials | Sign out of cloud CLI |
| **`whoami`** | Show authenticated user and active org | Verify login status |
| **`org`** | Manage active organization | Subcommands: `list`, `current`, `use <id-or-slug>` (no `switch`) |
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

- **Port:** explicit `--port`/`-p` flag, then `$PORT` env var, then the built server's own configured port (`start` only), then fallback `3000`
- **Host:** explicit `--host` flag, then `$HOST` env var, then the built server's own configured host (`start` only), then fallback `127.0.0.1` (localhost-only by default for security)
- **Views directory:** `views/` or `<mcp-dir>/views/`
- **Build output:** `.mcp-use/build/`
- **Inspector mount (dev):** Automatically at `/mcp/inspector`; disable with `--no-inspector`

## Removed in v4.x (v2 CLI)

These commands do **not** exist in `@mcp-use/cli` v4:

- `mcp-use skills` — removed in v2.0.0; skills are managed via conventional `skills/` directory discovery and served automatically
- `mcp-use generate-types` — merged into `typecheck` (regenerates `mcp-env.d.ts` at the project root)
- `mcp-use introspect` — use the Inspector (`mcp-use dev`, mounted at `/mcp/inspector`) instead
- `mcp-use serve` — use `start` instead (serves the `.mcp-use/build/` production build)
- `mcp-use generate-docs` — not shipped

## Next Steps

- **Local development:** read `03-mcp-use-dev.md`
- **Production build:** read `04-mcp-use-build-and-typecheck.md`
- **Cloud deployment:** read `06-mcp-use-deploy-and-cloud.md`
- **All flags reference:** read `09-flag-reference.md`
