# Custom Provider: oauthCustomProvider

*Read this when your identity provider is not listed in `references/11-auth/01-overview.md` or doesn't support DCR.*

For providers that don't ship a built-in factory (Auth0, Clerk, Keycloak, Supabase, WorkOS, Better Auth), use `oauthCustomProvider`:

```typescript
import { oauthCustomProvider } from "mcp-use/oauth";
import { jwtVerify, createRemoteJWKSet } from "jose";

const issuer = "https://auth.example.com";
const jwks = createRemoteJWKSet(new URL(`${issuer}/.well-known/jwks.json`));

const oauth = oauthCustomProvider({
  createTokenVerifier: (resource) => async (token) => {
    const { payload } = await jwtVerify(token, jwks, { issuer });
    return { payload: payload as Record<string, unknown> };
  },
  oauthMetadata: {
    issuer,
    authorization_endpoint: `${issuer}/oauth/authorize`,
    token_endpoint: `${issuer}/oauth/token`,
    registration_endpoint: `${issuer}/oauth/register`,
    jwks_uri: `${issuer}/.well-known/jwks.json`,
  },
  mapAuthInfo: (authInfo) => ({
    user: {
      id: authInfo.clientId ?? "unknown",
      email: authInfo.claims?.email as string | undefined,
    },
    payload: authInfo.claims ?? {},
    permissions: [],
  }),
});
```

## Required Options

### createTokenVerifier

A factory receiving the resolved MCP resource URL and returning an async token verifier:

```typescript
createTokenVerifier: (resource: URL) => async (token: string) => {
  // Verify token (JWKS, HS256, introspection, etc.)
  // Return { payload: { ...verified claims } }
  return { payload };
}
```

The `resource` parameter is the MCP server's canonical endpoint URL. Use it if you need to validate audience (`aud` claim).

### oauthMetadata

RFC 8414 authorization-server metadata. Clients discover these endpoints for registration and authorization:

```typescript
{
  issuer: "https://auth.example.com",
  authorization_endpoint: "...",
  token_endpoint: "...",
  registration_endpoint: "...",  // DCR endpoint
  jwks_uri: "...",
}
```

All four fields are required.

### mapAuthInfo

Maps verified SDK `AuthInfo` (the token payload) into application user type:

```typescript
mapAuthInfo: (authInfo: OAuthAuthInfo) => ({
  user: {                  // Application user type
    id: string,
    email?: string,
    // ... other fields
  },
  payload: Record<string, unknown>,  // Verified claims (passthrough usually)
  permissions: string[],   // Extracted or mapped permissions
})
```

## Inherited Options

Like all providers, custom provider inherits:

```typescript
oauthCustomProvider({
  // ... above required fields ...
  resource?: URL | string,           // Full MCP endpoint (overrides inference)
  requiredScopes?: readonly string[], // Scopes required by bearer gate
  scopesSupported?: readonly string[], // Scopes advertised in metadata
  resourceName?: string,              // Display name for metadata
  serviceDocumentationUrl?: URL,      // Documentation link
})
```

## Token Verification Examples

### JWKS (RSA/ECDSA)

```typescript
import { jwtVerify, createRemoteJWKSet } from "jose";

const jwks = createRemoteJWKSet(new URL("https://auth.example.com/.well-known/jwks.json"));
createTokenVerifier: (resource) => async (token) => {
  const { payload } = await jwtVerify(token, jwks, { issuer: "https://auth.example.com" });
  return { payload: payload as Record<string, unknown> };
}
```

### Symmetric (HS256)

```typescript
import { jwtVerify } from "jose";
const secret = new TextEncoder().encode(process.env.AUTH_SECRET);

createTokenVerifier: (resource) => async (token) => {
  const { payload } = await jwtVerify(token, secret);
  return { payload: payload as Record<string, unknown> };
}
```

### Token Introspection

```typescript
createTokenVerifier: (resource) => async (token) => {
  const res = await fetch("https://auth.example.com/oauth/introspect", {
    method: "POST",
    body: new URLSearchParams({ token, client_id: "...", client_secret: "..." }),
  });
  const data = await res.json();
  if (!data.active) throw new Error("Token invalid");
  return { payload: data };
}
```

## User Type

Define your own:

```typescript
type CustomUser = {
  id: string;
  email?: string;
  roles?: string[];
  organizationId?: string;
};
```

Returned from `mapAuthInfo()`, it populates `ctx.auth.user` for all callbacks.
