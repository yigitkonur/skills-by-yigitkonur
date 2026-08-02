# Error Catalog

*Read this when you have an exact symptom and need its grounded v2 cause, fix, and next reference.*

Use the exact error text when available. Do not apply v1 fixes such as restoring stdio, session stores, helper-based results, OAuth Proxy, or widget APIs.

## Startup and imports

| Symptom | Actual cause | Fix | Reference |
|---|---|---|---|
| `Cannot find module 'mcp-use/server'` | v2 removed the server subpath. | Import `MCPServer` from `mcp-use`. | `references/28-migration/03-v1-to-v2-imports-server-and-tools.md` |
| `ReferenceError: require is not defined` | v2 is ESM-only, but the entry file uses CommonJS. | Replace `require`/`module.exports` with `import`/`export`; set `"type": "module"`. | `references/02-setup/01-prerequisites.md` |
| Syntax or export errors while loading `mcp-use` | The process is running on an unsupported Node version or loading the ESM package as CommonJS. | Use Node 22 or newer and ESM configuration. | `references/02-setup/01-prerequisites.md` |
| Zod schema/type failures immediately after migration | The project still resolves Zod v3 or mixed Zod majors. | Install Zod v4 and remove duplicate v3 copies. | `references/04-tools/03-schemas-standard-schema-and-zod-v4.md` |
| `EADDRINUSE` | Another process owns the requested port. | Stop that process or select another `PORT`/`--port`. | `references/08-server-config/07-lifecycle-listen-fetch-shutdown.md` |
| Server starts locally but is unreachable from a container or platform | v2 defaults to `127.0.0.1`; the process is not bound to the platform interface, or the wrong port was selected. | Bind to `0.0.0.0` and honor `PORT`; verify host/port precedence. | `references/08-server-config/02-network-basepath-and-endpoints.md` |

## Connection and transport

| Symptom | Actual cause | Fix | Reference |
|---|---|---|---|
| Client cannot connect to a stdio command | v2 does not serve stdio. | Connect to the Streamable HTTP `/mcp` endpoint or add an external client-side bridge. | `references/09-transports/05-no-stdio-and-sse-history.md` |
| `404 Not Found` at `/sse` or `/stdio` | Those v1 transport routes are not v2 endpoints. | Use the configured `basePath`, `/mcp` by default. | `references/09-transports/02-streamable-http.md` |
| Client receives HTML instead of an MCP response | It reached `/`, a landing page, a proxy error page, or an auth redirect instead of the MCP endpoint. | Inspect status, `content-type`, and final URL; target `/mcp`. | `references/23-debug/02-transport-debugging.md` |
| Browser preflight fails | `cors` is absent or lacks the requesting origin, method, or headers. `allowedOrigins` alone does not emit CORS headers. | Configure v2 `cors.origin`, `cors.methods`, and `cors.allowedHeaders`. | `references/08-server-config/03-cors-and-allowed-origins.md` |
| Host validation rejects a local hostname | The `Host` value is outside the localhost defaults and `allowedHosts`. | Add the intended hostname to `allowedHosts`; do not put it in `allowedOrigins`. | `references/08-server-config/04-dns-rebinding-and-host-validation.md` |

## Tools and results

| Symptom | Actual cause | Fix | Reference |
|---|---|---|---|
| Tool appears in source but not in generated View typing | A static tool was not assigned to an exported module-level `ToolRef`. | Use `export const toolName = server.tool(...)`, then run `mcp-use typecheck`. | `references/04-tools/02-registering-a-tool.md` |
| Input validation fails before the callback runs | `inputSchema` rejected the arguments; the SDK validates before invocation. | Read the schema error, correct the caller or schema, and add field descriptions. | `references/04-tools/06-validation-pipeline.md` |
| Output validation fails after the callback | `structuredContent` does not match `outputSchema`, or a schema-backed success omitted it. | Return matching `structuredContent` or an `isError: true` envelope. | `references/04-tools/07-input-schema-vs-output-schema.md` |
| Client treats `"Error: ..."` as a normal response | The handler returned a text success instead of an MCP error result. | Return `{ isError: true, content: [...] }`. | `references/05-responses/05-error-handling.md` |
| Helper imports or helper-shaped code survive migration | `text()`, `object()`, `mix()`, `error()`, and `widget()` are deprecated compatibility helpers. | Return raw MCP envelopes. | `references/05-responses/07-deprecated-v1-helpers.md` |
| `ctx.auth.user.userId` is undefined | `userId` is the v1 path; built-in v2 provider users expose `id`. | Read `ctx.auth.user.id`. | `references/11-auth/03-ctx-auth-and-user-context.md` |
| `ctx.sample is not a function` | Server-side sampling was removed in v2. | Move generation to the model/client and keep the server tool deterministic. | `references/13-sampling/01-sampling-removed-in-v2.md` |

