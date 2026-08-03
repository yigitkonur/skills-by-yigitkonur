# Authentication and OAuth Migration

*Read this to migrate OAuth providers, handle user context changes, and remove the OAuth Proxy.*

## OAuth provider imports

**v1** (all from root):
```typescript
import { MCPServer, oauthAuth0Provider, oauthClerkProvider } from "mcp-use/server";
```

**v2** (providers scattered to subpaths):
```typescript
import { MCPServer } from "mcp-use";
import { oauthAuth0Provider } from "mcp-use/oauth/auth0";
import { oauthClerkProvider } from "mcp-use/oauth/clerk";
import { oauthSupabaseProvider } from "mcp-use/oauth/supabase";
import { oauthKeycloakProvider } from "mcp-use/oauth/keycloak";
import { oauthWorkOSProvider } from "mcp-use/oauth/workos";
import { oauthBetterAuthProvider } from "mcp-use/oauth/better-auth";
import { oauthCustomProvider } from "mcp-use/oauth";
```

## Built-in provider setup: Clerk example

**v1**:
```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth: oauthClerkProvider(...), // import from "mcp-use/server"
});
```

**v2**:
```typescript
import { MCPServer } from "mcp-use";
import { oauthClerkProvider } from "mcp-use/oauth/clerk";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth: oauthClerkProvider({
    frontendApiUrl: "https://your-domain.clerk.accounts.dev",
  }),
});
```

All providers require explicit option objects (no implicit env fallback).

## User context: userId → user.id

**v1**:
```typescript
export const protected = server.tool(
  { name: "protected", ... },
  async (_, ctx) => {
    const userId = ctx.auth.user.userId; // ← Removed
    const email = ctx.auth.user.email;
    return { ... };
  }
);
```

**v2**:
```typescript
export const protected = server.tool(
  { name: "protected", ... },
  async (_, ctx) => {
    const userId = ctx.auth.user.id; // ← Renamed to provider-specific `id`
    const email = ctx.auth.user.email;
    return { ... };
  }
);
```

**Why**: v2 uses provider-native user shapes. Every provider has an `id: string` field (the stable user identifier). Use `ctx.auth.user.id`, never `userId`.

## Provider-specific user fields

Each provider returns a different user type. Examples:

**Clerk** (`oauthClerkProvider`):
```typescript
ctx.auth.user.id                  // string — Clerk subject ID
ctx.auth.user.email               // optional
ctx.auth.user.name                // optional
ctx.auth.user.organizationId      // optional — active org
ctx.auth.user.organizationRole    // optional — role in active org
ctx.auth.user.roles               // string[] — normalized roles
```

**Auth0** (`oauthAuth0Provider`):
```typescript
ctx.auth.user.id                  // string — Auth0 subject
ctx.auth.user.email               // optional
ctx.auth.user.nickname            // optional
ctx.auth.user.roles               // string[] — from access token
```

**Supabase** (`oauthSupabaseProvider`):
```typescript
ctx.auth.user.id                  // string — Supabase UUID
ctx.auth.user.email               // optional
ctx.auth.user.role                // optional — Postgres role
ctx.auth.user.amr                 // SupabaseAmr[] — auth methods
```

Check provider documentation (in `references/11-auth/providers/`) for your provider's full shape.

## OAuth Proxy: Removal and migration

**v1**: OAuth Proxy allowed mcp-use to broker tokens for fixed-client providers (Google, GitHub, Okta) that don't support Dynamic Client Registration (DCR).

**v2**: OAuth Proxy is **removed**. No `oauthProxy()` export.

### Migration path for fixed-client providers

If your v1 server uses `oauthProxy()` for a provider without DCR, deploy an external authorization-server/broker layer:

- The external layer accepts MCP client registration (DCR), completes the fixed-client upstream flow, and issues/verifies resource-bound access tokens.
- The MCP server verifies those tokens with `oauthCustomProvider` or a built-in provider.
- Keycloak or another authorization server can fill this role; pointing `oauthCustomProvider` directly at a non-DCR provider does **not** add DCR and is not a replacement for the removed proxy.

### Custom verification for a DCR-capable provider

