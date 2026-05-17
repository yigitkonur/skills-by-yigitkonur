# DCR-Direct vs Proxy Mode: the v1.25.0 Architectural Shift

In v1.25.0 (April 2026), built-in OAuth providers default to **DCR-direct** instead of proxy mode. Proxy mode is now an explicit escape hatch via `oauthProxy()`.

For deeper architectural detail and the conceptual model, see `../11-auth/02-dcr-vs-proxy-mode.md`.

---

## 1. The shift

| Aspect              | Proxy mode (pre-v1.25.0 default)                    | DCR-direct (v1.25.0+ default)                        |
|---------------------|-----------------------------------------------------|------------------------------------------------------|
| Where the client authenticates | mcp-use server proxies to upstream AS    | Client talks directly to upstream AS                  |
| `clientId` / `clientSecret` | On the mcp-use server config              | Not on the server — clients get their own via DCR    |
| `registration_endpoint` | Manually wired                                  | Provided by the upstream AS                          |
| When upstream AS lacks DCR (Google, GitHub) | Proxy mode required                | Use new `oauthProxy()` helper                        |

The shift simplifies the common case (Auth0, WorkOS, Supabase, Keycloak, Better Auth — all support DCR) and pushes the complex case (Google, GitHub) to an explicit escape hatch.

---

## 2. Built-in providers affected

These providers **only** support DCR-direct in v1.25.0+:

- `oauthAuth0Provider()`
- `oauthWorkOSProvider()`
- `oauthSupabaseProvider()`
- `oauthKeycloakProvider()`
- `oauthBetterAuthProvider()`

Provider configurations no longer accept `clientId` / `clientSecret`. If you pass them, TypeScript flags it; at runtime they're ignored.

---

## 3. New helpers

### `oauthProxy()` — for upstream AS without DCR

```typescript
import { oauthProxy, jwksVerifier } from "mcp-use/server";

const oauth = oauthProxy({
  authEndpoint: "https://accounts.google.com/o/oauth2/v2/auth",
  tokenEndpoint: "https://oauth2.googleapis.com/token",
  issuer: "https://accounts.google.com",
  clientId: process.env.GOOGLE_CLIENT_ID!,
  clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
  scopes: ["openid", "email", "profile"],
  verifyToken: jwksVerifier({
    jwksUrl: "https://www.googleapis.com/oauth2/v3/certs",
    issuer: "https://accounts.google.com",
    audience: process.env.GOOGLE_CLIENT_ID!,
  }),
});

const server = new MCPServer({ name: "...", version: "1.0.0", oauth });
```

Use this for Google, GitHub, or any upstream that doesn't expose `/.well-known/oauth-authorization-server` with a `registration_endpoint`. See `libraries/typescript/packages/mcp-use/examples/server/oauth/auth0-proxy` in the mcp-use repo for the new proxy pattern.

### `jwksVerifier()` — for custom providers

```typescript
import { jwksVerifier } from "mcp-use/server";

const verifyToken = jwksVerifier({
  jwksUrl: "https://your-issuer.com/.well-known/jwks.json",
  issuer: "https://your-issuer.com",
  audience: "https://your-mcp-server.com",
});
```

Use inside a custom `OAuthProvider` for JWKS-based token verification.

### `verifyToken` is now required

If you have a custom `OAuthProvider` (not built-in, not `oauthProxy()`), you must implement `verifyToken`:

```typescript
const provider: OAuthProvider = {
  // ...other fields
  verifyToken: async (token: string) => {
    // throw on invalid; return { payload } on valid
    return { payload: { sub: "user-id" } };
  },
};
```

---

## 4. Migration path for existing servers

### Step 1: identify your current mode

If you call a built-in provider helper (`oauthSupabaseProvider`, `oauthAuth0Provider`, etc.) with `clientId` / `clientSecret`, you were in proxy mode.

### Step 2: pick a target

