# v1 → v2 Migration Overview

*Read this first if upgrading an mcp-use v1 server to v2.*

v1.34.5 to v2.0.0-beta.66 is a major rewrite. Import paths, tool registration, context shape, OAuth, and widgets all change. The migration checklist below maps every change; following sections dive into each category.

## Master delta table

| Feature | v1.34.5 | v2.0.0-beta.66 | Migrate to |
|---------|---------|---|---|
| **Import** | `mcp-use/server` | `mcp-use` (root) | Root import; see 03 |
| **Node.js** | `^20.19.0 \|\| >=22.12.0` | `>=22.22.2`, ESM only | Update `engines`; drop CommonJS |
| **Tool registration** | `schema` + `cb` | `inputSchema` + `outputSchema` + callback 2nd arg | See 03 |
| **Tool exports** | Optional | **Required** for Views | Export all static tools as `ToolRef` |
| **Response helpers** | `text()`, `object()`, etc. | Deprecated shims; prefer raw `CallToolResult` | Return `{ content, structuredContent }` |
| **Resource callback** | `()` or `(ctx)` (legacy v1 callback receives context, not requested URI) | `(uri, ctx)` | Add requested URI as first parameter; context moves to second |
| **Template config/callbacks** | Legacy nested `resourceTemplate.callbacks.complete` or newer flat `uriTemplate` + `callbacks.complete`; callbacks could take `(uri, params, ctx?)` | Flat top-level `uriTemplate` + `complete`; canonical `(uri, params, ctx)` callback | Remove legacy nesting; move `callbacks.complete`; use canonical signature |
| **Prompt schema** | `args: [{ name, type, required? }]` (deprecated even in v1; `schema` preferred there too) | Single `schema` field only — `args` removed | Move to unified `schema` |
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
| **View component** | `McpUseProvider` wrapper | Framework-owned bootstrap; optional `ThemeProvider`, `ViewControls`, nested `ErrorBoundary` | Remove aggregate provider |
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
| JSON-RPC/MCP result envelope concept | ✓ | ✓ | Still JSON-RPC with `content`/`structuredContent`/resource/prompt envelopes; protocol revisions and capabilities did change (v2 SDK targets date-string revisions such as `2026-07-28`) |
| Tool concept | ✓ | ✓ | Registration still exists; syntax changes only |
| Resource concept | ✓ | ✓ | Static and template variants both supported |
| Prompt concept | ✓ | ✓ | Arguments schema supported; `completable()` works |
| Zod schemas | ✓ (v4 peer dependency in v1.34.5) | ✓ | Zod v4 requirement carries over unchanged, not new in v2 |
| Completion helpers | ✓ | ✓ | Same signature and purpose |
| Middleware concept | ✓ | ✓ | `server.use(...)` remains, but imports, request context, and session assumptions must migrate |

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

## New patterns you'll adopt

1. **Stateless request model**: No session affinity; every request is independent. Store state externally keyed by `ctx.auth.user.id`.
2. **Definition-first tools**: Schema + callback separated; encourages cleaner code.
3. **Explicit Views**: Tool → View binding visible in tool definition; no auto-registry via directory.
4. **Hook composition**: View state split into model-visible (`useViewState`) and ephemeral (React `useState`).
5. **Raw MCP envelopes**: Type-safe; helpers remain as deprecated upgrade path only.

## Migration Exit Gate

Do not stop after text substitutions. Prove the migrated server is in the v2 package/API world and exercises the original behavior:

1. **Classify installed packages:** run the bundled `scripts/check-mcp-use-version.sh`; confirm `mcp-use` is 2.x/beta, has no `./server` export, and the CLI is 4.x/beta.
2. **Scan for removed patterns:** search the migrated project for `mcp-use/server`, `ctx.sample`, `ctx.elicit`, `ctx.session`, `sessionStore`, stdio/SSE listener config, `widget:`, `useWidget`, and `resources/<name>/widget.tsx`. Every remaining hit must be an intentional comment/migration fixture, not live code.
3. **Static proof:** run `mcp-use typecheck` separately from `mcp-use build`; build alone is transpile-only.
4. **Protocol proof:** start the migrated server and complete either the native modern probe in `references/09-transports/02-streamable-http.md` or the verified legacy initialize/list/call sequence in `references/22-validate/02-curl-handshake.md`.
5. **Auth proof when applicable:** public discovery metadata works, a valid unauthenticated MCP POST returns 401, and a real OAuth client calls a protected tool.
6. **View proof when applicable:** text fallback is useful, the View renders, assets load, and CSP/browser console checks are clean in the target host.
7. **Deployment proof when applicable:** identify the exact deployment/revision, wait for terminal success, then repeat the relevant live operation against the dashboard/platform URL.

Claim only the highest rung actually observed; a clean search or typecheck does not prove runtime behavior.

## Domain Follow-Ups

After the core eight steps, route any specialized surface instead of extending migration prose:

- Next.js: `references/19-nextjs-drop-in/01-overview-withmcpuse.md`
- Middleware and custom routes: `references/08-server-config/05-middleware.md`, `references/08-server-config/06-custom-routes.md`
- Proxy/gateway and OpenAPI: `references/17-advanced/01-proxy-and-gateway.md`, `references/17-advanced/03-openapi-fromopenapi.md`
- Subscriptions and notifications: `references/06-resources/06-subscriptions-listen.md`, `references/14-notifications/01-overview.md`
- Production and deploy: `references/24-production/04-security-hardening.md`, `references/25-deploy/02-pre-deploy-checklist.md`

---

**Next**: Go to `03-v1-to-v2-imports-server-and-tools.md` to start the migration, then return here for the exit gate.
