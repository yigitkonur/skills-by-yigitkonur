# v1 → v2 Migration Overview

*Read this first if upgrading an mcp-use v1 server to v2.*

v1.34.5 to v2.0.0-beta.66 is a major rewrite. Import paths, tool registration, context shape, OAuth, and widgets all change. The migration checklist below maps every change; following sections dive into each category.

## Master delta table

| Feature | v1.34.5 | v2.0.0-beta.66 | Migrate to |
|---------|---------|---|---|
| **Import** | `mcp-use/server` | `mcp-use` (root) | Root import; see 03 |
| **Node.js** | >=20.19.0 \\|\\ >=22.12.0 | >=22.22.2 ESM only | Update `engines`; drop CommonJS |
| **Tool registration** | `schema` + `cb` | `inputSchema` + `outputSchema` + callback 2nd arg | See 03 |
| **Tool exports** | Optional | **Required** for Views | Export all static tools as `ToolRef` |
| **Response helpers** | `text()`, `object()`, etc. | Deprecated shims; prefer raw `CallToolResult` | Return `{ content, structuredContent }` |
| **Resource callback** | `(uri)` | `(uri, ctx)` | Add `ctx` parameter |
| **Template callbacks** | Nested `callbacks` | Top-level `complete` + `(uri, params, ctx)` | Flatten and add params |
| **Prompt schema** | `args: [{ name, schema }]` | Single `schema` field | Move to unified schema |
| **Context lifecycle** | Session-affine, stateful | Request-scoped, stateless | No sessions in beta.66; see 07 |
| **User ID** | `ctx.auth.user.userId` | `ctx.auth.user.id` (provider-specific) | Rename everywhere; see 05 |
| **OAuth config** | In MCPServer constructor | Provider factories from `mcp-use/oauth/*` | Move to separate import; see 05 |
| **OAuth Proxy** | `oauthProxy()` | **Removed** | Use external broker + `oauthCustomProvider`; see 05 |
| **Sampling** | `ctx.sample()` | **Removed** | Model generates; server provides tools; see 07 |
| **Widget location** | `resources/<name>/widget.tsx` | `views/<name>/view.tsx` | Rename directory |
| **Widget binding** | `widget: { name }` in tool | `view: { name }` in tool | Rename field |
| **Widget result** | `widget()` helper | Raw `{ content, structuredContent }` or deprecated helper | Prefer raw envelopes |
| **View hook** | `useWidget()` | `useToolContext<"tool-name">()` | Rename and add type param |
| **View state** | `useWidgetState()` + local state | `useViewState()` + React `useState()` + `<ModelContext>` | Split concerns; see 06 |
| **View component** | `McpUseProvider` wrapper | `<ThemeProvider>` + `<ErrorBoundary>` | Unwrap and use explicit providers |
| **HTTP transport** | Implicit for web | Explicit `server.listen(port)` or `server.fetch` | See 07 |
| **Stdio serving** | `server.listen({ stdio: true })` | **Removed** | Use HTTP adapters only |
| **Express/Connect** | `server.listen({ express, router })` | **Removed** | Use Hono (`server.app`) or `server.fetch`; see 07 |
| **Notifications** | `sendToolsChanged()` | `notifyToolsChanged()` | Rename; await result |
| **Resource notify** | `sendResourcesListChanged()` | `notifyResourcesChanged()` | Rename |
| **Session store** | `sessionStore` option | **Not shipped in beta.66** | Use external DB keyed by `ctx.auth`; see 07 |

## What's removed entirely

