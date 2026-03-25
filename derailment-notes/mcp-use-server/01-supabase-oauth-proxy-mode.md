# Derailment Report: Supabase OAuth Proxy Mode with Third-Party MCP Clients

**Date**: 2026-03-25
**Affected versions**: mcp-use v1.21.5 with `oauthSupabaseProvider()`
**Severity**: Multi-hour derailment; authentication completely broken for third-party clients
**Environment**: mcp-use + Supabase Auth (Google provider) + mcpc / Claude Desktop as clients

---

## Summary

Using `oauthSupabaseProvider()` with default settings (proxy mode) results in a server that **cannot authenticate third-party MCP clients** that require RFC 7591 Dynamic Client Registration (DCR). The proxy mode metadata is incomplete, parameter mapping is incompatible with standard OAuth, and Hono routing prevents overriding built-in OAuth routes. Hours were spent diagnosing cascading failures across six different friction points.

---

## Friction Points

### F-01: SupabaseOAuthProvider does not implement `getRegistrationEndpoint()` or `getMode()`

**What happened**: Third-party clients (mcpc, Claude Desktop) that require DCR received `"Incompatible auth server: does not support dynamic client registration"` immediately on connection.

**Root cause**: `SupabaseOAuthProvider` does not implement `getRegistrationEndpoint()` or `getMode()`, so it defaults to `"proxy"` mode. Proxy mode hardcodes OAuth metadata WITHOUT a `registration_endpoint` field. WorkOS and Auth0 providers implement these methods; Supabase does not.

**Impact**: Complete authentication failure for any client that expects DCR.

**Resolution**: Override `/.well-known/oauth-authorization-server` via `server.use("*", ...)` middleware to inject `registration_endpoint` pointing to a custom DCR handler.

---

### F-02: Proxy mode `oauth-protected-resource` points clients to Supabase directly

**What happened**: `GET /.well-known/oauth-protected-resource` returned Supabase as the `authorization_server`. Clients fetched metadata FROM Supabase (not from the MCP server). Since Supabase has no DCR endpoint, clients rejected it.

**Root cause**: Proxy mode sets `resource` metadata with the upstream Supabase URL as the authorization server. Clients follow this URL to discover OAuth capabilities and find no DCR support.

**Impact**: Even after adding a custom DCR endpoint to the MCP server, clients never reached it because they were directed to Supabase for metadata.

**Resolution**: Override `oauth-protected-resource` to point `authorization_servers` at the MCP server's own URL, not Supabase.

---

### F-03: Hono trie router prevents overriding mcp-use's built-in OAuth routes

**What happened**: `server.get("/.well-known/oauth-authorization-server", handler)` silently failed to override the route. The mcp-use built-in handler still ran.

**Root cause**: mcp-use registers OAuth routes with `app.get("/authorize", ...)` during `listen()`. Hono's trie router gives SPECIFIC routes priority over wildcard `app.all("*")` catch-all. Since `server.get()` / `server.post()` go through `_customRoutes` which uses `app.all("*")`, custom handlers cannot win against mcp-use's specific routes.

**Impact**: Wasted significant time adding `server.get()` routes that appeared to register but never executed.

**Resolution**:
- Use `server.use("*", middleware)` to intercept `.well-known/*` paths (middleware runs before route handlers).
- Use custom paths like `/oauth/authorize` and `/oauth/token` for handlers that cannot override built-in routes (`/authorize`, `/token`).

---

### F-04: Supabase authorize endpoint requires `provider=google` parameter

**What happened**: Users redirected to Supabase's authorize endpoint saw `"Unsupported provider: Provider could not be found"`.

**Root cause**: mcp-use's proxy `/authorize` forwards the request to Supabase WITHOUT injecting the `provider` parameter. Supabase requires `provider=google` (or whichever social provider is configured) to know which OAuth flow to initiate.

**Impact**: Login flow completely broken even after metadata/DCR issues were resolved.

**Resolution**: Custom `/oauth/authorize` handler that injects `provider=google` into the Supabase redirect URL.

---

### F-05: Supabase parameter naming differs from standard OAuth

**What happened**: Token exchange returned various errors because standard OAuth parameter names were sent to Supabase.

**Root cause**: Supabase uses non-standard parameter names:

| Standard OAuth | Supabase equivalent |
|---|---|
| `redirect_uri` | `redirect_to` |
| `code` (auth code) | `auth_code` |
| `grant_type=authorization_code` | `grant_type=pkce` |
| `client_id` (forwarded) | Must NOT be forwarded (Supabase passes it to Google, which rejects unknown IDs) |

**Impact**: Token exchange failed silently or returned opaque errors from the upstream Google OAuth.

**Resolution**: Custom `/oauth/token` handler that translates parameter names and strips `client_id` before forwarding to Supabase.

---

### F-06: Supabase token endpoint requires JSON body + `apikey` header

**What happened**: Token exchange returned `"bad_json"` error from Supabase.

**Root cause**: mcp-use's proxy sends `Content-Type: application/x-www-form-urlencoded` to Supabase's `/auth/v1/token` endpoint. Supabase expects `Content-Type: application/json` with the Supabase anon key in an `apikey` header.

**Impact**: Even after fixing parameter names, the token exchange still failed.

**Resolution**: Custom token handler sends JSON body with `apikey` header (anon key from `SUPABASE_URL`-derived config).

---

### F-07: `mcp-use deploy` clones from git, not local files

**What happened**: Deployed server did not include recent OAuth fixes. The deployed version still had the broken proxy behavior.

**Root cause**: `mcp-use deploy` clones from the GitHub remote HEAD, not from the local working directory. Uncommitted or unpushed changes are invisible to the deployment.

**Impact**: Multiple deploy cycles wasted before realizing changes needed to be committed and pushed first.

**Resolution**: Always `git add . && git commit && git push` before running `mcp-use deploy`.

---

### F-08: Supabase Dashboard redirect URL configuration required for dynamic ports

**What happened**: After fixing everything server-side, mcpc still received `redirect_uri_mismatch` from Google OAuth.

**Root cause**: mcpc uses dynamic localhost ports for its OAuth callback (e.g., `http://localhost:54321/oauth/callback`). Supabase validates redirect URIs against its Dashboard configuration. Without a wildcard localhost entry, Supabase falls back to the configured Site URL.

**Impact**: OAuth flow completed on the server side but failed at the Google redirect step.

**Resolution**: Add `http://localhost:*/**` to Supabase Dashboard > Authentication > URL Configuration > Redirect URLs.

---

## Correct Implementation Pattern

The working solution requires:

1. A `server.use("*", ...)` wildcard middleware that intercepts `.well-known/*` paths and overrides metadata to point at the MCP server
2. A custom `/oauth/authorize` handler that injects `provider=google` and maps `redirect_uri` to `redirect_to`
3. A custom `/oauth/token` handler that sends JSON (not form-urlencoded) to Supabase with the `apikey` header, maps `code` to `auth_code`, and strips `client_id`
4. A custom `/oauth/register` handler for RFC 7591 DCR
5. Supabase Dashboard configured with `http://localhost:*/**` in Redirect URLs

---

## Prevention

- The `authentication.md` skill guide should warn that `oauthSupabaseProvider()` proxy mode does NOT support DCR out of the box
- The `common-errors.md` should list all five error messages encountered (DCR incompatible, unsupported provider, bad_json, redirect_uri_mismatch)
- The `anti-patterns.md` should flag forwarding `client_id` to Supabase and using form-urlencoded for Supabase token exchange
- Future agents should check whether the target MCP client requires DCR before choosing a provider mode
