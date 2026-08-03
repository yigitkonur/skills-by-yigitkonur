# Environment Variables

*Read this to understand which env vars the CLI and server respect.*

## CLI-respected variables

These affect CLI command behavior:

| Variable | Used by | Default | Effect |
|----------|---------|---------|--------|
| `$PORT` | dev, start | `3000` | HTTP listener port (flag `--port`/`-p` takes precedence) |
| `$HOST` | dev, start | `127.0.0.1` | HTTP listener address (flag `--host` takes precedence) |
| `$NODE_ENV` | start | unset | Set to `production` by `start` only if not already set (`process.env.NODE_ENV ??= "production"`); an explicit value already present is never overridden. `dev` never sets `NODE_ENV` at all |
| `$MCP_URL` | dev, server runtime | unset | **Not** the tunnel URL. `dev` writes a temporary `http://localhost:${port}` fallback into `process.env.MCP_URL` only while the server entry module loads, and only when `MCP_URL` was unset AND the bind host is loopback (`127.0.0.1`/`localhost`/`::1`) — restored to its prior value afterward. See "The `$MCP_URL` / tunnel misconception" below |
| `$MCP_ASSETS_URL` | build, server runtime | unset | CDN/static-hosting prefix for view JS/CSS/public assets; when set, `mcp-use build` rewrites each view's asset manifest to point there instead of the server's own origin |
| `$npm_config_user_agent` | create-mcp-use-app | auto-detect | Detects package manager (npm/pnpm/bun) from invocation; set by the package manager itself, not user-configured |
| `$MCP_USE_API_KEY` | login | unset | Fallback API key read by `mcp-use login` when neither `--api-key` nor `--device-code` is passed |
| `$MCP_USE_CLOUD_API_URL` / `$MCP_API_URL` | login, deploy, org, servers, deployments | `https://cloud.manufact.com/api/v1` | Overrides the cloud API base URL (`MCP_USE_CLOUD_API_URL` takes precedence over `MCP_API_URL`) |
| `$MCP_USE_CLOUD_WEB_URL` | deploy (`--open`), login | `https://manufact.com` | Overrides the cloud web app base URL used to build browser-facing links |
| `$MCP_USE_TUNNEL_API` | dev, start (`--tunnel`) | (built-in tunnel API) | Overrides the tunnel control-plane API base URL |
| `$MCP_USE_CHROME_PATH` / `$PUPPETEER_EXECUTABLE_PATH` / `$CHROME_PATH` | screenshot | auto-detect | Explicit path to a Chrome/Chromium/Edge/Brave binary; checked in this order before OS-specific auto-detection (which also reads `$PROGRAMFILES`/`$LOCALAPPDATA` on Windows) |
| `$MCP_USE_OAUTH_DEBUG` | client, server runtime | unset | Enables verbose OAuth flow logging |
| `$MANUFACT_CHAT_URL` | dev, start (`--with-inspector`) | (built-in) | Overrides the hosted chat endpoint injected into the Inspector shell |

### The `$MCP_URL` / tunnel misconception

A common but incorrect assumption is that `mcp-use dev --tunnel` sets `$MCP_URL` to the public tunnel URL. It does not, and no CLI-respected env var carries the tunnel URL:

- The tunnel's public URL is reported to the terminal via the `➜ Tunnel:        <url><basePath>` console line (see `03-mcp-use-dev.md`).
- Inside the running dev server, the Inspector's own `GET {basePath}/inspector/api/dev/info` JSON endpoint exposes the live tunnel URL through a same-named-but-distinct `mcpUrl` JSON field — computed fresh per request, never written to `process.env`.
- `process.env.MCP_URL` itself is touched only for a same-machine loopback fallback (`http://localhost:${port}`), and only transiently while the server entry module is imported — irrelevant to `--tunnel`.
- The standalone `npx @mcp-use/inspector` CLI (used outside a `mcp-use dev` session) reads zero environment variables.

If your server code needs the public tunnel URL, read it from the Inspector's dev-info API at runtime rather than from `process.env.MCP_URL`.

## Server-respected variables

Your MCP server receives all environment variables at runtime. Common patterns:

