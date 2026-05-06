# SSE alias (legacy)

`/sse` is a backward-compatibility alias for `/mcp`. Same handler, same session lifecycle, same auth - just a legacy URL for clients written before the Streamable HTTP migration.

When `server.listen()` runs, both `/mcp` and `/sse` are mounted automatically. There is no separate SSE-only mode and no opt-out.

## Why deprecated

The older split-route MCP protocol used separate write and stream URLs. Streamable HTTP collapses both into a single `/mcp` endpoint with method-based routing; mcp-use keeps `/sse` as an alias for compatibility:

| Era | Write | Stream | Status |
|---|---|---|---|
| Pre-Streamable HTTP | Separate write route | `GET /sse` | Migrate away |
| Transitional | `POST /mcp` or `POST /sse` | `GET /mcp` or `GET /sse` | Acceptable during migration |
| Current spec-aligned | `POST /mcp`, `GET /mcp` | `GET /mcp` | Preferred |

Benefits of the unified `/mcp`:

- One route to expose, secure, log, and rate-limit.
- One session contract across `POST`, `GET`, `DELETE`, `HEAD`.
- No discovery split between message and stream URLs.

## When `/sse` is still useful

| Case | Action |
|---|---|
| Old MCP client hardcoded to `/sse` | Leave the alias mounted (it's free) |
| New deployments | Document and publish only `/mcp` |
| Internal-only environments with full client control | Migrate clients off `/sse`; the alias is automatic anyway |

## Migration

For full migration steps from the legacy split-route protocol to Streamable HTTP, including dual-route compatibility, proxy rewrites, and client cutover, see `../28-migration/03-sse-to-streamable-http.md`.

Quick checklist:

1. Add `/mcp` first while `/sse` keeps working - `listen()` handles both automatically.
2. Switch docs and examples to `POST /mcp` and `GET /mcp`.
3. Update client configs to point at the new endpoint.
4. Log usage by route. Once `/sse` traffic is gone, the alias can stay (it's automatic) but stop publishing it.

## What not to do

- Do not register custom handlers on `/sse` - the alias points to `/mcp`'s handler.
- Do not document `/sse` for new clients.
- Do not assume the older split write route works in mcp-use. Use a reverse-proxy rewrite if you must support it during migration (`../28-migration/03-sse-to-streamable-http.md`).
