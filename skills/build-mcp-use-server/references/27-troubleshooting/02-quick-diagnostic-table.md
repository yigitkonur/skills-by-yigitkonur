# Quick Diagnostic Table

"I'm seeing X" → "check Y". Topical decision shortcut. For full error → cause → fix rows, see `01-error-catalog.md`.

---

## Build / runtime

| Symptom | First check |
|---|---|
| Import errors | `moduleResolution` in `tsconfig.json`. Importing from `mcp-use/server`? |
| Tools not visible | Tools registered before `listen()`? |
| Garbled responses | `console.log()` going to stdout on a stdio server? |
| Connection drops | Proxy timeout settings. |
| Memory growth | Unbounded caches or listeners. |
| Auth failures | Token expiration and scopes; `mcp-use` ≥ v1.21.4? |
| Port conflicts | `lsof -i :<port>`. |
| Timeout | Progress reporting enabled? |

---

## Sessions

| Symptom | First check |
|---|---|
| 404 after restart | Session store persistent? `RedisSessionStore` configured? |
| 400 after restart | Upgrade to v1.21.1+. |
| Session lost between requests | Client echoing `Mcp-Session-Id`? |
| `RedisSessionStore` connection failure | `redis-cli -u $REDIS_URL ping`. |

---

## Context and elicitation

| Symptom | First check |
|---|---|
| `ctx.auth` undefined | `mcp-use` ≥ v1.21.4? Null-guard the read? |
| `ctx.client.user()` undefined | `mcp-use` ≥ v1.21.0? Client sending user metadata? |
| `result.data` undefined after `elicit()` | Open bug pre-v1.22.0 — use `result.data ?? (result as any).content`. |
| `ElicitationDeclinedError` | Catch in try/catch. User cancelled. |
| `ElicitationTimeoutError` | Catch. Inspect `e.timeoutMs`. |
| `ElicitationValidationError` | Catch. Inspect `e.cause` (Zod error). |

---

## Networking

| Symptom | First check |
|---|---|
| CORS errors in browser | `cors` config explicit? `mcp-session-id` in `allowHeaders` + `exposeHeaders`? |
| DNS rebinding 403 | `Host` header. Add to `allowedOrigins`. |
| SSE drops at 60s | Proxy idle timeout. Or migrate to Streamable HTTP. |
| Payload too large (413) | nginx `client_max_body_size`. Switch to resources. |
| Gateway timeout (504) | LB timeout. Async job pattern. |

---

## Auth (OAuth and Supabase)

| Symptom | First check |
|---|---|
| 401 on protected endpoint | Token, scopes, provider config. |
| "Incompatible auth server: does not support DCR" | Supabase proxy mode missing `registration_endpoint`. See `03-oauth-and-supabase-issues.md`. |
| "Unsupported provider" (Supabase) | Missing `provider=google` query param. Custom authorize handler. |
| `bad_json` (Supabase token) | Supabase needs JSON + `apikey` header, not form-urlencoded. Custom token handler. |
| `redirect_uri_mismatch` (Google via Supabase) | Add `http://localhost:*/**` to redirect URLs. Don't forward `client_id`. |

Full OAuth + Supabase details: `03-oauth-and-supabase-issues.md`.

---

## Widgets

| Symptom | First check |
|---|---|
| Widget shows as plain HTML | Host doesn't speak MCP Apps protocol. See `04-widget-rendering-issues.md`. |
| Widget loads but blank | CSP violation in browser console. See `05-csp-violations.md`. |
| Hooks fire outside `McpUseProvider` | Provider missing in widget tree. |
| Duplicate CSP meta tags | Upgrade to v1.20.1+. |
| React Router broken in widget | `McpUseProvider` no longer wraps `BrowserRouter` (v1.20.1+); add manually. |

---

## CLI and deploy

| Symptom | First check |
|---|---|
| `mcp-use deploy` fails | Git initialized? GitHub App installed? `dist/mcp-use.json` exists? |
| New subdomain every deploy | Track `.mcp-use/project.json` in git. |
| Deployed server missing changes | `git push` before `mcp-use deploy`. |
| `mcp-use build` hangs | Upgrade `@mcp-use/cli@latest`. |
| `zod` not found after upgrade | Add `zod@^4.0.0` to your own `package.json`. |
| Windows `ERR_UNSUPPORTED_ESM_URL_SCHEME` | Upgrade to v1.21.5+. |
| OrbStack port conflict (macOS) | `lsof -i :<port>`; pick another port or stop OrbStack. |

---

## Filesystem and process

| Symptom | First check |
|---|---|
| `ENOSPC` watchers | `node_modules` excluded from watcher? |
| Zombie processes in Docker | `tini` ENTRYPOINT or `docker run --init`. |
| `EADDRINUSE` | `lsof -ti:<port> \| xargs kill`. |

---

## Cosmetic / harmless

| Symptom | First check |
|---|---|
| `resourceCallbacks undefined` warning | Harmless. Provide empty `callbacks.complete` to silence. |
| `GET /health` returns HTML | Register explicit `server.get("/health", ...)` before `listen()`. |

---

If a symptom matches none of these, jump to the decision tree at `06-decision-tree.md`.
