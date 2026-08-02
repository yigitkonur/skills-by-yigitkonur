# OAuth Issues

*Read this when OAuth discovery, bearer verification, provider mapping, scopes, permissions, or user identity fails in v2.*

v2 acts as an OAuth resource server. It advertises metadata and verifies bearer tokens. It does not mint tokens or provide native fixed-client OAuth brokering.

## Start with the failure boundary

| Boundary | Symptom | Check |
|---|---|---|
| Discovery | Client cannot locate authorization, token, registration, or JWKS endpoints. | Fetch the well-known metadata and verify every advertised URL. |
| Authorization server | Browser flow or DCR fails before returning a token. | Confirm the upstream provider supports DCR and the client follows its metadata. |
| Bearer gate | MCP request returns 401 before callback. | Inspect token presence, expiry, issuer, audience/resource, signature, and required scopes. |
| Provider mapping | Callback runs, but user fields or permissions are wrong. | Inspect the provider's native user type and mapping. |
| Downstream API | MCP auth succeeds, but an upstream API rejects the request. | Confirm the upstream expects the same access token and audience. |

## Provider imports fail

Provider factories are not root exports:

```typescript
import { MCPServer } from "mcp-use";
import { oauthAuth0Provider } from "mcp-use/oauth/auth0";
import { oauthSupabaseProvider } from "mcp-use/oauth/supabase";
```

Use the exact subpaths in `references/11-auth/01-overview.md`.

## Requests return 401 before tool code

OAuth-protected MCP routes reject unauthenticated requests before callbacks run. Check in this order:

1. The client sends `Authorization: Bearer <token>` to the MCP endpoint.
2. The token is not expired.
3. Its issuer matches the configured provider.
4. Its audience/resource matches the MCP resource when enforced.
5. Its scopes include every configured `requiredScopes` value.
6. The token uses the signature algorithm and key source expected by the provider.

Use a real MCP request or Inspector auth flow, not a plain browser navigation. See `references/11-auth/06-debugging-checklist.md`.

## `ctx.auth.user.userId` is undefined

`userId` is a v1 field path. Built-in v2 provider users expose a stable `id`:

```typescript
const userId = ctx.auth.user.id;
```

Optional fields vary by provider. Do not assume every user has the same email, role, organization, or session fields. See `references/11-auth/03-ctx-auth-and-user-context.md`.

## Scopes and permissions disagree

`ctx.auth.scopes` contains OAuth scopes granted to the access token. `ctx.auth.permissions` contains provider-normalized permissions. They are not interchangeable.

Use scopes for protocol/API grants and permissions for application authorization only when the provider mapping defines them. Do not authorize from `ctx.client.user()`; it is unverified client metadata.

## Built-in provider configuration fails

Verify the provider-specific required values:

| Provider | Required source |
|---|---|
| Clerk | `frontendApiUrl` |
| Auth0 | `domain` |
| WorkOS | `subdomain` |
| Supabase | `projectId` or `supabaseUrl` |
| Keycloak | `serverUrl` and `realm` |
| Better Auth | `authURL`, including its base path |

A malformed issuer/base URL usually appears as discovery, JWKS, issuer, or signature failure. Use the matching file in `references/11-auth/providers/`.

## Supabase verification fails

Check four values together:

1. `supabaseUrl` points to the token-issuing project; it overrides `projectId` when both are present.
2. The token audience matches the configured audience; the provider default is `authenticated`.
3. ES256 tokens use project JWKS; omit `jwtSecret`.
4. Legacy HS256 tokens require the matching `jwtSecret` explicitly.

Do not add an HS256 secret to fix an ES256/JWKS failure. See `references/11-auth/providers/04-supabase.md`.

## Custom provider fails

`oauthCustomProvider` requires all three boundaries:

```typescript
import { oauthCustomProvider } from "mcp-use/oauth";

const oauth = oauthCustomProvider({
  createTokenVerifier: (resource) => async (token) => {
    const payload = await verifyForResource(token, resource);
    return { payload };
  },
  oauthMetadata: {
    issuer: "https://auth.example.com",
    authorization_endpoint: "https://auth.example.com/oauth/authorize",
    token_endpoint: "https://auth.example.com/oauth/token",
    registration_endpoint: "https://auth.example.com/oauth/register",
    jwks_uri: "https://auth.example.com/.well-known/jwks.json",
  },
  mapAuthInfo: (authInfo) => ({
    user: { id: String(authInfo.claims?.sub) },
    payload: authInfo.claims ?? {},
    permissions: [],
  }),
});
```

The verifier must validate the token for the resolved MCP resource. The metadata must describe the same issuer that produced the token. The mapper must return a non-empty stable user identity and normalized permissions. See `references/11-auth/05-custom-provider-oauthcustomprovider.md`.

## OAuth Proxy import or fixed-client flow fails

`oauthProxy`, `mountOAuthProxy`, and related native proxy helpers were removed. Do not recreate their endpoints inside the MCP server as an undocumented workaround.

Use one of these paths:

- a built-in provider whose authorization server supports DCR;
- a custom DCR-capable provider via `oauthCustomProvider`; or
- an external authorization-server/broker for fixed-client upstreams, with the MCP server verifying its tokens.

See `references/11-auth/07-oauth-proxy-removed.md`.

## Safe verification pattern

```typescript
export const whoami = server.tool(
  {
    name: "whoami",
    description: "Return the verified user ID and granted permissions.",
    outputSchema: z.object({
      id: z.string(),
      permissions: z.array(z.string()),
    }),
  },
  async (_input, ctx) => ({
    content: [{ type: "text", text: `Authenticated as ${ctx.auth.user.id}.` }],
    structuredContent: {
      id: ctx.auth.user.id,
      permissions: ctx.auth.permissions,
    },
  }),
);
```

Never return `ctx.auth.accessToken`, full token claims, or authorization headers to the model.