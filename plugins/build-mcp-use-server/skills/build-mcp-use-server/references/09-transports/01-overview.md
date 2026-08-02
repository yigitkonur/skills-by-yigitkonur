# Transports in v2

*Read this when understanding how requests flow to the MCP server.*

v2 uses **Streamable HTTP only** — there is no stdio, SSE, or proprietary transport. All runtimes share one portable boundary: the Web-standard Fetch API at `server.fetch(request)`.

## Three transport patterns

1. **Node.js and filesystem runtimes (Railway, Manufact, Bun):** Call `server.listen(port)` to bind HTTP + automatic View file serving.
2. **Edge and serverless (Cloudflare Workers, Deno, Vercel):** Export `server.fetch` or mount via framework (`withMcpUse` for Next.js).
3. **Embedded in frameworks:** Use `mcp-use/next` or `mcp-use/node` adapters to bind the fetch handler.

## Default endpoint

MCP protocol requests route to `{basePath}` (default `/mcp`). All HTTP methods (GET, POST, DELETE, OPTIONS) on the MCP path and its subpaths are handled by the MCP handler; custom routes are mounted separately via `server.get()`, `server.post()`, etc.

## Request model

Every request is **stateless** — no session affinity, no server-side state carryover. The MCP SDK maintains per-request context; Clients (for `input_required` rounds) may send `requestState` on retry to allow the server to validate state integrity.

See `references/09-transports/03-stateless-and-request-state.md` for state codec usage.

## Cross-cluster references

- Runtime adapters: `04-runtime-adapters-node-next-fetch.md`
- Why stdio/SSE are gone: `05-no-stdio-and-sse-history.md`
- Sessions & scaling without session stores: `../10-sessions/`
