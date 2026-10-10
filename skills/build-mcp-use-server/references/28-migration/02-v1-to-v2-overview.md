# v1 → v2 Migration Overview & Master Delta Guide

*Read this first if upgrading an mcp-use v1 server to v2, or migrating external SDKs, widgets, REST APIs, or interactive flows.*

The transition from `mcp-use v1.34.5` to `v2.8.2` represents an architectural paradigm shift: the framework evolves from a session-affine, semi-stateful, helper-heavy wrapper into a lean, strictly stateless, definition-first MCP engine serving Streamable HTTP.

This guide provides the master index and delta map across all **5 core migration vectors**, complete with breaking change tables, silent failure traps, and an authoritative migration exit gate.

---

## At a Glance: The 5 Migration Vectors

The migration suite is organized into 10 modular reference documents covering 5 primary upstream vectors:

| Vector | Upstream Source System | Canonical v2 Destination | Primary Reference Guides |
|---|---|---|---|
| **Vector 1** | `mcp-use v1.x` Server Core | `mcp-use v2.8+` Stateless Streamable HTTP | `02-v1-to-v2-overview.md`<br>`03-v1-to-v2-imports-server-and-tools.md`<br>`04-v1-to-v2-responses-and-helpers.md`<br>`05-v1-to-v2-auth.md`<br>`07-v1-to-v2-sessions-transports-stdio-sse.md` |
| **Vector 2** | Raw `@modelcontextprotocol/sdk` | Definition-First `MCPServer` & `server.tool` | `01-from-modelcontextprotocol-sdk.md` |
| **Vector 3** | Legacy ChatGPT Widgets & Skybridge | MCP Apps Views & `@openai/apps-sdk-ui` | `06-v1-to-v2-widgets-to-views.md`<br>`08-appssdk-to-mcp-apps.md` |
| **Vector 4** | REST Endpoints & OpenAPI 3.x Specs | `MCPServer.fromOpenAPI()` & Curated Tools | `09-openapi-and-rest-to-tools.md` |
| **Vector 5** | Interactive Elicitation (`ctx.elicit`) & Sampling | `inputRequired` & `createRequestStateCodec` | `10-elicitation-and-state-evolution.md` |

---

## Master Delta Table

