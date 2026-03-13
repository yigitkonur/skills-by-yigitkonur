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

Start a development server with hot reload, automatic TypeScript compilation, and auto-opening inspector.

```bash
mcp-use dev [options]
```

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
mcp-use dev                    # Start with defaults
mcp-use dev --port 8080        # Custom port
mcp-use dev --no-open          # Disable inspector auto-open
mcp-use dev --no-hmr           # Disable HMR (uses tsx watch instead)
mcp-use dev -p ./my-server     # Custom project path
```

### Hot Module Reloading (HMR)

HMR is enabled by default. It applies changes without restarting the server or dropping client connections.

**Can be hot-reloaded:** Adding, updating, or removing tools, prompts, resources, resource templates, and their descriptions/schemas/handlers.

**Requires a full restart:** Server config changes (name, version, port), new middleware, OAuth configuration changes.

Connected clients automatically receive `list_changed` notifications and refresh their cached lists.

---

## `mcp-use build` — Production Build

```bash
mcp-use build [options]
```

| Flag                  | Description                      | Default           |
|-----------------------|----------------------------------|--------------------|
| `-p, --path <path>`   | Project directory                | Current directory  |
| `--with-inspector`    | Include inspector in build       | `false`            |

**Build steps:** TypeScript compilation → `.tsx` widget bundling as standalone HTML → asset hashing → minification → manifest generation (`dist/mcp-use.json`).

```bash
mcp-use build                              # Standard build
mcp-use build --with-inspector             # Build with inspector included
MCP_SERVER_URL=https://cdn.example.com mcp-use build  # Custom widget asset paths
```

> Use `MCP_SERVER_URL` during build to configure widget asset paths for static deployments (e.g., Supabase Storage).

---

## `mcp-use start` — Production Server

```bash
mcp-use start [options]
```

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
```

---

## `mcp-use deploy` — Cloud Deployment

Deploy to Manufact Cloud.

```bash
mcp-use deploy [options]
```

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

---

## `mcp-use generate-types` — Type Generation

Generate TypeScript types for MCP tools from Zod schemas.

```bash
mcp-use generate-types [options]
```

| Flag                  | Description                      | Default           |
|-----------------------|----------------------------------|--------------------|
| `-p, --path <path>`   | Project directory                | Current directory  |
| `--server <file>`     | Server entry file                | `index.ts`         |

**What it does:** Scans tool registrations → converts Zod schemas to TypeScript types → generates `.mcp-use/tool-registry.d.ts` → enables full IntelliSense in widget code.

> Type generation runs **automatically** during `mcp-use dev`. Run manually for CI/CD, after pulling schema changes, or when building without the dev server.

```bash
mcp-use generate-types                          # Current project
mcp-use generate-types --server src/server.ts   # Custom entry file
```

Ensure your `tsconfig.json` includes the generated types:

```json
{
  "include": ["index.ts", "src/**/*", "resources/**/*", ".mcp-use/**/*"]
}
```

---

## Authentication Commands

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

---

## Skills Commands

### `mcp-use skills add`

Download and install the latest mcp-use AI agent skills into all agent preset directories:
- `.cursor/skills/` (Cursor), `.claude/skills/` (Claude Code), `.agent/skills/` (Codex)

```bash
mcp-use skills add              # Current project
mcp-use skills add -p ./my-server
```

### `mcp-use skills install`

Alias for `skills add`. Identical behavior.

> Skills are also installed automatically by `create-mcp-use-app` unless `--no-skills` is passed.

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
| `mcp-use build`            | Production build                               | `--with-inspector`, `-p`                       |
| `mcp-use start`            | Run production build                           | `--port`, `--tunnel`, `-p`                     |
| `mcp-use deploy`           | Deploy to Manufact Cloud                       | `--name`, `--runtime`, `--env`, `--env-file`   |
| `mcp-use generate-types`   | Generate TS types from Zod schemas             | `--server`, `-p`                               |
| `mcp-use login`            | Authenticate with Manufact Cloud               | —                                              |
| `mcp-use whoami`           | Check auth status                              | —                                              |
| `mcp-use logout`           | Remove auth credentials                        | —                                              |
| `mcp-use skills add`       | Install AI agent skills                        | `-p`                                           |
| `mcp-use skills install`   | Alias for `skills add`                         | `-p`                                           |
