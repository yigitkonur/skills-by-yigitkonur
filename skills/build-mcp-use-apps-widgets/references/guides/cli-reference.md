# CLI Reference

Complete reference for the `@mcp-use/cli` — the build, development, and deployment tool for mcp-use MCP servers.

---

## Installation

```bash
npm install -g @mcp-use/cli       # Install globally
npx @mcp-use/cli dev              # Or use via npx (no install needed)
npm install --save-dev @mcp-use/cli  # Project dependency
```

> When using `npx create-mcp-use-app`, the CLI is automatically installed as a project dependency.

---

## Project Scaffolding

```bash
npx create-mcp-use-app my-server
cd my-server && npm run dev
```

Alternative package managers: `pnpm create mcp-use-app@latest my-server` / `yarn create mcp-use-app@latest my-server`.

### Templates

| Template     | Flag                       | Description                                      |
|-------------|----------------------------|--------------------------------------------------|
| **starter** | `--template starter`       | Default. Tools, resources, prompts, UI widgets.   |
| **mcp-apps**| `--template mcp-apps`      | OpenAI Apps SDK widgets for ChatGPT.              |
| **mcp-ui**  | `--template mcp-ui`        | All three MCP-UI UIResource types demonstrated.   |

```bash
npx create-mcp-use-app my-server --template starter   # Default
npx create-mcp-use-app my-server --template mcp-apps   # Apps SDK
npx create-mcp-use-app my-server --template mcp-ui     # MCP-UI
```

> Run `npx create-mcp-use-app --help` for all options. Pass `--no-skills` to skip AI agent skill installation.

---

## `mcp-use dev` — Development Server

Runs the dev server with HMR, type generation, and the Inspector. Always prefer `@mcp-use/cli` or `npx @mcp-use/cli` when documenting usage.

```bash
mcp-use dev [entry] [options]
# or
npx @mcp-use/cli dev [entry] [options]
```

### Options

| Flag                  | Description                      | Default           |
|-----------------------|----------------------------------|--------------------|
| `-p, --path <path>`   | Project directory                | Current directory  |
| `--port <port>`       | Server port                      | `3000`             |
| `--no-open`           | Don't auto-open inspector        | `false`            |
| `--no-hmr`            | Disable Hot Module Reloading     | `false`            |

**What happens in dev mode:**

1. TypeScript files are compiled in watch mode.
2. UI widgets are built with hot reload.
3. Server runs with automatic restart on changes.
4. Inspector automatically opens at `http://localhost:3000/inspector`.
5. MCP endpoint is available at `http://localhost:3000/mcp`.

```bash
mcp-use dev                    # Start with defaults (uses index.ts)
mcp-use dev index.ts           # Explicit entry file
mcp-use dev --port 8080        # Custom port
mcp-use dev --no-open          # Disable inspector auto-open
mcp-use dev --no-hmr           # Disable HMR (uses tsx watch instead)
mcp-use dev -p ./my-server     # Custom project path
npx @mcp-use/cli dev --no-hmr
```

### Hot Module Reloading (HMR)

HMR is enabled by default. It applies changes without restarting the server or dropping client connections.

**Can be hot-reloaded:** Adding, updating, or removing tools, prompts, resources, resource templates, and their descriptions/schemas/handlers.

**Requires a full restart:** Server config changes (name, version, port), new middleware, OAuth configuration changes.

Connected clients automatically receive `list_changed` notifications and refresh their cached lists.

### HMR Log Signals

| Log Message | Meaning | Action |
|---|---|---|
| `HMR: tools reloaded` | Tool registry updated | Clients receive `tools/list_changed` |
| `HMR: resources reloaded` | Resource list updated | Clients receive `resources/list_changed` |
| `HMR: prompts reloaded` | Prompt list updated | Clients receive `prompts/list_changed` |
| `HMR: widgets rebuilt` | UI bundle updated | Refresh widget UI |

### ❌ BAD: Disabling HMR Without Reason

```bash
mcp-use dev --no-hmr
```

