# OAuth and Supabase Issues

The single home for OAuth + Supabase auth troubleshooting. The auth cluster (`11-auth/`) and the anti-patterns cluster do **not** repeat this content; they link here.

For the v1.25.0 architectural shift to DCR-direct as the default, see `28-migration/05-dcr-vs-proxy-mode-shift.md`.

---

## 1. `Incompatible auth server: does not support dynamic client registration`

**When:** A third-party MCP client (mcpc, Claude Desktop) tries to connect to a server using `oauthSupabaseProvider()` in proxy mode.

**Cause:** `SupabaseOAuthProvider` in proxy mode serves `/.well-known/oauth-authorization-server` metadata **without** a `registration_endpoint`. RFC 7591 DCR clients reject the server immediately. `/.well-known/oauth-protected-resource` points to Supabase as the AS, and Supabase itself has no DCR endpoint.

**Fix:**

1. Add a `server.use("*", ...)` middleware that intercepts both `/.well-known/oauth-authorization-server` and `/.well-known/oauth-protected-resource` and returns metadata pointing at **your own server** with a `registration_endpoint` field.
2. Add `POST /oauth/register` implementing minimal RFC 7591 DCR — a handler that returns a generated `client_id` is enough.
3. Add custom `/oauth/authorize` and `/oauth/token` handlers on **custom paths** (don't reuse `/authorize` or `/token` — those are claimed by mcp-use's built-in proxy).

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({ name: "...", version: "1.0.0" });

server.use("*", async (c, next) => {
  if (c.req.path === "/.well-known/oauth-authorization-server") {
    return c.json({
      issuer: "https://your-server.com",
      authorization_endpoint: "https://your-server.com/oauth/authorize",
      token_endpoint: "https://your-server.com/oauth/token",
      registration_endpoint: "https://your-server.com/oauth/register",
      response_types_supported: ["code"],
      grant_types_supported: ["authorization_code", "refresh_token"],
    });
  }
  await next();
});

server.post("/oauth/register", async (c) => {
  const body = await c.req.json();
  return c.json({
    client_id: crypto.randomUUID(),
    client_secret: null,
    redirect_uris: body.redirect_uris,
    grant_types: ["authorization_code", "refresh_token"],
  });
});
```

**Prevention:** Before choosing `oauthSupabaseProvider()`, verify whether your target MCP clients require DCR. If they do, plan for the custom middleware from the start. Or use DCR-direct (default since v1.25.0) instead of proxy mode.

---

## 2. `Unsupported provider: Provider could not be found` (Supabase)

**When:** User redirected to Supabase's `/auth/v1/oauth/authorize` (legacy `/auth/v1/authorize` before v1.25.1) during the OAuth flow.

**Cause:** mcp-use's built-in proxy `/authorize` handler forwards the request to Supabase **without** injecting the `provider` query parameter. Supabase requires `provider=google` (or whichever social provider is configured) to know which OAuth flow to start.

**Fix:**

1. Create a custom authorize handler at `/oauth/authorize` that adds `provider=google` to the Supabase redirect URL.
2. Update `/.well-known/oauth-authorization-server` metadata to point `authorization_endpoint` at your custom handler.
3. Map `redirect_uri` to `redirect_to` (Supabase's expected parameter name).

```typescript
server.get("/oauth/authorize", async (c) => {
  const params = new URL(c.req.url).searchParams;
  const supabase = new URL(`${SUPABASE_URL}/auth/v1/oauth/authorize`);
  supabase.searchParams.set("provider", "google");
  supabase.searchParams.set("redirect_to", params.get("redirect_uri")!);
  // forward state, scope, etc., but NOT client_id
  return c.redirect(supabase.toString());
});
```

**Prevention:** Never rely on mcp-use's default proxy authorize handler when using Supabase with a social provider.

---

## 3. `bad_json` from Supabase token exchange

**When:** Token exchange against Supabase's `/auth/v1/oauth/token` (legacy `/auth/v1/token` before v1.25.1).

**Cause:** mcp-use's proxy sends `Content-Type: application/x-www-form-urlencoded`. Supabase's token endpoint requires `Content-Type: application/json` with a JSON body, plus an `apikey` header set to the Supabase anon key.

**Fix:**

1. Custom `POST /oauth/token` handler.
2. Send JSON body. Include `apikey` header.
3. Translate parameters: `code` → `auth_code`, `grant_type` → `pkce`. Do **not** forward `client_id`.
4. Update `/.well-known/oauth-authorization-server` to point `token_endpoint` at your custom handler.

```typescript
server.post("/oauth/token", async (c) => {
  const form = await c.req.parseBody();
  const res = await fetch(`${SUPABASE_URL}/auth/v1/oauth/token?grant_type=pkce`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "apikey": SUPABASE_ANON_KEY,
    },
    body: JSON.stringify({
      auth_code: form.code,
      code_verifier: form.code_verifier,
    }),
  });
  return c.json(await res.json(), res.status);
});
```

**Prevention:** Always use a custom token handler when integrating with Supabase. The default proxy's form-urlencoded encoding is incompatible.

---

## 4. `redirect_uri_mismatch` from Google via Supabase

**When:** Google OAuth callback fails after user authenticates.

**Causes:**

1. The MCP client uses a dynamic localhost port (e.g. `http://localhost:54321/oauth/callback`) not in Supabase's allowed redirect URLs. Supabase falls back to the configured Site URL, which Google rejects.
2. `client_id` was forwarded to Supabase, which passed it to Google. Google rejects the unknown `client_id`.

