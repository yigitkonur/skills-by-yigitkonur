# Symptom Index

*Entry point when the user brings an error or misbehavior rather than a feature request. Match the symptom family, open the entry file, then follow its pointers. For symptom-by-symptom first checks, `references/27-troubleshooting/02-quick-diagnostic-table.md` is the finer-grained companion.*

## Install, imports, startup

| Symptom | Entry |
|---|---|
| `Cannot find module 'mcp-use/server'` or `MCPServer` import fails | `references/26-anti-patterns/01-sdk-misuse.md` — v2 imports from `mcp-use` root; a `/server` import means v1 code → `references/28-migration/02-v1-to-v2-overview.md` |
| `require is not defined` / CJS build errors | `references/02-setup/01-prerequisites.md` — v2 is ESM-only, Node >= 22.22.2 |
| Zod version conflicts, `_zod` type errors | `references/26-anti-patterns/03-schemas.md` — v2 requires zod v4 / Standard Schema |
| Server exits before listening, port/env errors | `references/08-server-config/07-lifecycle-listen-fetch-shutdown.md` |
| Installed `mcp-use` but APIs in this skill are missing | `references/00-version-drift.md` — ensure `mcp-use` >= 2.8.2 on npm `latest` (v1 is `v1-legacy`) |

## Connection and transport

| Symptom | Entry |
|---|---|
| Client expects a stdio command / 404 at `/sse` | `references/09-transports/05-no-stdio-and-sse-history.md` |
| 404 / HTML at the MCP endpoint | `references/09-transports/02-streamable-http.md` — default route is `/mcp`; verify with the curl probes in `references/22-validate/02-curl-handshake.md` |
| `406 Not Acceptable: Client must accept both application/json and text/event-stream` | `references/09-transports/02-streamable-http.md` — this is the legacy compatibility wire; add `Accept: application/json, text/event-stream` or use the native modern `2026-07-28` request shape |
| Expected GET/SSE stream or DELETE teardown but received `204 No Content` | `references/09-transports/02-streamable-http.md` — GET/HEAD/DELETE are compatibility probes in stateless v2, not sessions or resource reads |
| Browser reports missing CORS headers or preflight fails | `references/08-server-config/03-cors-and-allowed-origins.md` — CORS is off unless `cors` is configured; `allowedOrigins` is a separate rejection control |
| `403` with forged/unexpected `Host`, especially on localhost or `server.fetch()` with `allowedHosts` | `references/08-server-config/04-dns-rebinding-and-host-validation.md` — Host validation differs from Origin validation and CORS |
| `MCP_URL` remains localhost after `mcp-use dev --tunnel`, or code cannot find the public URL | `references/03-cli/10-environment-variables.md` — the tunnel URL is printed separately and never written to `MCP_URL`; then read `references/21-tunneling/01-overview.md` |
| Works locally, dead in container/cloud | `references/08-server-config/02-network-basepath-and-endpoints.md` then `references/25-deploy/01-decision-matrix.md` |

## Tools, schemas, results

| Symptom | Entry |
|---|---|
| Tool missing from `tools/list` | `references/04-tools/02-registering-a-tool.md` |
| Call rejected before the callback runs | `references/04-tools/06-validation-pipeline.md` |
| Output/structuredContent validation failure | `references/04-tools/07-input-schema-vs-output-schema.md` |
| v1 helpers (`text()`, `object()`, `widget()`) flagged deprecated | `references/05-responses/07-deprecated-v1-helpers.md` |
| Client shows raw JSON instead of readable output | `references/05-responses/01-overview-decision-table.md` |

## Auth

| Symptom | Entry |
|---|---|
| 401 before the tool callback | `references/27-troubleshooting/03-oauth-issues.md` |
| `ctx.auth.user.userId` undefined | `references/11-auth/03-ctx-auth-and-user-context.md` — v2 uses `user.id` |
| `oauthProxy` import missing | `references/11-auth/07-oauth-proxy-removed.md` |
| OAuth discovery metadata unexpectedly returns 401 or was placed behind bearer auth | `references/11-auth/02-attaching-a-provider.md` — discovery metadata is public; only the exact MCP `basePath` is bearer-gated |
| Provider setup fails (clerk/auth0/workos/supabase/keycloak/better-auth) | the matching file under `references/11-auth/providers/` + `references/11-auth/06-debugging-checklist.md` |

## Views / MCP Apps / ChatGPT

