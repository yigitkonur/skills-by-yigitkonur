# Canonical Anchor: `mcp-use/mcp-multi-server-hub`

Reference implementation for gateway composition. Mirror the pattern, not nonexistent `src/` paths: the example app is rooted at `index.ts`.

---

## Repo

`mcp-use/mcp-multi-server-hub` (GitHub)

A worked example of a gateway built on `MCPServer`:

- Defines `PROXY_CONFIG` and calls `await server.proxy(PROXY_CONFIG)` when entries are present.
- Adds Hono middleware with `server.use(async (c, next) => ...)`.
- Adds MCP operation middleware with `server.use("mcp:tools/call", ...)`.
- Exposes local tools (`hub-status`, `hub-config-example`, `audit-log`) beside proxied tools.
- Serves a dashboard widget from `resources/hub-dashboard/widget.tsx`.

---

## Load-Bearing Files

Read these first when adapting the pattern:

| File | What it shows |
|---|---|
| `index.ts` | `MCPServer` constructor, Hono middleware, MCP operation middleware, `PROXY_CONFIG`, conditional `await server.proxy(PROXY_CONFIG)`, local tools, and `server.listen()`. |
| `resources/hub-dashboard/widget.tsx` | Dashboard widget rendered by the `hub-status` tool. |
| `resources/hub-dashboard/types.ts` | Shared props/types for the dashboard widget. |
| `resources/styles.css` | Widget stylesheet loaded by the resource UI. |

---

## What to Mirror

1. **Async proxy registration at startup.** The example awaits `server.proxy(PROXY_CONFIG)` before registering the always-local hub tools.
2. **Two middleware layers.** Use Hono `server.use(...)` for HTTP concerns and `server.use("mcp:tools/call", ...)` for MCP operation audit/rate-limit logic.
3. **Audit the tool call name.** The example reads `ctx.params.name` in MCP operation middleware.
4. **Keep local tools available.** Gateway tools coexist with proxied tools and can expose status/config/audit data.

---

## See Also

- **Proxy mechanics** → `01-server-proxy-and-gateway.md`
- **Per-user upstream auth** → `02-session-based-proxy.md`
- **Hono middleware and custom routes** → `../08-server-config/05-middleware-and-custom-routes.md`