**Fix:**

1. Supabase Dashboard → Authentication → URL Configuration → Redirect URLs: add `http://localhost:*/**`.
2. Custom token handler must NOT forward `client_id`.
3. Set Site URL to your production MCP server URL.

**Prevention:** Always include localhost wildcard in Supabase redirect URLs for development. Never forward `client_id` from DCR clients to Supabase.

---

## 5. `401 Unauthorized` on protected endpoints

**When:** Generic auth failure on a protected route.

**Causes (in order to check):**

1. Missing or expired access token.
2. Wrong OAuth provider config (issuer URL, audience).
3. Insufficient scopes — token has `read` but tool requires `write`.

**Fix:**

1. Inspect the `Authorization` header — is the bearer present and current?
2. Decode the JWT (`jwt.io` for dev only) — check `exp` and `aud`.
3. Compare `scope` claim against what the tool requires.
4. Implement token refresh on the client side if supported by the provider.

**Prevention:** Log auth failures with context (issuer, scopes seen, audience expected) — never log the token itself.

---

## 6. `ctx.auth` is undefined in tool handler

**When:** `ctx.auth` reads as `undefined` even though OAuth is configured and the user is authenticated.

**Cause:** v1.21.1–v1.21.3 regression — `mountMcp()` stopped wrapping `transport.handleRequest()` in `runWithContext()`, so `AsyncLocalStorage` was never populated for the MCP request lifecycle. Fixed in v1.21.4.

**Fix:**

1. `npm install mcp-use@latest` (≥ v1.21.4).
2. If you can't upgrade immediately:
   ```typescript
   import { runWithContext } from "mcp-use/server";
   server.app.use("/mcp/*", async (c, next) => runWithContext(c, () => next()));
   ```
3. Always guard `ctx.auth` with `if (!ctx.auth) return error("Not authenticated")`.

---

## 7. Endpoint paths changed in v1.25.1

`SupabaseOAuthProvider` endpoint getters now return OAuth 2.1 paths instead of legacy paths:

| Old (pre-v1.25.1)             | New (v1.25.1+)                  |
|-------------------------------|---------------------------------|
| `/auth/v1/authorize`          | `/auth/v1/oauth/authorize`      |
| `/auth/v1/token`              | `/auth/v1/oauth/token`          |

If you copied the legacy paths into custom middleware, update them. The mcp-use defaults handle this automatically once you upgrade.

---

## 8. When to give up on proxy mode

If you're hitting three or more of the above on the same setup, the path of least resistance since v1.25.0 is **DCR-direct**: your MCP clients hit Supabase directly, mcp-use does not proxy `/authorize` or `/token`. See `28-migration/05-dcr-vs-proxy-mode-shift.md`.

The proxy mode is now an explicit escape hatch via `oauthProxy()` (also new in v1.25.0). Use it only when the upstream AS truly does not support DCR (Google, GitHub).