### ✅ GOOD: Keep HMR On During UI Work

```bash
mcp-use dev --port 3000
```

---

## `mcp-use build` — Production Build

Compiles TypeScript, bundles widgets, and outputs `dist/`. Use `--with-inspector` if you want the Inspector shipped in production.

```bash
mcp-use build [entry] [options]
```

### Options

| Flag                  | Description                      | Default           |
|-----------------------|----------------------------------|--------------------|
| `-p, --path <path>`   | Project directory                | Current directory  |
| `--with-inspector`    | Include inspector in build       | `false`            |
| `--no-typecheck`      | Skip TypeScript type-checking (build only, faster) | `false` |

**Build steps:** TypeScript compilation → `.tsx` widget bundling as standalone HTML → asset hashing → minification → manifest generation (`dist/mcp-use.json`).

> As of v1.21.5, `--no-typecheck` separates type-checking from transpilation. Use it in CI when you run `tsc --noEmit` as a separate step.

```bash
mcp-use build                              # Standard build
mcp-use build --with-inspector             # Build with inspector included
mcp-use build --no-typecheck               # Skip type-checking (faster CI)
mcp-use build -p ./my-server
MCP_SERVER_URL=https://cdn.example.com mcp-use build  # Custom widget asset paths
```

> Use `MCP_SERVER_URL` during build to configure widget asset paths for static deployments (e.g., Supabase Storage).

### ❌ BAD: Building Without Asset URL for Static Deployments

```bash
mcp-use build
# Missing MCP_SERVER_URL means widget assets resolve to localhost in production.
```

### ✅ GOOD: Provide Public Asset URL

```bash
MCP_SERVER_URL=https://mcp.example.com mcp-use build
```

### Build Profiles

| Profile | Recommended Flags | When to Use |
|---|---|---|
| Debug | `--with-inspector` | Internal QA, staging |
| Production | default | Public deployments |

---

## `mcp-use start` — Run Production Server

Starts the compiled server and serves `/mcp`, `/inspector`, and widget assets from `dist/`.

```bash
mcp-use start [entry] [options]
```

### Options

| Flag                  | Description                      | Default           |
|-----------------------|----------------------------------|--------------------|
| `-p, --path <path>`   | Project directory                | Current directory  |
| `--port <port>`       | Server port                      | `3000`             |
| `--tunnel`            | Expose via tunnel                | `false`            |

Reads `dist/mcp-use.json` for the entry point. Falls back to checking `dist/index.js`, `dist/server.js`, etc. if the manifest is missing.

```bash
mcp-use start                    # Start production server
mcp-use start --port 8080        # Custom port
mcp-use start --tunnel           # Start with tunnel (exposes server publicly)
mcp-use start -p ./my-server
```

### ❌ BAD: Running `start` Without Building

```bash
mcp-use start
```

### ✅ GOOD: Build Then Start

```bash
mcp-use build && mcp-use start
```

---

## `mcp-use deploy` — Deploy to Manufact Cloud

Deploys the build output and uploads environment variables. Requires `mcp-use login` first.

```bash
mcp-use deploy [options]
```

### Options

| Flag                    | Description                           | Default        |
|-------------------------|---------------------------------------|----------------|
| `--name <name>`         | Custom deployment name                | Auto-generated |
| `--port <port>`         | Server port                           | `3000`         |
| `--runtime <runtime>`   | Runtime: `"node"` or `"python"`       | `"node"`       |
| `--open`                | Open deployment in browser            | `false`        |
| `--env <key=value>`     | Environment variable (repeatable)     | —              |
| `--env-file <path>`     | Path to `.env` file                   | —              |

**Deployment flow:**

1. Checks if project is a GitHub repository.
2. Prompts to install the GitHub App if needed.
3. Creates or links the deployment project.
4. Builds and deploys from GitHub.
5. Returns deployment URLs (MCP endpoint + Inspector).