## OAuth

| Symptom | Actual cause | Fix | Reference |
|---|---|---|---|
| `401 Unauthorized` before the tool callback | The bearer token is missing, expired, has the wrong issuer/audience, or lacks required scopes. | Verify the Authorization header and provider resource, issuer, expiry, and scope settings. | `references/11-auth/06-debugging-checklist.md` |
| OAuth provider import cannot be resolved | Provider factories moved to `mcp-use/oauth/<provider>`. | Import the exact provider subpath. | `references/11-auth/01-overview.md` |
| Fixed-client OAuth flow cannot find `oauthProxy` | Native OAuth Proxy was removed in v2. | Use a DCR-capable provider or an external authorization server plus `oauthCustomProvider`. | `references/11-auth/07-oauth-proxy-removed.md` |
| Custom provider constructs but token verification or user mapping fails | `createTokenVerifier`, `oauthMetadata`, or `mapAuthInfo` is missing or inconsistent. | Implement all three and make metadata match the token issuer. | `references/11-auth/05-custom-provider-oauthcustomprovider.md` |
| Supabase tokens fail audience or signature validation | The configured project URL/ID, audience, or ES256-versus-HS256 mode does not match the token. | Use the correct project source; omit `jwtSecret` for JWKS/ES256 or provide it only for legacy HS256; verify audience. | `references/11-auth/providers/04-supabase.md` |

## Views and CSP

| Symptom | Actual cause | Fix | Reference |
|---|---|---|---|
| View tool type-checking requires `outputSchema` | v2 Views are schema-backed and consume `structuredContent`. | Add `outputSchema` and return a matching value. | `references/18-mcp-apps/server-surface/01-tool-view-field.md` |
| A View resource is not discovered | The folder/name contract is wrong: `views/<name>/view.tsx` must match `view.name`. | Rename the folder/file or tool binding to match exactly. | `references/18-mcp-apps/server-surface/02-register-views-and-folder-conventions.md` |
| `Cannot find module '@mcp-use/react'` | There is no separate React package. | Import hooks and components from `mcp-use/react`. | `references/18-mcp-apps/view-react/01-setup-and-providers.md` |
| `useWidget` or `useWidgetProps` is missing | Those are v1 widget hooks. | Use `useToolContext`; use `useViewState` for model-visible View state. | `references/28-migration/06-v1-to-v2-widgets-to-views.md` |
| View renders a loading state forever or reads undefined output | The component reads `toolOutput` before `useToolContext().status` is `ready`. | Branch on `pending`, `error`, and `ready` before reading output. | `references/18-mcp-apps/view-react/02-usetoolcontext.md` |
| Browser console reports `connect-src` violation | The external fetch/WebSocket origin is absent from `view.csp.connectDomains`. | Add the exact origin or `CSP_CONNECT_DOMAINS`. | `references/27-troubleshooting/05-csp-violations.md` |
| Browser console reports script/style/image/font violation | The external asset origin is absent from `view.csp.resourceDomains`. | Add the exact origin or `CSP_RESOURCE_DOMAINS`. | `references/27-troubleshooting/05-csp-violations.md` |
| View works in Inspector but not another host | The host does not advertise MCP Apps support or supports fewer capabilities/display modes. | Detect View support and degrade to the text fallback. | `references/18-mcp-apps/05-host-capability-detection.md` |

Use `references/27-troubleshooting/02-quick-diagnostic-table.md` for broad symptoms and `references/27-troubleshooting/06-decision-tree.md` when the failing layer is not yet known.