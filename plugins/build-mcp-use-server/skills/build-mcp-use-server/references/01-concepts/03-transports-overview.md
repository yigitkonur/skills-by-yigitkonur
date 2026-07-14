# Transports overview

`mcp-use/server` is HTTP-first. `MCPServer` exposes `listen(port?)` for a standalone HTTP server and `getHandler()` for a Fetch-compatible handler. There is no first-class server-side stdio transport.

| Transport | Who calls it | When to use |
|---|---|---|
| **Streamable HTTP** | Claude Desktop (URL form), ChatGPT, Cursor (URL form), Inspector, programmatic clients | Default for local, hosted, and deployed mcp-use servers |
| **Serverless handler** | Vercel / Cloudflare Workers / Supabase Edge / Deno Deploy | Same as Streamable HTTP, returned via `getHandler()` |
| **SSE (legacy)** | Older MCP clients before the Streamable HTTP migration | Backward-compatibility only; `/sse` is an automatic alias for `/mcp` |
| **stdio** | Legacy hosts requiring a spawned child process with JSON-RPC over stdin/stdout | **Not supported by `mcp-use/server`** — drop to `@modelcontextprotocol/sdk` directly (see `09-transports/02-stdio.md`) |

## Default decisions

- **Greenfield local server** → Streamable HTTP on `localhost`. `mcp-use dev` runs it with HMR; `mcp-use start` runs the built artifact. Configure URL-capable clients with `{ "url": "http://localhost:3000/mcp" }`.
- **Greenfield hosted server** → Streamable HTTP. `mcp-use deploy` ships it.
- **Greenfield serverless** → Streamable HTTP via the platform's handler adapter (`05-serverless-handlers.md`).
- **Adding to existing app** → side-car HTTP server on its own port; do not embed as middleware (`08-server-config/05`).
- **Strict stdio-only client** → not an `mcp-use/server` use case. See `02-setup/04-manual-stdio-server.md` for the raw-SDK fallback.

## What about WebSockets?

Not a first-class transport in `mcp-use`. Streamable HTTP supports the streaming patterns most servers need (progress, notifications, sampling, elicitation) over normal HTTP.

## Stateful vs stateless

A second axis on top of transport choice — see `04-stateful-vs-stateless.md`.

## Read next

- `04-stateful-vs-stateless.md` — second axis
- `09-transports/` — full per-transport guide

**Canonical doc:** https://manufact.com/docs/typescript/server
