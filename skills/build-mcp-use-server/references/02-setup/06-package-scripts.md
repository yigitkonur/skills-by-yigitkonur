# Package scripts

*Read this to understand the standard npm scripts scaffolded by create-mcp-use-app.*

All templates include the same five scripts in `package.json`. They rely on `@mcp-use/cli@4.0.0-beta.15`.

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
npm run typecheck -- --noEmit       # Only type-check, no emit
```

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

Deploys to Manufact Cloud. Requires:
1. Git repository
2. GitHub remote and pushed commits
3. `mcp-use login` (one-time)

```bash
npm run deploy
npm run deploy -- --env API_KEY=sk-xxx
npm run deploy -- --env-file .env.production
npm run deploy -- --name my-server-name
npm run deploy -- --region us-west-2
```

First deployment prompts for GitHub App install. Subsequent deploys are automatic.

Result: `https://<name>.run.mcp-use.com/mcp`

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
| `--env <K=V>` | deploy | `npm run deploy -- --env FOO=bar` |
| `--env-file <path>` | deploy | `npm run deploy -- --env-file .env` |
| `--name <name>` | deploy | `npm run deploy -- --name my-server` |

## Environment variables

These override script defaults:

| Variable | Scripts | Precedence | Default |
|----------|---------|-----------|---------|
| `PORT` | dev, start | flag > env > 3000 | 3000 |
| `HOST` | dev, start | flag > env > 127.0.0.1 | 127.0.0.1 |
| `NODE_ENV` | start | always `production` | — |
| `MCP_URL` | (client targeting) | used by Inspector | http://127.0.0.1:PORT/mcp |

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