| Upstream AS          | DCR support? | Target mode               |
|----------------------|--------------|---------------------------|
| Auth0                | Yes          | DCR-direct (default)      |
| WorkOS               | Yes          | DCR-direct (default)      |
| Supabase             | Yes          | DCR-direct (default)      |
| Keycloak             | Yes          | DCR-direct (default)      |
| Better Auth          | Yes          | DCR-direct (default)      |
| Google               | No           | `oauthProxy()`            |
| GitHub               | No           | `oauthProxy()`            |
| Generic (custom)     | Depends      | DCR-direct or `oauthProxy()` |

### Step 3: update server config

For DCR-direct (Auth0 example):

```typescript
// Before (v1.24.x and earlier)
const oauth = oauthAuth0Provider({
  domain: "your-tenant.auth0.com",
  clientId: process.env.AUTH0_CLIENT_ID!,
  clientSecret: process.env.AUTH0_CLIENT_SECRET!,
});

// After (v1.25.0+)
const oauth = oauthAuth0Provider({
  domain: "your-tenant.auth0.com",
  // No clientId/clientSecret — clients get their own via DCR
});
```

For Google via `oauthProxy()`:

```typescript
// New escape-hatch path
const oauth = oauthProxy({
  authEndpoint: "https://accounts.google.com/o/oauth2/v2/auth",
  tokenEndpoint: "https://oauth2.googleapis.com/token",
  issuer: "https://accounts.google.com",
  clientId: process.env.GOOGLE_CLIENT_ID!,
  clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
  scopes: ["openid", "email", "profile"],
  verifyToken: jwksVerifier({
    jwksUrl: "https://www.googleapis.com/oauth2/v3/certs",
    issuer: "https://accounts.google.com",
    audience: process.env.GOOGLE_CLIENT_ID!,
  }),
});
```

### Step 4: update Auth0/WorkOS/etc dashboard

- For DCR-direct, your upstream AS must allow DCR. Most cloud-managed AS providers enable it by default.
- For Auth0: ensure "Dynamic Client Registration" is enabled in tenant settings.
- For WorkOS: DCR is enabled by default for OAuth-protected resources.
- For Supabase: see the Supabase auth troubleshooting in `../27-troubleshooting/03-oauth-and-supabase-issues.md` — Supabase has historical proxy-mode quirks that DCR-direct simplifies.

### Step 5: clean up

For DCR-direct providers, remove `clientId` / `clientSecret` env vars from your server's deploy config — they are now per-client (set by the MCP client during DCR), not per-server. Keep them only for explicit `oauthProxy()` providers.

If you had custom middleware patching `/.well-known/oauth-authorization-server` to add `registration_endpoint` (the Supabase workaround), consider removing it — DCR-direct flows through the upstream's own metadata.

---

## 5. When to keep proxy mode

There are still legitimate reasons:

- The upstream AS truly does not support DCR (Google, GitHub).
- You want a single `client_id` for compliance, audit, or rate-limit reasons (one cost center for all your MCP traffic).
- The upstream AS's DCR policy doesn't suit your tenant model (e.g. you can't or won't allow public DCR).

Use `oauthProxy()` explicitly. It's not deprecated — it's the right tool for these cases.

---

## 6. Test paths after migration

1. Confirm `mcp-use@^1.25.0` is installed.
2. Restart server. `curl /.well-known/oauth-authorization-server` — verify metadata reflects the new mode.
3. Connect a fresh MCP client (one without a stored `client_id`):
   - DCR-direct: client registers itself against the upstream AS, gets a `client_id`, performs auth flow.
   - Proxy: client registers against your mcp-use server, mcp-use proxies the rest.
4. Confirm `ctx.auth` is populated correctly inside a tool handler.
5. Test refresh flow if your AS supports refresh tokens.

---

## 7. Related

- `../11-auth/02-dcr-vs-proxy-mode.md` — conceptual deep dive.
- `../27-troubleshooting/03-oauth-and-supabase-issues.md` — single home for Supabase-specific issues. Most Supabase troubleshooting goes away with DCR-direct.
- `02-mcp-use-v1-to-v2.md` — context on the v1.25.0 release.
