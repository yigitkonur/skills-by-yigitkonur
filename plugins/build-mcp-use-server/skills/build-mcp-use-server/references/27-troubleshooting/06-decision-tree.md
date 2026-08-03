# Decision Tree

*Read this when the failing layer is unknown and you need to route the problem without guessing.*

Follow the branches in order: **can't start → can't connect → tools fail → auth fails → views fail**.

## 1. Can't start

**Does the process reach a listening message or return from `server.listen()`?**

- **No — import error mentions `mcp-use/server`:** replace it with the `mcp-use` root import. Go to `references/26-anti-patterns/01-sdk-misuse.md`.
- **No — `require is not defined` or ESM syntax error:** migrate to ESM, set `"type": "module"`, and verify Node 22+. Go to `references/02-setup/01-prerequisites.md`.
- **No — Zod/type error:** confirm Zod v4 and remove mixed-major installs. Go to `references/26-anti-patterns/03-schemas.md`.
- **No — `EADDRINUSE`:** stop the port owner or choose another `PORT`/`--port`.
- **No — required env/config error:** correct the missing boundary value; do not add a fake fallback secret. Go to `references/24-production/01-env-config.md`.
- **Yes:** continue to **2. Can't connect**.

## 2. Can't connect

**Can an MCP client or Inspector reach the configured base path?**

- **No — client launches a command or expects stdio:** v2 has no stdio serving. Use the Streamable HTTP URL. Go to `references/09-transports/05-no-stdio-and-sse-history.md`.
- **No — 404 at `/sse`, `/stdio`, or `/`:** use the configured `basePath`, `/mcp` by default. Go to `references/09-transports/02-streamable-http.md`.
- **No — `406 Not Acceptable` requires JSON and event-stream:** the legacy POST is missing `Accept: application/json, text/event-stream`. Copy the verified request from `references/22-validate/02-curl-handshake.md`; do not change the body first.
- **No — connection refused locally:** verify process, host, and port.
- **No — works on the host but not from container/network:** bind to `0.0.0.0`, honor `PORT`, and inspect firewall/proxy routing. Go to `references/08-server-config/02-network-basepath-and-endpoints.md`.
- **No — browser preflight error:** configure `cors`; `allowedOrigins` alone is not CORS. Go to `references/08-server-config/03-cors-and-allowed-origins.md`.
- **No — 401 or OAuth discovery flow begins:** the transport is reachable; continue to **4. Auth fails**.
- **Yes:** continue to **3. Tools fail**.

## 3. Tools fail

**Does `tools/list` include the tool?**

- **No:** verify the tool is registered on the served `MCPServer` instance before startup and inspect its exact name. If View typing is the only missing surface, export it as a module-level const and run `mcp-use typecheck`. Go to `references/04-tools/02-registering-a-tool.md`.
- **Yes — call fails before callback:** input validation rejected the arguments. Read the schema error. Go to `references/04-tools/06-validation-pipeline.md`.
- **Yes — callback runs but output validation fails:** return `structuredContent` matching `outputSchema`, or an `isError: true` result. Go to `references/04-tools/07-input-schema-vs-output-schema.md`.
- **Yes — expected failure appears as success:** set `isError: true`. Go to `references/05-responses/05-error-handling.md`.
- **Yes — `ctx.sample` missing:** sampling was removed. Go to `references/13-sampling/01-sampling-removed-in-v2.md`.
- **Yes — `ctx.auth.user.userId` missing or request is 401:** continue to **4. Auth fails**.
- **Tool succeeds:** continue to **5. Views fail** only if the UI is broken.

## 4. Auth fails

**Does the request return 401 before callback execution?**

- **Yes — no bearer header:** complete the client OAuth flow or send the bearer token.
- **Yes — token present:** verify expiry, issuer, audience/resource, signature source, and required scopes. Go to `references/11-auth/06-debugging-checklist.md`.
- **No — callback runs but user ID is undefined:** use `ctx.auth.user.id`, not `userId`. Go to `references/11-auth/03-ctx-auth-and-user-context.md`.
- **Provider import fails:** use `mcp-use/oauth/<provider>`. Go to `references/11-auth/01-overview.md`.
- **OAuth Proxy import or fixed-client flow fails:** native OAuth Proxy was removed. Use DCR or an external broker plus `oauthCustomProvider`. Go to `references/11-auth/07-oauth-proxy-removed.md`.
- **Custom provider fails:** verify `createTokenVerifier`, `oauthMetadata`, and `mapAuthInfo` describe one consistent issuer/resource flow. Go to `references/11-auth/05-custom-provider-oauthcustomprovider.md`.
- **Supabase-specific signature/audience failure:** verify project source, audience, and ES256-versus-HS256 mode. Go to `references/11-auth/providers/04-supabase.md`.
- **Auth succeeds:** retry the tool, then continue to **5. Views fail** if needed.

## 5. Views fail

**Does the tool succeed with both `content` and schema-valid `structuredContent`?**

- **No:** fix the tool result first. Go to `references/18-mcp-apps/server-surface/01-tool-view-field.md`.
- **Yes — no View resource:** match `view.name` to `views/<name>/view.tsx`; remove v1 widget registration. Go to `references/18-mcp-apps/server-surface/02-register-views-and-folder-conventions.md`.
- **Yes — React import fails:** import from `mcp-use/react`, not `@mcp-use/react`.
- **Yes — `useWidget` missing:** migrate to `useToolContext` and `useViewState`. Go to `references/28-migration/06-v1-to-v2-widgets-to-views.md`.
- **Yes — loading forever or undefined output:** branch on `useToolContext().status` before reading `toolOutput`. Go to `references/18-mcp-apps/view-react/02-usetoolcontext.md`.
- **Yes — blank with CSP console errors:** map the blocked directive to the narrow `view.csp` field. Go to `references/27-troubleshooting/05-csp-violations.md`.
- **Yes — works in Inspector but not target host:** check MCP Apps support and host capabilities; retain a text fallback. Go to `references/18-mcp-apps/05-host-capability-detection.md`.
- **Yes — works in dev but not deployment:** verify `.mcp-use/build/`, `MCP_URL`, `MCP_ASSETS_URL`, and production CSP. Go to `references/18-mcp-apps/server-surface/04-assets-mcp-url-and-serving.md`.

If no branch matches, search `references/27-troubleshooting/01-error-catalog.md` for the exact error. Then reproduce with the Inspector, request logs, and a curl handshake in that order using `references/23-debug/01-debugging-workflow.md`.