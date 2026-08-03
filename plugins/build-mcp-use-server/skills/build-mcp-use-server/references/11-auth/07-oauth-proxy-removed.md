# OAuth Proxy Removed in v2

*Read this if you used `oauthProxy` in v1 or need fixed-client brokering.*

## What Changed

v1's `oauthProxy` factory — used for providers that only support pre-registered (fixed-client) credentials — **is not exported in v2**. mcp-use does not provide a server-side OAuth proxy factory, and does not implement authorization, callback, token-exchange, or fixed-client brokering routes. This is a support-boundary decision, not a missing feature scheduled for a later release.

## Why

v2 standardizes on providers whose authorization server supports **Dynamic Client Registration (DCR)**: the MCP client registers itself directly with the upstream authorization server, and mcp-use acts only as the protected resource server (it verifies bearer tokens, it never brokers registration, consent, or token exchange). If your identity provider supports DCR, use a built-in provider (`oauthClerkProvider`, `oauthAuth0Provider`, `oauthWorkOSProvider`, `oauthSupabaseProvider`, `oauthKeycloakProvider`, `oauthBetterAuthProvider`) or `oauthCustomProvider` — see `01-overview.md` and `05-custom-provider-oauthcustomprovider.md`.

## For Fixed-Client Providers

If your provider (e.g., legacy GitHub OAuth, Google) gives you only a fixed `clientId` and `clientSecret` and no DCR support, deploy a standards-compliant external authorization server or broker (Better Auth, Ory Hydra, a custom OAuth server, …) that:

1. **Publishes OAuth authorization-server metadata**, including a registration endpoint.
2. **Registers MCP clients and enforces redirect URI and PKCE requirements.**
3. **Performs the upstream authorization and token exchange without exposing the fixed secret** to MCP clients.
4. **Issues or validates tokens bound to the MCP resource.**

Point `oauthCustomProvider` at that external authorization server's issuer/JWKS and implement resource-bound token verification — mcp-use has no server-side fixed-client brokering equivalent; the broker is a separate deployed service, not a mcp-use config option.

```typescript
import { oauthCustomProvider, type OAuthAuthInfo } from "mcp-use/oauth";
import { createRemoteJWKSet, jwtVerify } from "jose";

const issuer = "https://broker.example.com";
const jwks = createRemoteJWKSet(new URL(`${issuer}/.well-known/jwks.json`));

const oauth = oauthCustomProvider({
  createTokenVerifier: (resource) => ({
    async verifyAccessToken(token) {
      const { payload } = await jwtVerify(token, jwks, { issuer, audience: resource.href });
      if (!payload.sub || !payload.exp) throw new Error("Token missing sub or exp");
      return {
        token,
        clientId: typeof payload.client_id === "string" ? payload.client_id : "",
        scopes: typeof payload.scope === "string" ? payload.scope.split(/\s+/).filter(Boolean) : [],
        expiresAt: payload.exp,
        resource,
        extra: { payload: payload as Record<string, unknown> },
      };
    },
  }),
  oauthMetadata: {
    issuer,
    authorization_endpoint: `${issuer}/oauth/authorize`,
    token_endpoint: `${issuer}/oauth/token`,
    registration_endpoint: `${issuer}/oauth/register`,
    response_types_supported: ["code"],
    grant_types_supported: ["authorization_code", "refresh_token"],
    code_challenge_methods_supported: ["S256"],
  },
  mapAuthInfo: (authInfo: OAuthAuthInfo) => {
    const payload = authInfo.extra?.payload as Record<string, unknown>;
    return {
      user: { id: payload.sub as string, email: typeof payload.email === "string" ? payload.email : undefined },
      payload,
      permissions: [],
    };
  },
});
```

See `05-custom-provider-oauthcustomprovider.md` for the full `createTokenVerifier`/`mapAuthInfo` contract this example relies on.

## Migration Path

See `references/28-migration/05-v1-to-v2-auth.md` for the full v1→v2 OAuth migration guide.