| Feature / Subsystem | Legacy v1.34.5 / Upstream | Canonical v2.8.2 | Migration Guide |
|---|---|---|---|
| **Root Package Import** | `mcp-use/server` | `mcp-use` (root export) | `03-v1-to-v2-imports-server-and-tools.md` |
| **Node.js Engine** | `^20.19.0 \|\| >=22.12.0`, CJS/ESM | `>=22.22.2`, strictly ESM (`"type": "module"`) | `03-v1-to-v2-imports-server-and-tools.md` |
| **Tool Registration** | `schema` + `cb` property | `inputSchema` + `outputSchema` + callback 2nd arg | `03-v1-to-v2-imports-server-and-tools.md` |
| **Tool Static Exports** | Optional | **Required** as `ToolRef` for View typechecking | `03-v1-to-v2-imports-server-and-tools.md` |
| **Schema Validation** | Zod v3 (`zod@^3.22.0`) | Standard Schema compliant (Zod v4 / `zod@^4.0.0-alpha`) | `03-v1-to-v2-imports-server-and-tools.md` |
| **Response Envelopes** | Helper functions (`text()`, `object()`, `widget()`) | Deprecated shims; raw `CallToolResult` envelope | `04-v1-to-v2-responses-and-helpers.md` |
| **Multi-Block Returns** | `mix(text(), object())` helper | Array of `ContentBlock` objects in `content: [...]` | `04-v1-to-v2-responses-and-helpers.md` |
| **Auth Provider Imports**| `import { ... } from "mcp-use/server"` | Modular subpaths: `mcp-use/oauth/*` | `05-v1-to-v2-auth.md` |
| **Public Tool Discovery**| Single-mode auth; 401 on `tools/list` | `mixedAuth: true` on `MCPServer` | `05-v1-to-v2-auth.md` |
| **Tool Access Gating** | None (all-or-nothing server auth) | Tool `securitySchemes: [{ type: "noauth" }]` / `[{ type: "oauth2" }]` | `05-v1-to-v2-auth.md` |
| **User Identity** | `ctx.auth.user.userId` | `ctx.auth.user.id` (normalized across providers) | `05-v1-to-v2-auth.md` |
| **OAuth Proxy** | Built-in `oauthProxy()` | **Removed**; deploy external broker + `oauthCustomProvider` | `05-v1-to-v2-auth.md` |
| **Context Lifecycle** | Session-affine, stateful (`ctx.session`) | Stateless per-request (`ctx`) | `07-v1-to-v2-sessions-transports-stdio-sse.md` |
| **Session Stores** | `InMemory`, `RedisSessionStore`, `sessionStore` | **Removed**; external DB keyed by `ctx.auth.user.id` | `07-v1-to-v2-sessions-transports-stdio-sse.md` |
| **HTTP Transport** | Implicit SSE / Express adapters | Stateless Streamable HTTP (`basePath: "/mcp"`) | `07-v1-to-v2-sessions-transports-stdio-sse.md` |
| **Stdio Serving** | `server.listen({ stdio: true })` | **Removed**; Streamable HTTP only | `07-v1-to-v2-sessions-transports-stdio-sse.md` |
| **Express/Connect** | `server.listen({ express, router })` | **Removed**; use Hono (`server.app`) or `server.fetch` | `07-v1-to-v2-sessions-transports-stdio-sse.md` |
| **Notifications** | `sendToolsChanged()`, `sendNotificationToSession` | `notifyToolsChanged()`; active request only | `07-v1-to-v2-sessions-transports-stdio-sse.md` |
| **Widget Directory** | `resources/<name>/widget.tsx` | `views/<name>/view.tsx` | `06-v1-to-v2-widgets-to-views.md` |
| **Widget Binding** | `widget: { name }` on tool | `view: { name }` on tool | `06-v1-to-v2-widgets-to-views.md` |
| **View React Hooks** | `useWidget()`, `useWidgetState()` | `useToolContext<Name>()`, `useViewState()`, `useCallTool()` | `06-v1-to-v2-widgets-to-views.md` |
| **View Styling & UI** | Ad-hoc CSS, `McpUseProvider` | `@openai/apps-sdk-ui`, Tailwind 4, `<AppsSDKUIProvider>` | `08-appssdk-to-mcp-apps.md` |
| **Theme Sync** | Manual CSS / broken dark mode | `applyDocumentTheme(theme)` with `[data-theme]` | `08-appssdk-to-mcp-apps.md` |
| **Launch Entrypoints** | `_meta["openai/fileParams"]` | Typed `entrypoints: [{ type: "file", extensions: [...] }]` | `08-appssdk-to-mcp-apps.md` |
| **Evidence Ingestion** | Custom chat message via `sendFollowUpMessage` | `useModelContext().add("key", { type: "text" \| "image" })` | `08-appssdk-to-mcp-apps.md` |
| **Raw SDK Tool Setup** | `setRequestHandler(ListTools/CallTool)` | Declarative `server.tool({ inputSchema, outputSchema })` | `01-from-modelcontextprotocol-sdk.md` |
| **OpenAPI Wrapping** | Manual ad-hoc fetch scripts | `MCPServer.fromOpenAPI()` or curated `server.tool` forwarding | `09-openapi-and-rest-to-tools.md` |
| **Elicitation API** | Deprecated `ctx.elicit()` (removed v2.4.3) | `inputRequired`, `inputResponse`, `acceptedContent` | `10-elicitation-and-state-evolution.md` |
| **Multi-Round State** | In-memory `Map`, session variables | HMAC-signed `createRequestStateCodec` in `requestState` | `10-elicitation-and-state-evolution.md` |
| **Server-Side Sampling**| `ctx.sample()` | **Removed**; client LLM generates; server provides tools | `10-elicitation-and-state-evolution.md` |

