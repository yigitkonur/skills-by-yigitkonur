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

#### Parameter Table: Dev Options

| Flag | Description | Default |
|---|---|---|
| `-p, --path <path>` | Project directory | `.` |
| `--port <port>` | Port for HTTP server | `3000` |
| `--no-open` | Disable auto-open of Inspector | `false` |
| `--no-hmr` | Disable HMR and fall back to tsx watch | `false` |
| `--tunnel` | Expose dev server via tunnel (useful for ChatGPT HMR; added v1.20.5) | `false` |

**What happens in dev mode:**

1. TypeScript files are compiled in watch mode.
2. UI widgets are built with hot reload.
3. Server runs with automatic restart on changes.
4. Inspector automatically opens at `http://localhost:3000/inspector`.
5. MCP endpoint is available at `http://localhost:3000/mcp`.

**Can be hot-reloaded:** Adding, updating, or removing tools, prompts, resources, resource templates, and their descriptions/schemas/handlers.

**Requires a full restart:** Server config changes (name, version, port), new middleware, OAuth configuration changes.

Connected clients automatically receive `list_changed` notifications and refresh their cached lists.

### Examples

```bash
mcp-use dev src/server.ts
mcp-use dev --port 8080 --no-open
npx @mcp-use/cli dev --no-hmr
```

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

| Flag | Description | Default |
|---|---|---|
| `-p, --path <path>` | Project directory | `.` |
| `--with-inspector` | Include Inspector assets in build | `false` |

### Examples

```bash
mcp-use build
mcp-use build --with-inspector
mcp-use build -p ./my-server
```

### ❌ BAD: Building Without Asset URL for Static Deployments

```bash
mcp-use build
# Missing MCP_SERVER_URL means widget assets resolve to localhost in production.
```

### ✅ GOOD: Provide Public Asset URL

```bash
MCP_SERVER_URL=https://mcp.example.com mcp-use build
```

---

## `mcp-use start` — Run Production Server

Starts the compiled server and serves `/mcp`, `/inspector`, and widget assets from `dist/`.

```bash
mcp-use start [entry] [options]
```

### Options

| Flag | Description | Default |
|---|---|---|
| `-p, --path <path>` | Project directory | `.` |
| `--port <port>` | HTTP port | `3000` |
| `--tunnel` | Expose via tunnel | `false` |

### Examples

```bash
mcp-use start
mcp-use start --port 8080
mcp-use start --tunnel
mcp-use start -p ./my-server
```

---

## `mcp-use deploy` — Deploy to Manufact Cloud

Deploys the build output and uploads environment variables. Requires `mcp-use login` first.

```bash
mcp-use deploy [options]
```

### Options

| Flag | Description | Default |
|---|---|---|
| `--name <name>` | Custom deployment name | Auto-generated |
| `--port <port>` | Server port | `3000` |
| `--runtime <runtime>` | Runtime: `node` or `python` | `node` |
| `--open` | Open deployment in browser | `false` |
| `--env <key=value>` | Environment variable (repeatable) | — |
| `--env-file <path>` | Path to .env file | — |
| `--root-dir <path>` | Root directory for monorepo deployments (v1.21.1+) | — |

**Deployment flow:**

1. Checks if project is a GitHub repository.
2. Prompts to install the GitHub App if needed.
3. Creates or links the deployment project.
4. Builds and deploys from GitHub.
5. Returns deployment URLs (MCP endpoint + Inspector).

> Deploy automatically creates `.mcp-use/project.json` to link your local project to the cloud for stable URLs across redeployments.

### Examples

```bash
mcp-use deploy
mcp-use deploy --name my-server --open
mcp-use deploy --env DATABASE_URL=postgres://... --env API_KEY=secret
mcp-use deploy --env-file .env.production
mcp-use deploy --runtime python
mcp-use deploy --root-dir packages/my-server  # monorepo: specify server root
```

### ❌ BAD: Committing Secrets

```bash
mcp-use deploy --env API_KEY=sk-123  # Then commit this to shell history
```

### ✅ GOOD: Use an Env File

```bash
mcp-use deploy --env-file .env.prod
```

---

## `mcp-use generate-types` — Tool Type Generation

Generates TypeScript types from tool Zod schemas. Output goes to `.mcp-use/tool-registry.d.ts`. Type generation is **automatic** during `mcp-use dev` — run this command manually for CI/CD, after pulling schema changes, or when troubleshooting type inference.

```bash
mcp-use generate-types [options]
```

### Options

| Flag | Description | Default |
|---|---|---|
| `-p, --path <path>` | Project directory | `.` |
| `--server <file>` | Server entry file | `index.ts` |

### Examples

```bash
# Generate types for current project
mcp-use generate-types

# Custom project path
mcp-use generate-types -p ./my-server

# Custom server entry file
mcp-use generate-types --server src/server.ts
```

### ❌ BAD: Forgetting to Include `.mcp-use` in `tsconfig.json`

