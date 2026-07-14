# Error Catalog

The greppable error → cause → fix matrix. One row per known error message. Other clusters link to specific rows here.

---

## 1. Build, types, imports

| Error | Cause | Fix |
|---|---|---|
| `Cannot find module 'mcp-use/server'` | `tsconfig.json` missing `"moduleResolution": "node16"` (or `"bundler"`). | Set `module` and `moduleResolution` to `node16`; rebuild with `npx tsc --build`. |
| TypeScript errors on `mcp-use` import paths | Wrong `moduleResolution`, mismatched `@types/node`, importing from raw SDK. | Import from `mcp-use/server`. Set `module: node16`, `moduleResolution: node16`, `target: ES2022`. Match `@types/node` to your Node major. |
| `Unexpected token` parsing server output | `package.json` has `"type": "module"` but entry uses `require()`, or vice versa. | Pick one. ESM: `import`/`export`, `.js` extensions. CJS: drop `"type": "module"`. |
| `Maximum call stack size exceeded` from `JSON.stringify()` | Circular references in ORM models. | Map to plain DTOs. Use `safe-stable-stringify`. |
| Duplicate Zod type errors / OOM during `mcp-use build` (v1.21.5+) | Two Zod copies in tree. | `npm install zod@^4.0.0` explicitly; `rm -rf node_modules && npm install`. Zod is a `peerDependency` since v1.21.5. |
| `e.custom is not a function` (TypeError) | Zod v3/v4 conflict from esm.sh imports on Deno. | Switch `deno.json` to `npm:` specifiers. See `25-deploy/platforms/02-supabase.md`. |
| `ERR_UNSUPPORTED_ESM_URL_SCHEME` on Windows | Pre-v1.21.5 CLI passed raw OS paths to `tsImport`. | Upgrade `mcp-use@latest`. |
| Missing `zod` peer dependency after upgrading to v1.21.5 | Zod moved from dep to peerDep. | `npm install zod@^4.0.0`. |
| `mcp-use build` hangs after "Build complete" | Pre-v1.21.4 CLI missing `process.exit(0)`. | Upgrade `@mcp-use/cli@latest`. |

---

## 2. Server lifecycle

| Error | Cause | Fix |
|---|---|---|
| Tool not found when calling registered tool | Tool registered after `server.listen()`, typo, or two `MCPServer` instances. | Register tools before `listen()`. Verify name with `client.listTools()`. |
| Server starts but no tools appear | Same as above. | Register before `listen()`. Don't construct multiple `MCPServer`. |
| Client receives notifications but tool responses are empty | Handler doesn't return. | Return via `text()` / `error()` / response helper on every code path. Enable `noImplicitReturns`. |
| Connection refused | Server not running, wrong port, firewall, silent crash. | `ps aux \| grep node`; `lsof -i :3000`; verify `/mcp` URL. |
| `EADDRINUSE: address already in use :::3000` | Another process owns the port. | `lsof -ti:3000 \| xargs kill`. Or `PORT=3001 node dist/index.js`. |
| Broken local connection after restart | Stale client session against dead HTTP connection. | Restart client. Re-run `tools/list` or reconnect Inspector. |
| `ENOSPC: System limit for number of file watchers reached` | File watcher recursing into `node_modules`. | Ignore `node_modules` and `dist` in watcher config. Linux: `fs.inotify.max_user_watches=524288`. |
| Memory grows steadily over hours | Unbounded caches, leaked listeners, accumulated session state. | Profile with `node --inspect`. Add TTL/size limits. Clean up on `close`. |
| `Invalid character in header content` | Unsanitized user input passed into HTTP headers. | `val.replace(/[\r\n]/g, '')` before set. |
| Zombie processes in Docker | PID 1 not an init system. | `tini` in Dockerfile or `docker run --init`. |

---

## 3. Schemas and validation

