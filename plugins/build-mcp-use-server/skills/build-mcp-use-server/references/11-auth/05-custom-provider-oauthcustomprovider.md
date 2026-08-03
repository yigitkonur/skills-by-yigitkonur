# Custom Provider: oauthCustomProvider

*Read this when your identity provider is not listed in `references/11-auth/01-overview.md` or doesn't support DCR.*

Use `oauthCustomProvider` when your authorization server supports Dynamic Client Registration (DCR) but mcp-use has no built-in adapter for it. All six built-in factories (`oauthClerkProvider`, `oauthAuth0Provider`, `oauthWorkOSProvider`, `oauthSupabaseProvider`, `oauthKeycloakProvider`, `oauthBetterAuthProvider`) are themselves thin wrappers around `oauthCustomProvider` — reach for a built-in factory first if your provider is one of those six; use `oauthCustomProvider` directly only for a different DCR-capable authorization server.

```typescript
import { MCPServer } from "mcp-use";
import {
  oauthCustomProvider,
  type OAuthAuthInfo,
  type OAuthMetadata,
} from "mcp-use/oauth";
import { createRemoteJWKSet, jwtVerify } from "jose";

const issuer = "https://auth.example.com";
const jwks = createRemoteJWKSet(new URL(`${issuer}/.well-known/jwks.json`));

const oauthMetadata = {
  issuer,
  authorization_endpoint: `${issuer}/oauth/authorize`,
  token_endpoint: `${issuer}/oauth/token`,
  registration_endpoint: `${issuer}/oauth/register`,
  response_types_supported: ["code"],
  grant_types_supported: ["authorization_code", "refresh_token"],
  code_challenge_methods_supported: ["S256"],
} satisfies OAuthMetadata;

type AppUser = {
  id: string;
  email?: string;
  organizationId?: string;
};

const server = new MCPServer({
  name: "custom-auth-server",
  version: "1.0.0",
  oauth: oauthCustomProvider<AppUser>({
    oauthMetadata,

    createTokenVerifier(resource) {
      return {
        async verifyAccessToken(token) {
          const { payload } = await jwtVerify(token, jwks, {
            issuer,
            audience: resource.href,
          });

          if (!payload.sub || !payload.exp) {
            throw new Error("Token is missing sub or exp");
          }

          const scopes =
            typeof payload.scope === "string"
              ? payload.scope.split(/\s+/).filter(Boolean)
              : [];

          return {
            token,
            clientId:
              typeof payload.client_id === "string"
                ? payload.client_id
                : typeof payload.azp === "string"
                  ? payload.azp
                  : "",
            scopes,
            expiresAt: payload.exp,
            resource,
            extra: { payload: payload as Record<string, unknown> },
          };
        },
      };
    },

    mapAuthInfo(authInfo: OAuthAuthInfo) {
      const payload = authInfo.extra?.payload as Record<string, unknown>;
      if (typeof payload.sub !== "string") {
        throw new Error("Verified token is missing sub");
      }

      return {
        user: {
          id: payload.sub,
          email: typeof payload.email === "string" ? payload.email : undefined,
          organizationId:
            typeof payload.organization_id === "string"
              ? payload.organization_id
              : undefined,
        },
        payload,
        permissions: Array.isArray(payload.permissions)
          ? payload.permissions.filter(
              (value): value is string => typeof value === "string",
            )
          : [],
      };
    },
  }),
});

export default server;
```

## Required Options

### createTokenVerifier

A factory receiving the resolved MCP resource URL and returning an `OAuthTokenVerifier` — an object with a `verifyAccessToken` method, **not** a bare function:

```typescript
createTokenVerifier(resource: URL): OAuthTokenVerifier {
  return {
    async verifyAccessToken(token: string): Promise<AuthInfo> {
      // Verify token (JWKS, HS256, introspection, etc.)
      // Return the full AuthInfo shape below.
      return {
        token,
        clientId: "",             // client_id/azp claim, or "" if the IdP omits one
        scopes: [],                // string[] parsed from the scope claim
        expiresAt: 0,              // Unix seconds, must be in the future
        resource,                  // echo back the validated resource argument
        extra: { payload },        // verified claims record, read via extra.payload
      };
    },
  };
}
```

