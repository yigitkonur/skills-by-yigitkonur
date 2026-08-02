# OAuth Proxy Removed in v2

*Read this if you used `oauthProxy` in v1 or need fixed-client brokering.*

## What Changed

v1's `oauthProxy` factory — used for providers that only support pre-registered (fixed-client) credentials — **is not exported in v2**. There is no native OAuth proxy in the SDK.

## Why

v2 standardizes on **Dynamic Client Registration (DCR)**: the MCP server itself registers as an OAuth client with upstream providers at startup. All six built-in providers (Clerk, Auth0, Keycloak, Supabase, WorkOS, Better Auth) support DCR; clients register directly with the provider and the MCP server only verifies tokens.

## For Fixed-Client Providers

If your provider (e.g., legacy GitHub OAuth, Google) only supports a pre-registered `clientId` and `clientSecret`, do one of:

1. **Migrate to a provider that supports DCR** — use `oauthAuth0Provider`, `oauthKeycloakProvider`, etc.
2. **Implement an external authorization server** — run a separate OAuth broker service that handles registration, authorization, and token issuance. The MCP server verifies tokens from that broker using `oauthCustomProvider`.
3. **Use `oauthCustomProvider` with your provider's JWKS** — if your provider exposes a JWKS endpoint and allows JWT verification without registration:
   ```typescript
   const oauth = oauthCustomProvider({
     createTokenVerifier: (resource) => async (token) => {
       const { payload } = await jwtVerify(token, jwks);
       return { payload: payload as Record<string, unknown> };
     },
     oauthMetadata: { /* your provider's metadata */ },
     mapAuthInfo: (authInfo) => ({
       user: { id: authInfo.clientId ?? "unknown", email: authInfo.claims?.email },
       payload: authInfo.claims ?? {},
       permissions: [],
     }),
   });
   ```

## Migration Path

See `references/28-migration/05-v1-to-v2-auth.md` for the full v1→v2 OAuth migration guide.

## External Broker Example

If you need a broker:

1. Deploy a service that owns registration, authorization, consent, and token issuance (e.g., Better Auth, Hydra, custom OAuth server)
2. Clients register with the broker
3. The broker calls your upstream provider
4. The MCP server verifies tokens from the broker's JWKS endpoint

The MCP server's job is unchanged: verify bearer tokens and expose protected endpoints. The broker handles everything upstream.
