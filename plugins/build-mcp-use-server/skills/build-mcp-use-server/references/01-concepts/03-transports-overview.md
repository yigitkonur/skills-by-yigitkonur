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
- View assets served at `/_mcp-use/views/` subtree
- Inspector automounts at `/mcp/inspector` during `mcp-use dev`

## Binding to runtimes

| Runtime | Adapter | How |
|---------|---------|-----|
| **Node.js** | `mcp-use/node` | `toNodeHandler(server)` wraps `server.fetch` for `http.createServer((req, res) => ...)` |
| **Next.js** | `mcp-use/next` | `createNextHandler(server)` exports `{ GET, POST, DELETE, OPTIONS }` for App Router |
| **Cloudflare Workers** | `server.fetch` | Direct mount; views via static binding |
| **Vercel Functions** | `server.fetch` | Catch-all function; views included in bundle |
| **Deno Deploy** | `server.fetch` | Direct mount; external assets via CDN |
| **Hono** | `server.fetch` | Mount at route: `app.all("/mcp", c => server.fetch(c.req.raw))` |
| **Supabase Edge Fn** | `server.fetch` | Deployed with `static_files` config |
| **Google Cloud Run** | `server.fetch` | Default export or `POST` export |

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