| Error | Cause | Fix |
|---|---|---|
| Zod validation failures from client args | Schema mismatch with what LLM generates. | Add `.describe()` everywhere. Use `z.coerce` for numbers/booleans. `.default()` on optional fields. Test with Inspector. |
| Invalid JSON-RPC response | Client hit wrong endpoint, proxy returned HTML, middleware mutated response. | Confirm client uses `/mcp`. Check raw body with `curl -i`. Disable proxy rewrites until clean. |

---

## 4. Sessions

| Error | Cause | Fix |
|---|---|---|
| Session lost between requests (Streamable HTTP) | Client doesn't echo `Mcp-Session-Id`. | Use SDK's `StreamableHTTPClientTransport`. Configure `sessionStore`. |
| `404 Not Found` after server restart (v1.21.1+) | In-memory session store wiped on restart. | Use `RedisSessionStore`. Per spec, clients must send a new `InitializeRequest` on 404. |
| `400 Bad Request` after restart (v1.21.0 only) | Session recovery sent 400 instead of spec-required 404. | Upgrade to v1.21.1+. |
| `RedisSessionStore` connection failure | Bad `REDIS_URL`, Redis down, or fs permissions for file store. | `redis-cli -u $REDIS_URL ping`. Fall back to `InMemorySessionStore` in dev. Add retry. |

---

## 5. Auth (OAuth and Supabase)

The full auth troubleshooting set lives at `03-oauth-and-supabase-issues.md`. This catalog has one-row entries for grepping; the deep notes are next door.

| Error | Cause | Fix |
|---|---|---|
| `401 Unauthorized` on protected endpoints | Missing/expired token, wrong provider, insufficient scopes. | Verify provider config and credentials. Check token expiry. Confirm scopes. |
| `ctx.auth` is undefined in tool handler | Pre-v1.21.4 `mountMcp()` didn't wrap `handleRequest()` in `runWithContext()`. | Upgrade `mcp-use@^1.21.4`. Always guard `ctx.auth` with null check. |
| `Incompatible auth server: does not support dynamic client registration` | `SupabaseOAuthProvider` proxy mode lacks `registration_endpoint`. | See `03-oauth-and-supabase-issues.md`. |
| `Unsupported provider: Provider could not be found` (Supabase) | Missing `provider=google` query param to Supabase `/auth/v1/authorize`. | Custom authorize handler. See `03-oauth-and-supabase-issues.md`. |
| `bad_json` from Supabase token exchange | mcp-use proxy uses form-urlencoded; Supabase requires JSON + `apikey` header. | Custom token handler. See `03-oauth-and-supabase-issues.md`. |
| `redirect_uri_mismatch` from Google via Supabase | Dynamic localhost not allowed, or `client_id` forwarded to Google. | Add `http://localhost:*/**` to Supabase redirect URLs. Don't forward `client_id`. |
| `ctx.client.user()` returns undefined | Added in v1.21.0; client not sending user metadata. | Upgrade. Guard with `?? "anonymous"`. |
| DNS rebinding 403 | `Host` header doesn't match `allowedOrigins`. | Add domain to `allowedOrigins` on `MCPServer`. Test: `curl -H "Host: evil.com"` → 403. |

---

## 6. CORS and CSP

| Error | Cause | Fix |
|---|---|---|
| Browser CORS errors | Server didn't send `Access-Control-Allow-Origin`, or `cors` config too restrictive. | Pass `cors` to `MCPServer`. Include `mcp-session-id` in `allowHeaders` and `exposeHeaders`. |
| CSP violations — widget content blocked | Wrong CSP headers, missing widget origins. | See `05-csp-violations.md`. Configure `widgetMetadata.metadata.csp.connectDomains`. |
| Duplicate CSP meta tags (pre-v1.20.1) | Sandbox proxy injected without removing existing. | Upgrade `mcp-use@^1.20.1`. |

---

## 7. Transports and proxies