Use `oauthCustomProvider` directly only when the upstream authorization server already supports Dynamic Client Registration but mcp-use has no built-in adapter. `createTokenVerifier(resource)` must return an `OAuthTokenVerifier` object (`{ verifyAccessToken }`), not a bare function:

```typescript
import { oauthCustomProvider } from "mcp-use/oauth";
import { jwtVerify } from "jose";

const oauth = oauthCustomProvider({
  createTokenVerifier: (resource) => ({
    async verifyAccessToken(token) {
      // Manually verify token (e.g., against provider's JWKS)
      const { payload } = await jwtVerify(token, jwks, {
        issuer: "https://your-provider.com",
        audience: resource.href,
      });
      if (!payload.sub || !payload.exp) throw new Error("Token missing sub or exp");
      return {
        token,
        clientId: typeof payload.client_id === "string" ? payload.client_id : "",
        scopes: [],
        expiresAt: payload.exp,
        resource,
        extra: { payload }, // your verified claims, read back via authInfo.extra in mapAuthInfo
      };
    },
  }),
  oauthMetadata: {
    issuer: "https://your-provider.com",
    authorization_endpoint: "https://your-provider.com/oauth/authorize",
    token_endpoint: "https://your-provider.com/oauth/token",
    registration_endpoint: "https://your-provider.com/oauth/register", // Required for direct MCP client registration
    jwks_uri: "https://your-provider.com/.well-known/jwks.json",
  },
  mapAuthInfo: (authInfo) => {
    const payload = authInfo.extra?.payload as Record<string, unknown> | undefined;
    return {
      user: {
        id: (payload?.sub as string) ?? authInfo.clientId ?? "unknown",
        email: payload?.email as string | undefined,
      },
      payload: payload ?? {},
      permissions: [],
    };
  },
});
```

## Custom provider options

If you had a custom provider in v1, the shape has changed:

**v1**:
```typescript
{
  issuer: "https://auth.example.com",
  verifyToken: async (token) => { /* verify */ },
  jwksUrl: "https://auth.example.com/.well-known/jwks.json",
  getUserInfo: (payload) => ({ userId: payload.sub, email: payload.email }),
}
```

**v2**: `createTokenVerifier(resource)` returns an `OAuthTokenVerifier` object; `mapAuthInfo` reads `authInfo.extra` (populated by your own verifier), not `authInfo.claims` (no such field exists):
```typescript
oauthCustomProvider({
  createTokenVerifier: (resource) => ({
    async verifyAccessToken(token) {
      // Your verification logic; receives resource URL (MCP endpoint)
      // Must return AuthInfo: { token, clientId, scopes, expiresAt, resource, extra? }
      return {
        token,
        clientId: "client-123",
        scopes: [],
        expiresAt: Math.floor(Date.now() / 1000) + 3600,
        resource,
        extra: { claims: { sub: "user-123", email: "user@example.com" } },
      };
    },
  }),
  oauthMetadata: {
    // RFC 8414 metadata object
    issuer: "https://auth.example.com",
    authorization_endpoint: "...",
    token_endpoint: "...",
    jwks_uri: "...",
  },
  mapAuthInfo: (authInfo) => {
    const claims = authInfo.extra?.claims as { sub: string; email?: string };
    return {
      user: { id: claims.sub, email: claims.email },
      payload: claims,
      permissions: [],
    };
  },
})
```

## Permission mapping

**v1**:
```typescript
ctx.auth.scopes        // OAuth grants
ctx.auth.permissions   // Custom app-level claims (if provider supplied them)
ctx.hasScope("scope")
ctx.requireScope("scope")
```

**v2**:
```typescript
ctx.auth.scopes        // OAuth grants (still available)
ctx.auth.permissions   // Provider-mapped or custom claim (from mapAuthInfo)
// No hasScope/requireScope; use array methods:
if (!ctx.auth.permissions.includes("admin")) {
  throw new Error("Not admin");
}
```

Permission guards must be written explicitly; no built-in helpers.

## Unauthenticated requests

When OAuth is configured on `MCPServer`, unauthenticated requests (missing bearer token) are rejected at the endpoint level before your tool callback runs. `ctx.auth` is guaranteed present in protected callbacks.

---

**Next**: See `06-v1-to-v2-widgets-to-views.md` for View migration.