| Feature | v1 | v2 Status | Migration |
|---------|----|----|---|
| OAuth Proxy (`oauthProxy`) | ✓ | ✗ Removed | Deploy external auth server; use `oauthCustomProvider` for verification |
| Session stores (InMemory, Redis, Filesystem) | ✓ | ✗ Not shipped in beta.66 | Use application-owned DB keyed by `ctx.auth.user.id` |
| Post-response push | `sendNotificationToSession()` | ✗ Removed | Use subscription listeners only (request-scoped) |
| Server-side sampling | `ctx.sample()` | ✗ Removed | Delegate generation to client/model; server provides deterministic tools |
| Stdio serving | `server.listen({ stdio: true })` | ✗ Removed | Use HTTP adapters or compatible CLI clients |
| Express/Connect adapters | `server.listen({ express })` | ✗ Removed | Use Hono (`server.app`) or `server.fetch` |
| `@mcp-ui/server` adapters | ✓ | ✗ Removed | Use MCP Apps Views framework |
| v1 helper shims | `text()`, `widget()`, etc. | ✓ Deprecated only | Migrate to raw MCP envelopes |

## What's unchanged

| Feature | v1 | v2 | Note |
|---------|----|----|---|
| MCP protocol wire format | ✓ | ✓ | Same JSON-RPC; clients still don't assume sessions |
| Tool concept | ✓ | ✓ | Registration still exists; syntax changes only |
| Resource concept | ✓ | ✓ | Static and template variants both supported |
| Prompt concept | ✓ | ✓ | Arguments schema supported; `completable()` works |
| Zod schemas | ✓ | ✓ | v4 required (v3 no longer supported) |
| Completion helpers | ✓ | ✓ | Same signature and purpose |
| Middleware API | ✓ | ✓ | MCP event patterns identical |

## Migration sequence (8 steps)

1. **Imports & Node.js** (see `03-v1-to-v2-imports-server-and-tools.md`): Update `mcp-use` root import, Node.js to >=22.22.2, ESM-only config.
2. **Tools** (see `03`): Convert tools to definition-first + callback; update `schema` → `inputSchema`; add `outputSchema` for Views; export all static tools.
3. **Resources & Prompts** (see `03`): Migrate callback signatures and result shapes.
4. **Responses** (see `04-v1-to-v2-responses-and-helpers.md`): Return raw MCP envelopes; deprecate response helpers.
5. **Authentication** (see `05-v1-to-v2-auth.md`): Move OAuth providers to subpath imports; replace `ctx.auth.user.userId` with provider-specific `ctx.auth.user.id`; remove OAuth Proxy or replace with external broker.
6. **Widgets → Views** (see `06-v1-to-v2-widgets-to-views.md`): Rewrite as `views/<name>/view.tsx`; update hooks and component providers.
7. **Sessions & Transports** (see `07-v1-to-v2-sessions-transports-stdio-sse.md`): Remove session assumptions; migrate to HTTP-only; keyed state via `ctx.auth.user.id`.
8. **Apps SDK compatibility** (see `08-appssdk-to-mcp-apps.md`): If you have OpenAI Apps SDK code, rewrite to MCP Apps Views.

## Checklist: What breaks silently

⚠️ These will compile but fail at runtime without explicit fixes:

- Importing from `mcp-use/server` (path removed; use `mcp-use` root)
- Using `ctx.auth.user.userId` (field renamed to `ctx.auth.user.id`)
- Calling `ctx.sample()` (not available; design for model-side generation)
- Passing `sessionStore` to constructor (config option removed)
- Using `server.listen({ stdio: true })` (transport removed)
- Exporting helpers only, not tools (View typing breaks; export `ToolRef` instead)
- Raw v3 Zod schemas (must upgrade to v4)

## New patterns you'll adopt

1. **Stateless request model**: No session affinity; every request is independent. Store state externally keyed by `ctx.auth.user.id`.
2. **Definition-first tools**: Schema + callback separated; encourages cleaner code.
3. **Explicit Views**: Tool → View binding visible in tool definition; no auto-registry via directory.
4. **Hook composition**: View state split into model-visible (`useViewState`) and ephemeral (React `useState`).
5. **Raw MCP envelopes**: Type-safe; helpers remain as deprecated upgrade path only.

---

**Next**: Go to `03-v1-to-v2-imports-server-and-tools.md` to start the migration.
