# Transports overview

Every mcp-use server speaks at least one transport. Pick based on **who calls it**:

| Transport | Who calls it | When to use |
|---|---|---|
| **stdio** | Claude Desktop, Cursor, VSCode (local clients via spawned process) | Local-only servers, CLI-installed servers, dev workflows |
| **Streamable HTTP** | Web hosts, ChatGPT, programmatic clients | Hosted/deployed servers; the modern remote default |
| **Serverless handler** | Vercel / Cloudflare Workers / Supabase Edge / Deno Deploy | Same as Streamable HTTP, but as a stateless function |
| **SSE (legacy)** | Older MCP clients before the Streamable HTTP migration | Only for backward compatibility |

## Default decisions

- **Greenfield local server** → stdio. `mcp-use start` runs it directly.
- **Greenfield hosted server** → Streamable HTTP. `mcp-use deploy` ships it.
- **Greenfield serverless** → Streamable HTTP via the platform's handler adapter (`05-serverless-handlers.md`).
- **Adding to existing app** → side-car HTTP server on its own port; do not embed as middleware (`08-server-config/05`).

## What about WebSockets?

Not a first-class transport in `mcp-use`. Streamable HTTP supports the streaming patterns most servers need (progress, notifications, sampling, elicitation) over normal HTTP.

## Stateful vs stateless

A second axis on top of transport choice — see `04-stateful-vs-stateless.md`.

## Read next

- `04-stateful-vs-stateless.md` — second axis
- `09-transports/` — full per-transport guide

**Canonical doc:** https://manufact.com/docs/typescript/server
