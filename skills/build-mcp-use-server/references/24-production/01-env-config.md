# Environment configuration for production

*Read this when setting up a production deployment.*

Production servers require these environment variables at startup. In serverless runtimes, pass them via the platform's environment configuration UI; in Node.js, use `.env` files or process manager (systemd, PM2, etc.) exports.

## Core server variables

| Variable | Runtime | Purpose | Default | Notes |
|----------|---------|---------|---------|-------|
| `PORT` | Node.js, edge | HTTP listen port | `3000` | Port precedence: argument > `PORT` env > `config.port` > `3000`. In containerized runtimes (Cloud Run, Fly), set to `$PORT` (platform-injected). |
| `HOST` | Node.js | Bind address | `127.0.0.1` | Use `0.0.0.0` for public binding behind a reverse proxy. Localhost-class binds (`127.0.0.1`, `::1`) get DNS-rebinding protection by default. |
| `NODE_ENV` | Node.js | Runtime mode | `development` | Set to `production` in deploy; controls logging level and performance features. |
| `MCP_URL` | Build-time | Public MCP endpoint | — | **Build-time only.** Set before `mcp-use build` so views link to correct origin: `MCP_URL=https://api.example.com/mcp npm run build`. Baked into View HTML; not read at runtime. |
| `MCP_ASSETS_URL` | Build-time | View assets CDN origin | `${MCP_URL}` | **Build-time only.** For edge runtimes with external CDN: `MCP_ASSETS_URL=https://cdn.example.com/mcp-assets`. Views load from this origin. |

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
    level: process.env.NODE_ENV === "production" ? "info" : "debug",
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
| `NODE_ENV` | `production`, `development` | When `production`, logging defaults to `info`; when `development`, defaults to `debug`. |

## Stateless request model

v2 builds a fresh MCP server from the registry **per request**; no persistent session state at runtime. Each variable is read once during server construction, then used identically for every request.

Do **not** change environment variables while the server is running in production — no reload hooks exist. Use:
- **Container restart** (Kubernetes, Cloud Run) for env changes
- **Blue-green deployment** for zero-downtime updates
- **Process manager (systemd, PM2)** with restart hooks on `.env` changes (local development only)

## Verification

After setting up environment variables, verify the server starts cleanly:

```bash
# Local development
npm run build  # Uses MCP_URL at build time
npm run start

# Docker / container
docker run -e PORT=8080 -e NODE_ENV=production -e MCP_URL=https://api.example.com/mcp my-server:latest
```

Read `references/25-deploy/` for platform-specific environment setup (Vercel, Cloud Run, Railway, etc.).