---

## What is Removed Entirely

The following features have no direct equivalent and must be re-architected:

| Feature / Primitive | v1 / Legacy Status | v2 Status | Replacement Architecture |
|---|---|---|---|
| `mcp-use/server` import | Subpath export | ✗ Deleted | Import `MCPServer` directly from `mcp-use` root |
| `Logger` root API | Exported class | ✗ Deleted | Use standard logging (`pino`, `console`) for server sinks; `ctx.sendLog()` for client MCP logging |
| `ctx.elicit()` | Experimental method | ✗ Deleted (v2.4.3) | Return `inputRequired()` envelope and validate with `acceptedContent()` |
| `ctx.sample()` | Server LLM sampling | ✗ Deleted | Host LLM handles generation; server provides deterministic tools |
| `oauthProxy()` | Non-DCR proxy | ✗ Deleted | Deploy external authorization server (Keycloak, Auth0) + `oauthCustomProvider` |
| Session Stores (`RedisSessionStore`, etc.) | Transport state | ✗ Deleted | Application-owned database keyed by `ctx.auth.user.id` or explicit trace tokens |
| Stdio Serving (`stdio: true`) | CLI transport | ✗ Deleted | Streamable HTTP (`server.listen(port)`) |
| Express/Connect adapters | Web framework bridge | ✗ Deleted | Use Hono (`server.app`) or `server.fetch` |
| `window.openai.*` | Injected globals | ✗ Deprecated | Use `mcp-use/react` hooks (`useToolContext`, `useViewState`, `useCallTool`) |
| `text/html+skybridge` MIME | Legacy widget MIME | ✗ Replaced | Framework automatically serves `text/html;profile=mcp-app` |

---

## Complete 10-Guide Migration Roadmap

Follow the sequenced roadmap below based on your codebase requirements:

1. **Raw SDK Migration** (`01-from-modelcontextprotocol-sdk.md`): Convert manual JSON-RPC dispatch, `Server.setRequestHandler`, and stdio to declarative `server.tool()`, `server.resourceTemplate()`, and Streamable HTTP.
2. **Master Overview & Delta Table** (`02-v1-to-v2-overview.md`): Review breaking changes, master checklist, and the migration exit gate.
3. **Imports, Server & Tools** (`03-v1-to-v2-imports-server-and-tools.md`): Update root imports, Node.js `>= 22.22.2`, ESM configuration, Standard Schema (Zod v4), and export `ToolRef` for all static tools.
4. **Responses & Envelopes** (`04-v1-to-v2-responses-and-helpers.md`): Replace deprecated helpers (`text()`, `object()`) with raw spec-compliant `CallToolResult` envelopes.
5. **Authentication & Mixed Auth** (`05-v1-to-v2-auth.md`): Move provider imports to `mcp-use/oauth/*`, enable `mixedAuth: true`, configure tool `securitySchemes`, update `ctx.auth.user.id`, and remove `oauthProxy`.
6. **Widgets to Views** (`06-v1-to-v2-widgets-to-views.md`): Reorganize `resources/widget.tsx` to `views/<name>/view.tsx`, update view hooks, split ephemeral vs model-visible state, and handle cached ChatGPT URIs.
7. **Stateless Transports & Stdio** (`07-v1-to-v2-sessions-transports-stdio-sse.md`): Eliminate session stores and post-response push; adopt stateless Streamable HTTP serving.
8. **ChatGPT Widgets to Apps SDK UI** (`08-appssdk-to-mcp-apps.md`): Convert `window.openai` to `mcp-use/react`, apply `@openai/apps-sdk-ui` components, configure Tailwind 4 `@source` directives, synchronize dark mode, and set up typed file entrypoints.
9. **REST APIs & OpenAPI Specifications** (`09-openapi-and-rest-to-tools.md`): Bootstrap tools via `MCPServer.fromOpenAPI()` or curate production tools with dynamic token pass-through and payload pruning.
10. **Interactive Elicitation & State Evolution** (`10-elicitation-and-state-evolution.md`): Replace removed `ctx.elicit()` and `ctx.sample()` with `inputRequired`, validate with `acceptedContent()`, and manage multi-turn state via HMAC-signed `createRequestStateCodec`.