| Error | Cause | Fix |
|---|---|---|
| SSE connection drops after 60s | Proxy idle timeout (nginx, Cloudflare, ALB). | `proxy_read_timeout 86400s; proxy_send_timeout 86400s;`. Or migrate to Streamable HTTP — see `28-migration/03-sse-to-streamable-http.md`. |
| Timeout for long-running tools | Tool exceeds client timeout. | Use `ctx.reportProgress`. Or return job ID + polling tool. Increase client timeout if appropriate. |
| Payload too large (413) | Transport or proxy size limit. | Increase nginx `client_max_body_size`. Use blob/resource patterns instead of inline arguments. |
| Rate limit exceeded (429) | Server or upstream API throttling. | Backoff/retry on client. Cache on server. Token bucket on server. Return `Retry-After`. |
| Gateway timeout (504) | Tool exceeds LB `proxy_read_timeout`. | Increase LB timeout. Switch to async job pattern. Keep sync tools < 30s. |
| Protocol version mismatch | Client speaks newer/older MCP protocol. | Upgrade `mcp-use`. Capability negotiation handles compatible mismatches automatically. |

---

## 8. Elicitation

| Error | Cause | Fix |
|---|---|---|
| `result.data` undefined after `ctx.elicit()` (open in v1.21.5, fixed in v1.22.0) | Spec puts data in `result.content`; older versions never mapped to `data`. | Upgrade to v1.22.0+. Workaround: `result.data ?? (result as any).content`. |
| `ElicitationDeclinedError` | User cancelled the prompt. | Catch and return graceful response. |
| `ElicitationTimeoutError` | No response inside `timeoutMs`. | Catch. Use `e.timeoutMs`. Provide default behavior. |
| `ElicitationValidationError` | User input failed Zod schema. | Catch. Inspect `e.cause`. Use `.describe()` and `z.coerce` on schema. |

---

## 9. Widgets (cross-link)

Widget-specific issues live at `04-widget-rendering-issues.md`. Catalog entries for grep:

| Error | Cause | Fix |
|---|---|---|
| Widget shows duplicate CSP meta tags (pre-v1.20.1) | Sandbox didn't strip existing tags. | Upgrade `mcp-use@^1.20.1`. |
| React Router not working in widget (v1.20.1+) | `McpUseProvider` no longer wraps `BrowserRouter`. | Add `<BrowserRouter>` manually inside `<McpUseProvider>`. |
| Widget renders as plain HTML / blank / hooks fire outside provider | See `04-widget-rendering-issues.md`. | — |

---

## 10. CLI / deploy

| Error | Cause | Fix |
|---|---|---|
| `mcp-use deploy` fails | Not a git repo, GitHub App not installed, missing `dist/mcp-use.json`. | `git init`. Install GitHub App on first prompt. Run `mcp-use build` first. |
| New subdomain on every deploy / custom domain breaks | `.mcp-use/project.json` missing on the deploy machine. | Track `!.mcp-use/project.json` in `.gitignore`. Commit, push. |
| Deployed server missing recent changes | `mcp-use deploy` builds from remote HEAD on GitHub. | `git add && commit && push` before `mcp-use deploy`. |
| OrbStack port conflict (macOS, mcpc) | OrbStack claims ports that mcpc allocates. | `lsof -i :<port>`. Stop OrbStack or pick non-overlapping port. |

---

## 11. Cosmetic warnings

| Warning | Cause | Fix |
|---|---|---|
| `resourceCallbacks undefined` / `Cannot read properties of undefined (reading 'complete')` | mcp-use references `callbacks.complete` on resource templates even without callbacks. | Harmless. Silence by passing `callbacks: { complete: async () => ({ values: [] }) }` if it bothers you. |
| `GET /health` returns Inspector HTML | mcp-use serves Inspector on all `GET` requests; no explicit `/health` route. | Register `server.get("/health", c => c.json({ status: "ok" }))` **before** `listen()`. |
