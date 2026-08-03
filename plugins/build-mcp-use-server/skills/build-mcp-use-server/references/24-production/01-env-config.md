# Environment configuration for production

*Read this when setting up a production deployment.*

Production servers require these environment variables at startup. In serverless runtimes, pass them via the platform's environment configuration UI; in Node.js, use `.env` files or process manager (systemd, PM2, etc.) exports.

## Core server variables

| Variable | Runtime | Purpose | Default | Notes |
|----------|---------|---------|---------|-------|
| `PORT` | Node.js, edge | HTTP listen port | `3000` | Port precedence: argument > `PORT` env > `config.port` > `3000`. In containerized runtimes (Cloud Run, Fly), set to `$PORT` (platform-injected). |
| `HOST` | Node.js | Bind address | `127.0.0.1` | Use `0.0.0.0` for public binding behind a reverse proxy. Localhost-class binds (`127.0.0.1`, `::1`) get DNS-rebinding protection by default. |
| `NODE_ENV` | Node.js | Runtime mode | unset | Set to `production` only by the `mcp-use start` CLI (forces `process.env.NODE_ENV ??= "production"`). Controls favicon/View dev-mode branding only — **not** logging level, which is governed entirely by `MCP_USE_LOG_LEVEL`/`config.logging.level` (see Logging control below). |
| `MCP_URL` | Build and runtime | Public server origin | request origin | Read **at runtime, per request** by `resolveServerOrigin()` to resolve the public server origin (OAuth resource identity, CSP `connectDomains`, View asset base fallback when `MCP_ASSETS_URL` is unset). Falls back to forwarded/request headers when unset. Also has a narrow build-time role: a synthetic `http://localhost:3000` default is used only for build-time OAuth entry-module inspection when unset. Set explicitly in production: `MCP_URL=https://api.example.com`. |
| `MCP_ASSETS_URL` | Build and runtime | View assets CDN origin | `MCP_URL` (or request origin) | Read at runtime by `resolveAssetsBase()` for every View asset request. Also read at `mcp-use build` time to rewrite the asset manifest to absolute `https://` URLs for static/CDN upload workflows. For edge runtimes with external CDN: `MCP_ASSETS_URL=https://cdn.example.com/mcp-assets`. |

## OAuth variables (per provider)

Each OAuth provider requires its own environment variables. See `references/11-auth/providers/` for exact names. Example:

```bash
# Clerk
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# Supabase
SUPABASE_URL=https://project.supabase.co
SUPABASE_ANON_KEY=eyJ...
```

Store secrets in your platform's secret manager (GitHub Secrets, Vercel Secrets, Cloud Secret Manager, etc.); never commit to git.

## Application variables

Store business logic config (API keys, database URLs, feature flags) as regular environment variables. The server reads these at startup; changes require restart or hot reload (dev only).

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "inventory-server",
  version: "1.0.0",
  basePath: "/mcp",
  host: process.env.HOST || "0.0.0.0",
  port: parseInt(process.env.PORT || "3000", 10),
  logging: {
    level: "info", // Or set MCP_USE_LOG_LEVEL=debug/trace per-environment instead
  },
});

// Access app config
const apiKey = process.env.EXTERNAL_API_KEY;
const dbUrl = process.env.DATABASE_URL;
```

## Health check variables (optional)

Define custom health check routes via custom HTTP endpoints on `server.app` (see `references/24-production/03-health-and-custom-routes.md`). No built-in health variable; most platforms infer health from response codes.

## Logging control

| Variable | Values | Effect |
|----------|--------|--------|
| `MCP_USE_LOG_LEVEL` | `info`, `debug`, `trace` | Overrides `config.logging.level`. At `info`, one summary line per request; at `debug`, compact payloads; at `trace`, full headers/body. |
| `NODE_ENV` | — | **No effect on logging level.** Resolution order is `MCP_USE_LOG_LEVEL` env (if valid) > `config.logging.level` > `"info"` default, always — regardless of `NODE_ENV`. |

## Stateless request model

v2 builds a fresh MCP server from the registry **per request**; no persistent session state at runtime. Most variables (`PORT`, `HOST`, OAuth credentials, `config.logging.level`) are read once during server construction and reused for every request. `MCP_URL` and `MCP_ASSETS_URL` are the exception — `resolveServerOrigin()`/`resolveAssetsBase()` re-read them from `process.env` on every request rather than caching a construction-time value.

Do **not** change environment variables while the server is running in production — no reload hooks exist. Use:
- **Container restart** (Kubernetes, Cloud Run) for env changes
- **Blue-green deployment** for zero-downtime updates
- **Process manager (systemd, PM2)** with restart hooks on `.env` changes (local development only)

## Verification

After setting up environment variables, verify the server starts cleanly:

```bash
# Local development
npm run build  # MCP_ASSETS_URL (if set) rewrites the asset manifest to absolute URLs
npm run start  # MCP_URL and MCP_ASSETS_URL are read per-request at this point

# Docker / container
docker run -e PORT=8080 -e NODE_ENV=production -e MCP_URL=https://api.example.com my-server:latest
```

Read `references/25-deploy/` for platform-specific environment setup (Vercel, Cloud Run, Railway, etc.).
