# MCP spec version history

The Model Context Protocol has evolved through several versions. `mcp-use` always targets the current spec while preserving backward compatibility for older clients.

## Spec milestones

| Spec date | Notable changes |
|---|---|
| **2024-11-05** | First public spec. Tools, resources, prompts, sampling, stdio + SSE transports. |
| **2025-03-26** | Streamable HTTP introduced as a replacement for SSE. Sessions, progress tokens. Elicitation added. |
| **2025-06-18** | Resource templates, structured content (`structuredContent`), tool annotations, `_meta` field. |
| **2025-11-25** | MCP Apps protocol (widgets) standardized. `text/html;profile=mcp-app` MIME. |
| **2026-03-04** | DCR (Dynamic Client Registration) for OAuth becomes the default. ChatGPT Apps SDK protocol distinct from MCP Apps. |

## How `mcp-use` handles version differences

- The server advertises the spec version it implements via `initialize` capabilities.
- Clients negotiate down to a shared version. `mcp-use` accepts older clients gracefully.
- Features that require newer spec versions are guarded — e.g. `ctx.client.can("elicitation")` returns `false` for clients below 2025-03-26.

## When you'll hit version issues

- **Older client + newer feature** → guard with `ctx.client.can(...)` (`16-client-introspection/03`) and supply a fallback. Don't crash.
- **Streamable HTTP rejected** → client wants SSE alias (`09-transports/06`).
- **Widget MIME unrecognized** → host predates MCP Apps; route to a non-widget tool path or set `widget` config to optional.

## Migrating between mcp-use versions

See `28-migration/`:

- `02-mcp-use-v1-to-v2.md`
- `03-sse-to-streamable-http.md`
- `04-appssdk-to-mcpapps.md`
- `05-dcr-vs-proxy-mode-shift.md`

**Canonical doc:** https://manufact.com/docs/typescript/changelog/changelog