```bash
mcp-use deploy                                               # Basic deploy
mcp-use deploy --name my-server --open                       # Named + open browser
mcp-use deploy --env DATABASE_URL=postgres://... --env API_KEY=secret
mcp-use deploy --env-file .env.production
mcp-use deploy --runtime python                              # Python runtime
```

> Deploy automatically creates `.mcp-use/project.json` to link your local project to the cloud for stable URLs across redeployments.

### ❌ BAD: Committing Secrets

```bash
mcp-use deploy --env API_KEY=sk-123  # Then commit this to shell history
```

### ✅ GOOD: Use an Env File

```bash
mcp-use deploy --env-file .env.prod
```

### Deploy Environments and Secrets

`mcp-use deploy` supports inline and file-based environment variables. Prefer `.env` files for repeatable deployments.

**Env File Format:**

```text
MCP_SERVER_URL=https://mcp.example.com
API_KEY=sk-live-123
```

Keep env files out of version control:

```bash
echo '.env.prod' >> .gitignore
```

---

## `mcp-use generate-types` — Tool Type Generation

Generates TypeScript types from tool Zod schemas. Output goes to `.mcp-use/tool-registry.d.ts`. Type generation is **automatic** during `mcp-use dev` — run this command manually for CI/CD, after pulling schema changes, or when troubleshooting type inference.

```bash
mcp-use generate-types [options]
```

### Options

| Flag                  | Description                      | Default           |
|-----------------------|----------------------------------|--------------------|
| `-p, --path <path>`   | Project directory                | Current directory  |
| `--server <file>`     | Server entry file                | `index.ts`         |
| `--root-dir <dir>`    | TypeScript rootDir for monorepos | Auto-detected      |

**What it does:** Scans tool registrations → converts Zod schemas to TypeScript types → generates `.mcp-use/tool-registry.d.ts` → enables full IntelliSense in widget code.

```bash
mcp-use generate-types                          # Current project (uses index.ts)
mcp-use generate-types -p ./my-server           # Custom project path
mcp-use generate-types --server index.ts        # Explicit entry file
```

### ❌ BAD: Forgetting to Include `.mcp-use` in `tsconfig.json`

```json
{
  "include": ["src/**/*"]
}
```

### ✅ GOOD: Include Generated Types

Ensure your `tsconfig.json` includes the generated types:

```json
{
  "include": ["index.ts", "src/**/*", "resources/**/*", ".mcp-use/**/*"]
}
```

### `generate-types` + React Hooks Workflow

The generated `tool-registry.d.ts` powers typed hooks like `useCallTool` when used with `generateHelpers`.

```tsx
import { generateHelpers } from 'mcp-use/react';
import type { ToolRegistry } from '../.mcp-use/tool-registry';

const { useCallTool } = generateHelpers<ToolRegistry>();
```

**Type Sync Checklist:**

1. Update Zod schemas.
2. Run `mcp-use generate-types`.
3. Restart widget dev server if necessary.

---

## `mcp-use login`, `whoami`, `logout`

Authentication commands manage access to Manufact Cloud deployments.

```bash
mcp-use login
mcp-use whoami
mcp-use logout
```

### `mcp-use login`

Authenticate with Manufact Cloud via OAuth device code flow. Opens browser, stores session token in `~/.mcp-use/config.json`.

```bash
mcp-use login
```

### `mcp-use whoami`

Display current authentication status and user information.

```bash
mcp-use whoami
```

### `mcp-use logout`

Remove authentication credentials from `~/.mcp-use/config.json`.

```bash
mcp-use logout
```

### Usage Tips

| Command | When to Use | Expected Output |
|---|---|---|
| `mcp-use login` | Before first deploy | Browser-based OAuth flow |
| `mcp-use whoami` | Validate session | Logged-in account info |
| `mcp-use logout` | Revoke credentials | Local auth removed |

### ❌ BAD: Deploying Without Checking Auth

```bash
mcp-use deploy
```

### ✅ GOOD: Confirming Auth First

```bash
mcp-use whoami && mcp-use deploy
```

---

## `mcp-use skills` — Skill Installation

