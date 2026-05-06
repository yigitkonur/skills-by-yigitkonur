# Canonical: `mcp-use/mcp-multi-server-hub`

**URL:** https://github.com/mcp-use/mcp-multi-server-hub

The server-composition reference. Combines `MCPServer.proxy()` (async, v1.21.0+) with HTTP-layer middleware *and* MCP-operation middleware to log and audit every proxied tool call. The audit log is exposed back to clients via a hub-only tool and a `hub-dashboard` widget.

## Load-bearing files

| File | What to read it for |
|---|---|
| `index.ts` (`server.use(async (c, next) => ...)`) | HTTP request log middleware |
| `index.ts` (`server.use("mcp:tools/call", async (ctx, next) => ...)`) | MCP-operation middleware that records duration and tool name |
| `index.ts` (`PROXY_CONFIG` + `await server.proxy(PROXY_CONFIG)`) | Conditional proxy setup. The `await` is mandatory — without it `listen()` races the proxy initialisation |
| `index.ts` (`hub-status`, `audit-log`, `hub-config-example` tools) | Hub-local tools that surface audit data |
| `resources/hub-dashboard/widget.tsx` | Widget that renders the proxied servers and recent audit entries |

## Patterns demonstrated

| Pattern | Where |
|---|---|
| Async `server.proxy({ key: { url } / { command, args, env } })` | Top of `index.ts` |
| Two middleware layers: HTTP (`server.use(handler)`) and MCP-op (`server.use("mcp:tools/call", handler)`) | Top of `index.ts` |
| Audit log as an in-process array | `auditLog` array |
| Hub-local tools alongside namespaced proxied tools | `hub-status`, `audit-log` |
| Empty-config fallback (server runs even if no upstreams configured) | `PROXY_CONFIG` guard |

## Clusters this complements

- `../17-advanced/` — proxy and middleware deep dive
- `../15-logging/` — audit-log persistence options
- `../30-workflows/06-multi-server-proxy-gateway.md` — gateway without audit
- `../30-workflows/14-multi-server-hub-with-audit.md` — workflow derived from this repo

## When to study this repo

- You are putting any proxy in production and need audit-grade logging of upstream calls.
- You want to see HTTP and MCP-op middleware composed in one server.
- You are worried about the v1.21.0 async-proxy gotcha and want a confirmed-working `await server.proxy(...)` example.
- You need a UX for surfacing audit data back to operators.

## Local run

```bash
gh repo clone mcp-use/mcp-multi-server-hub
cd mcp-multi-server-hub
npm install
npm run dev
# Edit PROXY_CONFIG to add a real upstream, restart, observe the audit entries.
```