```json
{
  "include": ["src/**/*"]
}
```

### ✅ GOOD: Include Generated Types

```json
{
  "include": ["src/**/*", "resources/**/*", ".mcp-use/**/*"]
}
```

---

## `create-mcp-use-app` — Project Scaffolding

`create-mcp-use-app` scaffolds a ready-to-run MCP server with widgets, resources, and tooling. Use `npx create-mcp-use-app` or your package manager’s `create` command.

```bash
npx create-mcp-use-app my-server --template starter
```

### Options

| Flag | Description | Default |
|---|---|---|
| `--template <name>` | `starter`, `mcp-apps`, `mcp-ui` | `starter` |
| `--no-skills` | Skip skill installation | `false` |

### Generated Project Structure

```text
my-server/
├─ src/
│  ├─ server.ts
│  ├─ tools/
│  ├─ resources/
│  └─ prompts/
├─ resources/
│  ├─ apps/
│  ├─ panels/
│  └─ cards/
├─ public/
├─ package.json
├─ tsconfig.json
└─ .mcp-use/
```

### ❌ BAD: Editing `dist/` Instead of Source

```text
dist/server.js
```

### ✅ GOOD: Edit `src/server.ts`

```text
src/server.ts
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

## Environment Variables (Core)

### Development & Build

| Variable         | Description                            | Default         |
|-----------------|----------------------------------------|-----------------|
| `PORT`           | Server port                            | `3000`          |
| `NODE_ENV`       | Environment mode                       | `development`   |
| `MCP_SERVER_URL` | Server URL for widget asset paths      | —               |

```bash
# Custom port
PORT=8080 mcp-use dev

# Production build with custom MCP URL
MCP_SERVER_URL=https://myserver.com mcp-use build
```

### Deployment & Cloud

| Variable      | Description               | Default                             |
|--------------|---------------------------|-------------------------------------|
| `MCP_WEB_URL` | Frontend URL (auth pages) | `https://manufact.com`              |
| `MCP_API_URL` | Backend API URL           | `https://cloud.manufact.com/api/v1` |

```bash
# Local development environment
export MCP_WEB_URL=http://localhost:3000
export MCP_API_URL=http://localhost:8000
mcp-use login
mcp-use deploy
```

---

## Command Reference Table (Condensed)

| Command                    | Description                                    | Key Flags                                      |
|---------------------------|------------------------------------------------|------------------------------------------------|
| `mcp-use dev`              | Start dev server with HMR + Inspector          | `--port`, `--no-open`, `--no-hmr`, `--tunnel`, `-p` |
| `mcp-use build`            | Production build                               | `--with-inspector`, `-p`                       |
| `mcp-use start`            | Run production build                           | `--port`, `--tunnel`, `-p`                     |
| `mcp-use deploy`           | Deploy to Manufact Cloud                       | `--name`, `--runtime`, `--env`, `--env-file`, `--open`, `--root-dir` |
| `mcp-use generate-types`   | Generate TS types from Zod schemas             | `--server`, `-p`                               |
| `mcp-use login`            | Authenticate with Manufact Cloud               | —                                              |
| `mcp-use whoami`           | Check auth status                              | —                                              |
| `mcp-use logout`           | Remove auth credentials                        | —                                              |
| `mcp-use skills add`       | Install AI agent skills                        | `-p`                                           |
| `mcp-use skills install`   | Alias for `skills add`                         | `-p`                                           |

---

## `mcp-use login`, `whoami`, `logout`

Authentication commands manage access to Manufact Cloud deployments.

```bash
mcp-use login
mcp-use whoami
mcp-use logout
```

`mcp-use login` starts an OAuth device code flow; opens browser and stores the session token in `~/.mcp-use/config.json`. `mcp-use logout` removes credentials from the same file.

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

Skills provide AI helper prompts and workflows. Install them per project to avoid global drift. Downloads and installs into all agent preset directories:
- `.cursor/skills/` (Cursor), `.claude/skills/` (Claude Code), `.agent/skills/` (Codex)

```bash
mcp-use skills add build-mcp-use-server
mcp-use skills install build-mcp-use-server
```

### Options

| Flag | Description | Default |
|---|---|---|
| `-p, --path <path>` | Project directory | `.` |

### ❌ BAD: Installing Skills in the Wrong Repo

```bash
mcp-use skills add build-mcp-use-server -p ~/Downloads
```

### ✅ GOOD: Target the Active Project

```bash
mcp-use skills add build-mcp-use-server -p ./
```

---

## CI-Friendly Workflows

Use `@mcp-use/cli` in CI to keep output predictable and ensure builds match local dev.

### Recommended Script Matrix

| Script | Command | Notes |
|---|---|---|
| `dev` | `mcp-use dev src/server.ts` | Local only |
| `build` | `mcp-use build` | Production assets |
| `start` | `mcp-use start` | Runs compiled output |
| `typecheck` | `tsc --noEmit` | Optional for CI |
| `generate-types` | `mcp-use generate-types` | Ensure hooks are up to date |