Skills provide AI helper prompts and workflows. Install them per project to avoid global drift. Download and install the latest mcp-use AI agent skills into all agent preset directories:
- `.cursor/skills/` (Cursor), `.claude/skills/` (Claude Code), `.agent/skills/` (Codex)

```bash
mcp-use skills add build-mcp-use-app
mcp-use skills install build-mcp-use-app
```

### `mcp-use skills add`

```bash
mcp-use skills add              # Current project
mcp-use skills add -p ./my-server
```

### Options

| Flag | Description | Default |
|---|---|---|
| `-p, --path <path>` | Project directory | `.` |

### `mcp-use skills install`

Alias for `skills add`. Identical behavior.

> Skills are also installed automatically by `create-mcp-use-app` unless `--no-skills` is passed.

### ❌ BAD: Installing Skills in the Wrong Repo

```bash
mcp-use skills add build-mcp-use-app -p ~/Downloads
```

### ✅ GOOD: Target the Active Project

```bash
mcp-use skills add build-mcp-use-app -p ./
```

---

## Troubleshooting CLI Issues

| Symptom | Likely Cause | Fix |
|---|---|---|
| Inspector does not open | `--no-open` set or browser blocked | Remove flag or open `/inspector` manually. |
| Widgets 404 in production | Missing `MCP_SERVER_URL` | Set the public URL before `mcp-use build`. |
| Types not updated | `generate-types` not run | Run `mcp-use generate-types` after schema changes. |
| Deploy fails auth | Not logged in | Run `mcp-use login` first. |

---

## CI-Friendly Workflows

Use `@mcp-use/cli` in CI to keep output predictable and ensure builds match local dev.

### Recommended Script Matrix

| Script | Command | Notes |
|---|---|---|
| `dev` | `mcp-use dev` | Local only |
| `build` | `mcp-use build` | Production assets |
| `start` | `mcp-use start` | Runs compiled output |
| `typecheck` | `tsc --noEmit` | Optional for CI |
| `generate-types` | `mcp-use generate-types` | Ensure hooks are up to date |

### Example CI Step

```bash
npm ci
mcp-use build
mcp-use generate-types --server index.ts
```

### Common CLI Workflows

#### Local Dev → Build → Start

```bash
mcp-use dev
mcp-use build
mcp-use start --port 4000
```

#### Deploy with Environment Vars

```bash
mcp-use login
mcp-use deploy --env-file .env.prod
```

---

## Custom Entry Files

You can pass a server entry file to most commands. This is useful for monorepos or multi-server setups.

```bash
mcp-use dev packages/api/index.ts
mcp-use build packages/api/index.ts
mcp-use generate-types --server packages/api/index.ts
```

### Entry Path Tips

| Tip | Rationale |
|---|---|
| Use relative paths | Keeps scripts portable across machines |
| Keep entry in `src/` | Easier TS path mapping |
| Pair with `--path` | Useful for monorepos |

---

## Command Output Examples

### `mcp-use dev`

```text
Starting MCP server...
HMR enabled (widgets + tools)
Inspector: http://localhost:3000/inspector
MCP endpoint: http://localhost:3000/mcp
```

### `mcp-use build`

```text
Building widgets...
Compiling TypeScript...
Output written to dist/
```

### `mcp-use deploy`

```text
Uploading build artifacts...
Deployment available at https://mcp.example.com
```

---

## Exit Codes

| Exit Code | Meaning | Common Cause |
|---|---|---|
| `0` | Success | Command completed |
| `1` | General failure | Build errors, missing entry |
| `2` | Invalid arguments | Unknown flag or missing path |

---

## CLI Safety Checklist

- Validate env files before deploy.
- Run `mcp-use generate-types` after schema changes.
- Confirm `/mcp` and `/inspector` are reachable after start.
- Keep `MCP_SERVER_URL` in sync with deployment URL.

---

## CLI FAQ

### Why does `mcp-use start` fail?

- Ensure `mcp-use build` ran successfully.
- Check Node version matches the runtime.
- Verify `dist/` exists.

