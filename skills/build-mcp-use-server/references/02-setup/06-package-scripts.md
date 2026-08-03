# Package scripts

*Read this to understand the standard npm scripts scaffolded by create-mcp-use-app.*

All templates include the same five scripts in `package.json`. Each invokes the `mcp-use` binary directly (the canonical CLI implementation, shipped with the `mcp-use` package itself) — not `@mcp-use/cli`, which is a separate compatibility-only bin shim for the historical install command.

## Scripts

```json
{
  "scripts": {
    "dev": "mcp-use dev",
    "build": "mcp-use build",
    "typecheck": "mcp-use typecheck",
    "start": "mcp-use start",
    "deploy": "mcp-use deploy"
  }
}
```

### `npm run dev`

Starts the development server with hot module reload (HMR). Inspector automounts at `http://localhost:3000/mcp/inspector` and opens in your browser (unless `--no-open`).

```bash
npm run dev
npm run dev -- --port 4000          # Override port
npm run dev -- --host 0.0.0.0       # Listen on all interfaces
npm run dev -- --no-inspector       # Disable Inspector
npm run dev -- --tunnel             # Public tunnel (24h expiry, 5 per IP)
```

Restarts on changes to `index.ts`, tools, resources, prompts, or views.

### `npm run build`

Builds the server and views into `.mcp-use/build/`. Output is optimized for production.

```bash
npm run build
npm run build -- --source-maps      # Include source maps
npm run build -- --inline           # Embed CSS/JS in resources
```

Required before `npm run start` or `npm run deploy`.

### `npm run typecheck`

Regenerates `mcp-env.d.ts` (the bridge between server tools and view typing) and runs TypeScript strict-mode check.

```bash
npm run typecheck
npm run typecheck -- -- --noUnusedLocals  # Forward an extra flag to tsc
```

The CLI always appends `--noEmit`. With npm scripts, forwarding an additional TypeScript flag needs two separators: npm consumes the first `--`, and `mcp-use typecheck` consumes the second before passing the remaining arguments to `tsc`.

Run this after adding/removing tools or modifying schemas. CI should fail if types are stale.

### `npm run start`

Serves the production build from `.mcp-use/build/`. Does not rebuild; use after `npm run build`.

```bash
npm run start
npm run start -- --port 8080        # Override port
npm run start -- --with-inspector   # Mount Inspector on production
```

Useful for testing production build locally.

### `npm run deploy`

Deploys to Manufact Cloud. The CLI does **not** initialize Git, create a repository, commit, push, install the GitHub App, or upload local source — configure those prerequisites yourself first:
1. Commit the server to an existing Git repository.
2. Configure `origin` as a supported GitHub repository and push the branch to deploy.
3. Install the Manufact GitHub App with access to that repository.
4. `mcp-use login` (one-time; supports `--api-key`/`--org` or `--device-code`/`--org` for non-interactive sign-in).

```bash
npm run deploy -- --name my-server-name
npm run deploy -- --env API_KEY=sk-xxx
npm run deploy -- --env-file .env.production
npm run deploy -- --region us-west-2
```

The first deploy resolves the repo from `origin`, confirms GitHub App access, creates a Git-backed cloud server, starts the deployment, and writes non-secret linkage to `.mcp-use/cloud/link.json`. It starts the deployment; it does not wait for the build to finish — follow it with `mcp-use deployments logs DEPLOYMENT_ID --build --follow`. A later `npm run deploy` with a link file present redeploys the same linked server; pass `--new` to create a separate server instead.

**Result URL:** after the deployment is running, copy the exact generated MCP URL from the Manufact dashboard. Do not infer a hostname from the server slug — the dashboard is authoritative for generated and custom domains; no fixed URL pattern is guaranteed.

## Flags per script

| Flag | Commands | Example |
|------|----------|---------|
| `--port <n>` | dev, start | `npm run dev -- --port 4000` |
| `--host <host>` | dev, start | `npm run dev -- --host 0.0.0.0` |
| `--tunnel` | dev, start | `npm run dev -- --tunnel` |
| `--no-open` | dev | `npm run dev -- --no-open` |
| `--no-inspector` | dev | `npm run dev -- --no-inspector` |
| `--source-maps` | build | `npm run build -- --source-maps` |
| `--inline` | build | `npm run build -- --inline` |
| `--with-inspector` | start | `npm run start -- --with-inspector` |

### Deploy flags

| Flag | Purpose |
|------|---------|
| `[path]` | Project directory; defaults to the current directory |
| `--org <id-or-slug>` | Select the Manufact organization |
| `--name <name>` | Set the server name on creation |
| `--branch <name>` | Deploy a branch instead of the current branch |
| `--root-dir <path>` | Repository-relative app root (must stay inside the repo) |
| `--region <region>` | Select an API-supported region |
| `--env <KEY=VALUE>` | Add an environment value; repeatable, overrides duplicates loaded from `--env-file` |
| `--env-file <path>` | Load environment values from a file |
| `--build-command <command>` | Override the detected build command |
| `--start-command <command>` | Override the detected start command |
| `--dockerfile <path>` | Use a repository-relative Dockerfile (must stay inside the repo) |
| `--new` | Create a new server instead of reusing the `.mcp-use/cloud/link.json` link |
| `--open` | Open the dashboard after deployment starts |
| `--yes` | Accept confirmation prompts (non-interactive) |
| `--json` | Emit machine-readable output |

Full reference: `references/25-deploy/`.

## Environment variables

These override script defaults:

| Variable | Scripts | Precedence | Default |
|----------|---------|-----------|---------|
| `PORT` | dev, start | flag > env > code (`ServerConfig.port`, `start` only) > 3000 | 3000 |
| `HOST` | dev, start | flag > env > code (`ServerConfig.host`, `start` only) > 127.0.0.1 | 127.0.0.1 |
| `NODE_ENV` | start | `process.env.NODE_ENV ??= "production"` — set only if unset, never clobbers an explicit value | — |
| `MCP_URL` | (client targeting) | used by Inspector | http://127.0.0.1:PORT/mcp |

`start` resolves port/host against the built entry's exported `MCPServer` instance (`candidate.port`/`candidate.host`, i.e. whatever was passed to the `ServerConfig` at construction) as an extra fallback tier between `env` and the hardcoded default; `dev` has no such code-level tier because there is no built entry to inspect.

For secrets, use `--env-file` (not committed) or GitHub Actions secrets on deploy.

## CI/CD integration

Typical workflow:

```bash
npm run typecheck  # Fail if types stale
npm run build      # Fail if build breaks
npm run dev &      # Start server (background)
# Run integration tests against http://localhost:3000/mcp
npm run deploy     # Deploy if all pass
```