`resource` is the MCP server's canonical endpoint URL; validate it as the token's audience (`aud` claim) or bind verification to it another way. The framework runtime-validates the returned `AuthInfo` (`token`, `clientId` as a string, `scopes` as a string array, a future `expiresAt`) and rejects the request with an "invalid token" error if any field is missing or the wrong type — a verifier that returns only `{ payload }` fails this check at request time, not at server startup.

### oauthMetadata

RFC 8414 authorization-server metadata. Clients discover these endpoints for registration and authorization:

```typescript
{
  issuer: "https://auth.example.com",
  authorization_endpoint: "...",
  token_endpoint: "...",
  registration_endpoint: "...",       // DCR endpoint
  response_types_supported: ["code"],
  grant_types_supported: ["authorization_code", "refresh_token"],
  code_challenge_methods_supported: ["S256"],
}
```

Only `issuer` is runtime-validated (must be a secure HTTP(S) URL). The other fields are not enforced by the framework, but clients rely on `authorization_endpoint`, `token_endpoint`, and `registration_endpoint` to complete DCR and the authorization flow — omitting them breaks real clients even though the server will not error. `jwks_uri` is not part of this object; JWKS key retrieval is wired separately inside `createTokenVerifier` (e.g. via `jose`'s `createRemoteJWKSet`).

### mapAuthInfo

Maps verified `OAuthAuthInfo` (the SDK auth information your `createTokenVerifier` returned) into application user, claims, and permissions. It runs only after the token has been verified, and does not touch `ctx.auth.scopes` — those are copied straight from `AuthInfo.scopes`:

```typescript
mapAuthInfo: (authInfo: OAuthAuthInfo) => {
  const payload = authInfo.extra?.payload as Record<string, unknown>;
  return {
    user: {                  // Application user type
      id: string,
      email?: string,
      // ... other fields
    },
    payload,                 // Verified claims (usually a passthrough)
    permissions: string[],   // Extracted or mapped permissions
  };
}
```

Claims live at `authInfo.extra?.payload`, not `authInfo.claims` — `claims` does not exist on `AuthInfo`.

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

Every verifier below returns the `{ verifyAccessToken }` object shape — never a bare function — and every returned `AuthInfo` must include `token`, `clientId`, `scopes`, `expiresAt`, `resource`, and `extra: { payload }` (trimmed for brevity below; fill in `clientId`/`scopes`/`expiresAt` from verified claims as shown in the full example above).

### JWKS (RSA/ECDSA)

```typescript
import { jwtVerify, createRemoteJWKSet } from "jose";

const jwks = createRemoteJWKSet(new URL("https://auth.example.com/.well-known/jwks.json"));

createTokenVerifier: (resource) => ({
  async verifyAccessToken(token) {
    const { payload } = await jwtVerify(token, jwks, {
      issuer: "https://auth.example.com",
      audience: resource.href,
    });
    // ... build clientId, scopes, expiresAt from payload as in the example above
    return { token, clientId: "", scopes: [], expiresAt: payload.exp!, resource, extra: { payload } };
  },
})
```

### Symmetric (HS256)

```typescript
import { jwtVerify } from "jose";
const secret = new TextEncoder().encode(process.env.AUTH_SECRET);

createTokenVerifier: (resource) => ({
  async verifyAccessToken(token) {
    const { payload } = await jwtVerify(token, secret, { audience: resource.href });
    return { token, clientId: "", scopes: [], expiresAt: payload.exp!, resource, extra: { payload } };
  },
})
```

### Token Introspection

```typescript
createTokenVerifier: (resource) => ({
  async verifyAccessToken(token) {
    const res = await fetch("https://auth.example.com/oauth/introspect", {
      method: "POST",
      body: new URLSearchParams({ token, client_id: "...", client_secret: "..." }),
    });
    const data = await res.json();
    if (!data.active) throw new Error("Token invalid");
    return {
      token,
      clientId: data.client_id ?? "",
      scopes: typeof data.scope === "string" ? data.scope.split(/\s+/).filter(Boolean) : [],
      expiresAt: data.exp,
      resource,
      extra: { payload: data },
    };
  },
})
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