```bash
# Auth
export DATABASE_URL=postgres://user:pass@host/db
export OPENAI_API_KEY=sk-...
export OAUTH_CLIENT_ID=client123
export OAUTH_CLIENT_SECRET=secret456

# Deployment
export NODE_ENV=production
export PORT=8080
export LOG_LEVEL=debug

# Then run your server
mcp-use dev
mcp-use start
mcp-use deploy --env DATABASE_URL=$DATABASE_URL
```

CSP-related env vars (`CSP_URLS`, `CSP_CONNECT_DOMAINS`, `CSP_RESOURCE_DOMAINS`, `CSP_FRAME_DOMAINS`, `CSP_BASE_URI_DOMAINS`) configure the views Content-Security-Policy at server runtime; see the server-config reference for that cluster rather than this CLI doc.

## deploy: passing env to cloud

Use `--env` or `--env-file` to set runtime env vars on the cloud deployment:

```bash
# Individual vars
mcp-use deploy --env API_KEY=secret --env DB_URL=postgres://...

# Load from file
mcp-use deploy --env-file .env.production
```

Vars passed via `--env` or `--env-file` override defaults and are stored in Manufact Cloud; your code reads them via `process.env` at runtime.

## Securing secrets

**Do not:**
- Commit `.env` files to git (add `.env*` to `.gitignore`)
- Pass API keys as command-line args where they appear in shell history

**Do:**
- Use CI secrets (GitHub Actions `secrets.MY_KEY`)
- Store in `.env.production` (git-ignored) for local deploys
- Use Manufact Cloud env var UI for persistent secrets

**Example CI workflow (GitHub Actions):**
```yaml
- name: Deploy to Manufact
  env:
    MCP_USE_API_KEY: ${{ secrets.MCP_USE_API_KEY }}
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: |
    mcp-use login --api-key "$MCP_USE_API_KEY"
    mcp-use deploy --env DATABASE_URL="$DATABASE_URL"
```

`$MCP_USE_API_KEY` is also read automatically by `mcp-use login` when `--api-key`/`--device-code` are both omitted — the explicit `--api-key "$MCP_USE_API_KEY"` above is for clarity, not strictly required.

## Priority order

For a given env var, the precedence is:

1. Flag (e.g., `--port 8000`)
2. Environment variable (e.g., `$PORT=8000`)
3. Default (e.g., `3000`)

Example:

```bash
# $PORT is set but flag overrides
PORT=9000 mcp-use dev --port 8000
# → listens on 8000

# Only $PORT is set
PORT=9000 mcp-use dev
# → listens on 9000

# Neither set
mcp-use dev
# → listens on 3000
```

## Accessing env vars in your server code

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

// Read env at startup; callbacks capture these values.
const apiBaseUrl = process.env.API_BASE_URL;
const apiKey = process.env.API_KEY;

export const query = server.tool(
  {
    name: "query",
    description: "Fetch a text response from the configured application API.",
    inputSchema: z.object({
      path: z.string().min(1).describe("API path relative to API_BASE_URL"),
    }),
  },
  async ({ path }) => {
    if (!apiBaseUrl || !apiKey) {
      return {
        isError: true,
        content: [{ type: "text", text: "API_BASE_URL and API_KEY must be set" }],
      };
    }

    const response = await fetch(new URL(path, apiBaseUrl), {
      headers: { authorization: `Bearer ${apiKey}` },
    });
    const text = await response.text();

    return {
      content: [{ type: "text", text }],
      ...(response.ok ? {} : { isError: true as const }),
    };
  }
);

export default server;
```

This is a CLI-managed entry: `mcp-use dev` or `mcp-use start` owns the listener, so the module default-exports the server and does not call `listen()`.

## Common issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Cannot find API key" | Env var not set | `export KEY=value` before running CLI |
| Port already in use | `$PORT` or default conflicts | `PORT=8000 mcp-use dev` or use `--port` |
| Build fails with `undefined` | Env var referenced but not defined | Check `.env` or pass via `--env` |
| Cloud deploy missing secret | Env var not passed to deploy | Use `--env` or `--env-file` |

## Deployment example

```bash
# Local development (reads from shell env)
export DATABASE_URL=localhost
mcp-use dev

# Production deploy (passes env to cloud)
mcp-use deploy \
  --env DATABASE_URL=postgres://prod-db/... \
  --env OPENAI_API_KEY=sk-prod-key \
  --env NODE_ENV=production
```
