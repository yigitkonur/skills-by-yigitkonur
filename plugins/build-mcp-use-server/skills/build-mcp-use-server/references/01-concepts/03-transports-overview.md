# Transports Overview

*Read this when you need to understand how clients reach your MCP server.*

## v2 transport: Streamable HTTP

v2 uses **Web-standard Fetch API only** — no stdio, no SSE aliases.

**How it works:**
- Server exports `server.fetch(request: Request): Promise<Response>` handler
- Client sends HTTP POST to `/mcp` endpoint (configurable basePath, default `/mcp`)
- SDK manages streaming, stateless exchanges
- MCP protocol envelope frames sent as JSON request/response bodies

**Capabilities:**
- GET, POST, DELETE, OPTIONS (CORS preflight)
- Production View bundles served at `${basePath}/_mcp-use/views/<name>/...`; public files at `${basePath}/_mcp-use/public/...`
- Inspector automounts at `/mcp/inspector` during `mcp-use dev` (production: `mcp-use start --with-inspector` mounts it at `${basePath}/inspector`)

## Binding to runtimes

| Runtime | Adapter | How |
|---------|---------|-----|
| **Node.js** | `mcp-use/node` | `toNodeHandler(server)` wraps `server.fetch`; pass the result to `http.createServer(...)` |
| **Next.js** | `mcp-use/next` | `createNextHandler(server)` exports `{ GET, POST, DELETE, OPTIONS }` for App Router |
| **Supabase Edge Functions** | `server.fetch` directly | Edge Function forwards requests to `server.fetch`; no `listen()` call. Set `basePath` to match the gateway prefix (e.g. `/functions/v1/mcp-server/mcp`) |
| **Google Cloud Run** | CLI-built server, no direct adapter | `mcp-use start` binds `0.0.0.0` and Cloud Run's injected `PORT`; set `host: "0.0.0.0"` in `ServerConfig` |
| **Cloudflare Workers, Vercel, Deno Deploy, Hono, Bun, Railway** | `server.fetch` | Plain Web-standard `server.fetch(request: Request): Promise<Response>` — mount under any router or platform accepting that signature. Per-platform View-asset topology differs (co-located static binding vs. `MCP_ASSETS_URL` CDN) |

See `25-deploy/01-decision-matrix.md` for the full target/asset-topology matrix and `25-deploy/platforms/` for a file per platform (Manufact Cloud, Vercel, Cloudflare Workers, Google Cloud Run, Supabase, Deno, Bun, Hono, Railway).

## No stdio in v2

v1 supported:
- `server.listen({ stdio: true })` — Claude Desktop integration (removed)
- Stdio child-process proxy (removed)
- Express/Connect adapters (removed)
- SSE transport (removed; streamable HTTP is the replacement)

**v2 path:** Use HTTP endpoints only. Claude Desktop, Cursor, and other clients connect via HTTP.

## What stayed

- MCP protocol wire format (tools, resources, prompts, notifications, resource subscriptions)
- Zod schemas for input/output validation
- Context (`ctx`) per-request surface
- Middleware patterns (`mcp:*` events)

See `09-transports/01-overview.md` for detailed HTTP mechanics and `09-transports/05-no-stdio-and-sse-history.md` for migration context.
