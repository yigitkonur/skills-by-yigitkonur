# Transports overview

Pick the runtime surface based on **who owns the HTTP lifecycle**. For the conceptual decision matrix and statefulness axis, see `../01-concepts/03-transports-overview.md` and `../01-concepts/04-stateful-vs-stateless.md`.

## Supported mcp-use server surfaces

| Surface | Entry call | Who connects | Sessions | Reference |
|---|---|---|---|---|
| **Streamable HTTP** | `await server.listen(port?)` | Web hosts, ChatGPT, programmatic clients | Auto-detected per request on Node.js | `03-streamable-http.md` |
| **Fetch/serverless handler** | `await server.getHandler(opts?)` | Cloudflare Workers, Supabase Edge, Deno Deploy, other Fetch runtimes | Deno defaults stateless; set `stateless: true` explicitly for other serverless/edge runtimes | `05-serverless-handlers.md` |
| **SSE alias** | Auto-mounted at `/sse` when HTTP endpoints mount | Legacy MCP clients | Same handler and session lifecycle as `/mcp` | `06-sse-alias.md` |

`stateless: true` is a **mode**, not a separate transport. It changes how the HTTP handler processes requests; see `04-stateless-mode.md`.

## Not a mcp-use server transport

`mcp-use@1.26.0` does not expose a server-side stdio entry call. `MCPServer` exposes `listen(port?)` and `getHandler(opts?)`; the CLI `mcp-use start` is the documented production HTTP command with `--port`.

If a host strictly requires a spawned stdio child process, use a separate stdio implementation outside `mcp-use/server`. See `02-stdio.md` and `../02-setup/04-manual-stdio-server.md`.

## Default decisions

| You are building | Use |
|---|---|
| Hosted server reachable over the network | Streamable HTTP (`03-streamable-http.md`) |
| Edge / serverless deploy | Fetch handler (`05-serverless-handlers.md`) plus stateless rules (`04-stateless-mode.md`) |
| Pure request/response service, no notifications | Streamable HTTP with `stateless: true` (`04-stateless-mode.md`) |
| Backward compatibility with legacy MCP clients | `/sse` alias (`06-sse-alias.md`) while publishing `/mcp` for new clients |
| Strict local stdio package | Separate stdio implementation, not `mcp-use/server` (`02-stdio.md`) |

## What mcp-use does not ship

- **Server-side stdio for `MCPServer`** - the published package exposes HTTP listener and Fetch-handler surfaces, not a stdio server surface.
- **WebSockets** - not a first-class server transport. Streamable HTTP covers stateful MCP over normal HTTP.
- **Custom transport adapters** - `MCPServer` exposes `listen()` and `getHandler()`; put unusual transport needs in a sidecar.

## Cross-cluster references

- Statefulness rules: `../01-concepts/04-stateful-vs-stateless.md`
- CORS / `allowedOrigins` (single source): `../08-server-config/03-cors-and-allowed-origins.md`
- Network bind / public URL: `../08-server-config/02-network-config.md`
- Session stores for stateful HTTP: `../10-sessions/`

**Canonical docs:** https://manufact.com/docs/typescript/server, https://manufact.com/docs/typescript/server/cli-reference