### Where is the MCP endpoint?

- Dev: `http://localhost:3000/mcp`
- Start: `http://localhost:<port>/mcp`

### How do I expose a local server?

```bash
mcp-use start --tunnel
```

---

## Getting Help

```bash
mcp-use --help
mcp-use dev --help
npx @mcp-use/cli deploy --help
```

---

## Build Artifacts

| File                        | Created By       | Purpose                                                              |
|-----------------------------|------------------|----------------------------------------------------------------------|
| `dist/mcp-use.json`        | `mcp-use build`  | Build manifest — entry point, widget schemas, build ID, tunnel config |
| `.mcp-use/project.json`    | `mcp-use deploy` | Links local project to cloud deployment for stable URLs              |
| `.mcp-use/sessions.json`   | `mcp-use dev`    | Persists dev sessions to survive hot reloads (dev only)              |
| `~/.mcp-use/config.json`   | `mcp-use login`  | User-level auth credentials (apiKey, apiUrl)                         |
| `.mcp-use/tool-registry.d.ts` | `generate-types` | TypeScript type augmentations for tool schemas                    |

### `dist/mcp-use.json` structure

```json
{
  "includeInspector": true,
  "buildTime": "2025-02-04T10:30:00.000Z",
  "buildId": "a1b2c3d4e5f6g7h8",
  "entryPoint": "dist/index.js",
  "widgets": {
    "weather-display": {
      "title": "Weather Display",
      "description": "Shows weather information",
      "props": {
        "type": "object",
        "properties": {
          "city": { "type": "string" }
        }
      }
    }
  },
  "tunnel": {
    "subdomain": "my-server-abc123"
  }
}
```

### `~/.mcp-use/config.json` structure

```json
{
  "apiKey": "your-api-key-here",
  "apiUrl": "https://cloud.manufact.com/api/v1"
}
```

> `.mcp-use/` is auto-added to `.gitignore`. In production, sessions are stored in memory by default — use Redis for multi-instance deployments.

---

## Environment Variables

| Variable         | Description                            | Default                             |
|-----------------|----------------------------------------|-------------------------------------|
| `PORT`           | Server port                            | `3000`                              |
| `NODE_ENV`       | Environment mode                       | `development`                       |
| `MCP_SERVER_URL` | Server URL for widget asset paths      | —                                   |
| `MCP_WEB_URL`    | Frontend URL (auth pages)              | `https://manufact.com`              |
| `MCP_API_URL`    | Backend API URL                        | `https://cloud.manufact.com/api/v1` |

```bash
PORT=8080 mcp-use dev                              # Custom port in dev
MCP_SERVER_URL=https://myserver.com mcp-use build   # Custom asset URL for build

# Local cloud development
export MCP_WEB_URL=http://localhost:3000
export MCP_API_URL=http://localhost:8000
mcp-use deploy
```

---

## Command Reference Table

| Command                    | Description                                    | Key Flags                                      |
|---------------------------|------------------------------------------------|------------------------------------------------|
| `mcp-use dev`              | Start dev server with HMR + Inspector          | `--port`, `--no-open`, `--no-hmr`, `-p`        |
| `mcp-use build`            | Production build                               | `--with-inspector`, `--no-typecheck`, `-p`     |
| `mcp-use start`            | Run production build                           | `--port`, `--tunnel`, `-p`                     |
| `mcp-use deploy`           | Deploy to Manufact Cloud                       | `--name`, `--runtime`, `--env`, `--env-file`, `--open` |
| `mcp-use generate-types`   | Generate TS types from Zod schemas             | `--server`, `--root-dir`, `-p`                 |
| `mcp-use login`            | Authenticate with Manufact Cloud               | —                                              |
| `mcp-use whoami`           | Check auth status                              | —                                              |
| `mcp-use logout`           | Remove auth credentials                        | —                                              |
| `mcp-use skills add`       | Install AI agent skills                        | `-p`                                           |
| `mcp-use skills install`   | Alias for `skills add`                         | `-p`                                           |