| Symptom | Entry |
|---|---|
| View not discovered; folder is deeper than `views/<name>/view.tsx` | `references/18-mcp-apps/server-surface/02-register-views-and-folder-conventions.md` — discovery is one directory deep, not recursive |
| View is discovered but blank or fails at runtime | `references/27-troubleshooting/04-view-rendering-issues.md`, then `references/23-debug/03-view-debugging.md` |
| `/mcp/inspector` or `/api/mcp/inspector` is 404 / Inspector did not auto-mount | `references/20-inspector/01-overview.md` and `references/19-nextjs-drop-in/02-route-and-file-placement.md` — auto-mount exists only on `mcp-use dev` and `mcp-use start --with-inspector`, not direct `listen()`/`fetch()` or embedded Next.js |
| Model/host cannot highlight, filter, or otherwise act on the mounted View | `references/18-mcp-apps/view-react/09-useviewtool.md` — register an ephemeral View-local tool with `useViewTool`; `useCallTool` is the opposite direction |
| CSP violations in the iframe console | `references/27-troubleshooting/05-csp-violations.md` |
| `useWidget` / `McpUseProvider` / `@mcp-use/react` not found | `references/28-migration/06-v1-to-v2-widgets-to-views.md` — v2 hooks live in `mcp-use/react` |
| View renders in Inspector but not in the host | `references/18-mcp-apps/05-host-capability-detection.md` |
| ChatGPT-specific rendering differences | `references/18-mcp-apps/chatgpt-apps/01-dual-protocol.md` and `references/20-inspector/08-debugging-chatgpt-apps.md` |

## Advanced protocol

| Symptom | Entry |
|---|---|
| `ctx.sample is not a function` | `references/13-sampling/01-sampling-removed-in-v2.md` |
| `ctx.elicit is not a function` or TypeScript says `RequestContext` has no `elicit` | `references/12-elicitation/01-overview.md` — upstream docs describe it, but v2 ships `inputRequired()` / `inputResponse()` / `acceptedContent()` instead |
| `createRequestStateCodec({ secret })`, `requestState: codec.verify`, or `ctx.requestState.parse()` fails | `references/12-elicitation/04-multi-round-and-request-state.md` — use `{ key, ttlSeconds }`, configure `requestState: { verify }`, mint with `.mint()`, and read with `ctx.requestState<T>()` |
| `resources/subscribe` or `resources/unsubscribe` returns `-32601 Method Not Found` | `references/06-resources/06-subscriptions-listen.md` — v2 uses `subscriptions/listen` with exact URIs in `resourceSubscriptions`; the capability bit does not wire the legacy methods |
| Elicitation never returns / handler re-runs unexpectedly | `references/12-elicitation/01-overview.md` — v2 re-entry model |
| Notifications not reaching the client | `references/14-notifications/01-overview.md` — stateless delivery limits |
| Session state disappears between calls | `references/10-sessions/01-overview-stateless-truth.md` |

## CLI, build, deploy

| Symptom | Entry |
|---|---|
| `mcp-use: command not found` or unknown command (`serve`, `generate-types`) | `references/03-cli/01-overview.md` |
| `mcp-use build` succeeds but TypeScript errors remain | `references/03-cli/04-mcp-use-build-and-typecheck.md` — build is transpile-only; run `mcp-use typecheck` separately |
| Stale output in production | `references/03-cli/04-mcp-use-build-and-typecheck.md` — artifact is `.mcp-use/build/` |
| Deploy fails or 80 MB limit | `references/03-cli/06-mcp-use-deploy-and-cloud.md` |
| Platform-specific runtime errors | `references/25-deploy/platforms/10-runtime-patterns.md` then the platform file |

## Migration and upgrade (v1→v2, Raw SDK, Widgets, OpenAPI, Elicitation)