---

## Checklist: Silent Runtime Traps

⚠️ The following patterns may compile cleanly in TypeScript or bypass naive text substitutions, but will fail catastrophically at runtime:

- **Missing `mixedAuth: true`**: Public tools fail with 401 Unauthorized during client discovery because the server defaults to single-mode protection.
- **Accessing `ctx.auth.user.userId`**: Evaluates silently to `undefined` because v2 normalized user identity under `ctx.auth.user.id`.
- **Calling Removed `ctx.elicit()`**: Throws `TypeError: ctx.elicit is not a function` because the method was deleted in v2.4.3 (#2409).
- **Passing a Primitive to `useViewState()`**: Calling `useViewState(true)` or `useViewState("step1")` crashes in the host; the root state **must be a JSON object**.
- **Missing Tailwind 4 `@source`**: Apps SDK UI components render completely unstyled because Tailwind 4 does not scan `node_modules` by default.
- **Failing to Export `ToolRef`**: Writing `const myTool = server.tool(...)` without `export` breaks View typechecking in `mcp-env.d.ts`.
- **Chaining `server.tool().tool()`**: `server.tool()` returns a `ToolRef`, not `this`; method chaining throws a runtime type error.
- **Using Short Secrets with `createRequestStateCodec`**: Secrets shorter than 32 bytes throw a runtime `RangeError: Key must be at least 32 bytes`.

---

## Migration Exit Gate

Never declare a migration complete based solely on text substitutions. Execute the 7-rung validation protocol before deploying:

1. **Classify Installed Packages**:
   Run `bash scripts/check-mcp-use-version.sh`. Confirm `mcp-use` is `^2.8.2` (npm `latest`), has no `./server` export, and the CLI is `4.x`.
2. **Scan for Removed Patterns**:
   Run a codebase scan for forbidden patterns:
   ```bash
   grep -rnE 'mcp-use/server|ctx\.sample|ctx\.elicit|ctx\.session|sessionStore|streamManager|stateless|baseUrl|allowMethods|allowHeaders|exposeHeaders|getActiveSessions|getServerForSession|registerCapabilities|Logger\.get|widget:|useWidget|window\.openai' src/ index.ts views/
   ```
   Every remaining match must be an intentional migration fixture or comment, never active code.
3. **Static Proof**:
   Run `npx mcp-use typecheck` independently from `mcp-use build`. Confirm all tools export `ToolRef` and generate valid `mcp-env.d.ts` types.
4. **Protocol Probe**:
   Start the server (`npm run dev`) and probe the Streamable HTTP endpoint:
   ```bash
   curl -i -X POST http://localhost:3000/mcp \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
   ```
   Confirm valid JSON-RPC 2.0 response with registered tool schemas.
5. **Auth Proof (When Applicable)**:
   Verify that unauthenticated `tools/list` succeeds under `mixedAuth: true`, an unauthenticated call to a protected tool returns HTTP 401, and an authenticated call with a valid Bearer token succeeds.
6. **View Proof (When Applicable)**:
   Open the Inspector (`http://localhost:3000/mcp/inspector`), trigger the tool, and confirm the View renders with correct `@openai/apps-sdk-ui` styling, dark mode adapts to `[data-theme]`, and CSP console checks are clean.
7. **Production Deployment Proof**:
   Verify deployment on target environment (Node >= 22.22.2, Cloudflare Workers, or Next.js), ensuring environment variables (`MCP_URL`, `REQUEST_STATE_SECRET`) are configured.

---

## Next Steps

Begin your implementation with `03-v1-to-v2-imports-server-and-tools.md` for core server migration, or jump directly to the relevant vector guide above.