### Example CI Step

```bash
npm ci
mcp-use build
mcp-use generate-types --server src/server.ts
```

---

## CLI Output Artifacts

| File | Created By | Purpose |
|---|---|---|
| `dist/mcp-use.json` | `mcp-use build` | Build manifest — entry point, widget schemas, build ID, tunnel config |
| `dist/` | `mcp-use build` | Compiled server + widget bundles |
| `.mcp-use/project.json` | `mcp-use deploy` | Links local project to cloud deployment for stable URLs |
| `.mcp-use/sessions.json` | `mcp-use dev` | Persists dev sessions to survive hot reloads (dev only) |
| `~/.mcp-use/config.json` | `mcp-use login` | User-level auth credentials (apiKey, apiUrl) |
| `.mcp-use/tool-registry.d.ts` | `mcp-use generate-types` | TypeScript type augmentations for tool schemas |
| `public/` | scaffold | Static assets served via MCP server |
| `resources/` | scaffold | UI widgets and MCP apps |

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

## Common CLI Workflows

### Local Dev → Build → Start

```bash
mcp-use dev src/server.ts
mcp-use build
mcp-use start --port 4000
```

### Deploy with Environment Vars

```bash
mcp-use login
mcp-use deploy --env-file .env.prod
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

## CLI Flags and Environment Interactions

| Scenario | Prefer Flag | Prefer Env Var |
|---|---|---|
| Quick port change | `--port 4000` | `PORT=4000` |
| Persistent public URL | — | `MCP_SERVER_URL` |
| Local debugging | `--with-inspector` | — |

---

## Dev Mode Diagnostics and HMR Signals

`mcp-use dev` emits console logs when it reloads tools, resources, prompts, or widgets. Use these logs to verify HMR is functioning.

### HMR Log Signals

| Log Message | Meaning | Action |
|---|---|---|
| `HMR: tools reloaded` | Tool registry updated | Clients receive `tools/list_changed` |
| `HMR: resources reloaded` | Resource list updated | Clients receive `resources/list_changed` |
| `HMR: prompts reloaded` | Prompt list updated | Clients receive `prompts/list_changed` |
| `HMR: widgets rebuilt` | UI bundle updated | Refresh widget UI |

### Debug Flags

| Flag | Description |
|---|---|
| `--no-open` | Prevents browser auto-open (useful in CI) |
| `--no-hmr` | Use tsx watch if bundler fails |

### ❌ BAD: Ignoring HMR Errors

```bash
mcp-use dev
# HMR error in console, but no action taken.
```

### ✅ GOOD: Restart After HMR Failure

```bash
mcp-use dev --no-hmr
# Or restart after fixing the bundler issue.
```

---

## Build Profiles

Different build options are ideal for different stages of delivery.

| Profile | Recommended Flags | When to Use |
|---|---|---|
| Debug | `--with-inspector` | Internal QA, staging |
| Production | default | Public deployments |

### Example: Debug Build

```bash
mcp-use build --with-inspector
```

---

## Deploy Environments and Secrets

`mcp-use deploy` supports inline and file-based environment variables. Prefer `.env` files for repeatable deployments.

### Env File Format

```text
MCP_SERVER_URL=https://mcp.example.com
API_KEY=sk-live-123
```

### ❌ BAD: Storing Secrets in Git

```text
.env.prod  # Committed with secrets
```

### ✅ GOOD: Keep Env Files Local

```bash
echo '.env.prod' >> .gitignore
```

---

## `generate-types` + React Hooks Workflow

The generated `tool-registry.d.ts` powers typed hooks like `useCallTool` when used with `generateHelpers`.

```tsx
import { generateHelpers } from 'mcp-use/react';
import type { ToolRegistry } from '../.mcp-use/tool-registry';

const { useCallTool } = generateHelpers<ToolRegistry>();
```

### Type Sync Checklist

1. Update Zod schemas.
2. Run `mcp-use generate-types`.
3. Restart widget dev server if necessary.

---

## Templates Deep Dive

| Template | Ideal For | Includes |
|---|---|---|
| `starter` | General-purpose servers | Tools, resources, prompts, widgets |
| `mcp-apps` | Apps SDK adoption | App UI examples + adapters |
| `mcp-ui` | MCP UI resources | UIResource examples + assets |

### Choosing a Template

```bash
npx create-mcp-use-app analytics --template mcp-ui
```

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

## Custom Entry Files

You can pass a server entry file to most commands. This is useful for monorepos or multi-server setups.

```bash
mcp-use dev packages/api/src/server.ts
mcp-use build packages/api/src/server.ts
mcp-use generate-types --server packages/api/src/server.ts
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

## Getting Help

```bash
mcp-use --help
mcp-use dev --help
npx @mcp-use/cli deploy --help
```