| Symptom / Error Message | Migration Vector | Root Cause & Diagnostic | Actionable Remedy & Guide |
|---|---|---|---|
| `Cannot find module 'mcp-use/server'` or `MCPServer` import fails | Vector 1 (v1→v2) | v1 legacy subpath import removed in v2. | Change to `import { MCPServer } from "mcp-use"` (root export). → `references/28-migration/03-v1-to-v2-imports-server-and-tools.md` |
| `require is not defined in ES module scope` / CJS build errors | Vector 1 (v1→v2) | v2 enforces Node >= 22.22.2 and pure ESM. CommonJS `require()` fails. | Add `"type": "module"` to `package.json`, set `"moduleResolution": "NodeNext"` in `tsconfig.json`. → `references/28-migration/02-v1-to-v2-overview.md` & `references/02-setup/01-prerequisites.md` |
| `TypeError: ctx.text is not a function` or `text is not defined` / `object is not defined` | Vector 1 (v1→v2) | v1 response helper functions (`text()`, `object()`, `widget()`) deprecated/removed in v2. | Return raw `CallToolResult` envelope: `{ content: [{ type: "text", text: "..." }], structuredContent?: ... }`. → `references/28-migration/04-v1-to-v2-responses-and-helpers.md` |
| `Property 'userId' does not exist on type 'User'` | Vector 1 (v1→v2) | `ctx.auth.user.userId` was renamed to `user.id` in v2. | Replace `.userId` with `.id` across all tool callbacks. → `references/28-migration/05-v1-to-v2-auth.md` |
| `Schema must conform to Standard Schema specification` / `~standard` missing | Vector 1 (v1→v2) | Zod v3 (`zod@^3.22.0`) does not implement `~standard` schema contract required by v2. | Upgrade to `zod@^4.0.0-alpha` or any Standard Schema v1 validator. → `references/28-migration/03-v1-to-v2-imports-server-and-tools.md` & `references/26-anti-patterns/03-schemas.md` |
| `tools/list` returns 401 or public discovery requires authentication | Vector 1 (v1→v2) | Default OAuth provider blocks all requests before tool discovery. | Configure `mixedAuth: true` on `MCPServer` and set `securitySchemes: [{ type: "noauth" }]` on public tools. → `references/28-migration/05-v1-to-v2-auth.md` |
| `oauthProxy is not exported from 'mcp-use/oauth'` | Vector 1 (v1→v2) | `oauthProxy()` was removed in v2. | Migrate to direct provider adapters (`mcp-use/oauth/*`) or use `oauthCustomProvider` with `createTokenVerifier`. → `references/28-migration/05-v1-to-v2-auth.md` & `references/11-auth/07-oauth-proxy-removed.md` |
| `ctx.session is undefined` / session state lost between HTTP turns | Vector 1 (v1→v2) | `sessionStore` (in-memory/Redis) removed in v2; Streamable HTTP is stateless per turn. | Migrate session data to external databases or signed `ctx.requestState`. → `references/28-migration/07-v1-to-v2-sessions-transports-stdio-sse.md` |
| `TypeError: server.setRequestHandler is not a function` | Vector 2 (Raw SDK→v2) | Attempting to call low-level `@modelcontextprotocol/sdk` method on `MCPServer` instance. | Replace imperative handlers (`ListToolsRequestSchema`, `CallToolRequestSchema`) with declarative `server.tool()`, `server.resourceTemplate()`, and `server.prompt()`. → `references/28-migration/01-from-modelcontextprotocol-sdk.md` |
| `StdioServerTransport is not supported` / Client expects stdio command | Vector 2 (Raw SDK→v2) | `mcp-use v2` serves exclusively via Streamable HTTP; stdio removed. | Connect client over HTTP (`http://localhost:3000/mcp`) or use an HTTP-to-stdio bridge. → `references/28-migration/01-from-modelcontextprotocol-sdk.md` & `references/09-transports/05-no-stdio-and-sse-history.md` |
| `McpError: Method not found (-32601) on tools/call` / Missing static ToolRef export | Vector 2 (Raw SDK→v2) | Tool registered but unexported or name mismatched in TypeScript compilation. | Ensure `export const myTool = server.tool(...)` is exported statically for type generation. → `references/28-migration/01-from-modelcontextprotocol-sdk.md` & `references/28-migration/03-v1-to-v2-imports-server-and-tools.md` |
| `McpError vs CallToolResult` / manual JSON-RPC error code throwing | Vector 2 (Raw SDK→v2) | Throwing raw `new McpError(ErrorCode.InvalidParams, ...)` inside tools. | Return `{ isError: true, content: [{ type: "text", text: "..." }] }` for expected errors; throw standard `Error` for crashes. → `references/28-migration/01-from-modelcontextprotocol-sdk.md` & `references/28-migration/04-v1-to-v2-responses-and-helpers.md` |
| `ReferenceError: window.openai is not defined` | Vector 3 (Widgets→MCP Apps) | Direct access to legacy ChatGPT widget global in an MCP Apps host or Inspector. | Replace `window.openai.*` with `useToolContext()`, `useViewState()`, and `useCallTool()` from `mcp-use/react`. → `references/28-migration/08-appssdk-to-mcp-apps.md` |
| `Failed to load resource: unsupported MIME text/html+skybridge` or `application/vnd.openai.chatgpt-app+html` | Vector 3 (Widgets→MCP Apps) | Legacy ChatGPT widget MIME type used instead of standard MCP Apps view. | Delete manual HTML resource registration; place view at `views/<name>/view.tsx` with `view: { name: "<name>" }` on tool. Framework generates `text/html;profile=mcp-app`. → `references/28-migration/08-appssdk-to-mcp-apps.md` & `references/28-migration/06-v1-to-v2-widgets-to-views.md` |
| `@openai/apps-sdk-ui components render unstyled / raw` | Vector 3 (Widgets→MCP Apps) | Tailwind 4 compiler did not scan `@openai/apps-sdk-ui` node_modules package. | Add `@source "../node_modules/@openai/apps-sdk-ui";` and `@import "@openai/apps-sdk-ui/css";` in view stylesheet. → `references/28-migration/08-appssdk-to-mcp-apps.md` & `references/chatgpt-apps-ui.md` |
| `View dark mode does not update with ChatGPT theme` | Vector 3 (Widgets→MCP Apps) | Missing theme synchronization between `mcp-use/react` and Apps SDK UI `[data-theme]`. | In view root, read `useViewTheme()` and call `applyDocumentTheme(theme)` in a `useEffect`. → `references/28-migration/08-appssdk-to-mcp-apps.md` & `references/chatgpt-apps-ui.md` |
| `Cannot find module '@mcp-use/react'` | Vector 3 (Widgets→MCP Apps) | Non-existent scoped package name hallucinated by LLM or legacy migration. | Change import to `mcp-use/react` (subpath of root `mcp-use` package). → `references/28-migration/06-v1-to-v2-widgets-to-views.md` |
| `Launch entrypoint not appearing for file uploads` / `openai/fileParams` deprecation | Vector 3 (Widgets→MCP Apps) | Using legacy `_meta["openai/fileParams"]` instead of typed view entrypoints. | Declare `view.entrypoints: [{ type: "file", extensions: [...] }]` on tool definition. → `references/28-migration/08-appssdk-to-mcp-apps.md` & `references/chatgpt-extensions.md` |
| `fromOpenAPI failed: Cannot resolve remote $ref in spec` | Vector 4 (REST/OpenAPI) | `MCPServer.fromOpenAPI()` does not bundle remote `$ref` URIs at runtime. | Pre-bundle or dereference the OpenAPI specification before passing to `fromOpenAPI({ spec })`. → `references/28-migration/09-openapi-and-rest-to-tools.md` & `references/17-advanced/03-openapi-fromopenapi.md` |
| `Downstream REST API returns 401 Unauthorized` | Vector 4 (REST/OpenAPI) | Hardcoded token missing or failure to pass caller bearer token to upstream REST service. | Extract caller token via `ctx.auth?.token` and pass in upstream `headers: { Authorization: \`Bearer \${ctx.auth.token}\` }`. → `references/28-migration/09-openapi-and-rest-to-tools.md` |
| `TypeError: ctx.elicit is not a function` | Vector 5 (Elicitation) | `ctx.elicit()` was removed in v2.4.3 (#2409). `RequestContext` has no `elicit`. | Return `inputRequired({ inputRequests: { key: inputRequired.elicit(...) } })` and read with `inputResponse()` / `acceptedContent()`. → `references/28-migration/10-elicitation-and-state-evolution.md` & `references/12-elicitation/01-overview.md` |
| `TypeError: ctx.sample is not a function` | Vector 5 (Elicitation) | Server-side LLM sampling removed in v2. | Eliminate server sampling; provide deterministic tool outputs and guide host model via prompts or `<ModelContext>`. → `references/28-migration/10-elicitation-and-state-evolution.md` & `references/13-sampling/01-sampling-removed-in-v2.md` |
| `Infinite elicitation loop (tool re-prompts continuously)` | Vector 5 (Elicitation) | Handler does not inspect `ctx.inputResponses` or `acceptedContent()` on re-entry. | On re-entry, inspect `inputResponse(ctx.inputResponses, key)` and only return `inputRequired` if content is missing/undefined. → `references/28-migration/10-elicitation-and-state-evolution.md` & `references/12-elicitation/04-multi-round-and-request-state.md` |
| `ctx.requestState returns string instead of parsed object` | Vector 5 (Elicitation) | Server missing `requestState: { verify: codec.verify }` configuration. | Pass `{ requestState: { verify: codec.verify } }` to `new MCPServer(...)`. → `references/28-migration/10-elicitation-and-state-evolution.md` & `references/12-elicitation/04-multi-round-and-request-state.md` |
| `RequestState verification failed: signature mismatch or TTL expired` | Vector 5 (Elicitation) | Attacker tampered with wire token, or user waited longer than `ttlSeconds`. | Catch verification error at boundary; return `{ isError: true, content: [{ type: "text", text: "Session expired or state invalid" }] }`. → `references/28-migration/10-elicitation-and-state-evolution.md` & `references/12-elicitation/04-multi-round-and-request-state.md` |

Still ambiguous after the entry file? Walk `references/27-troubleshooting/06-decision-tree.md` top to bottom.
