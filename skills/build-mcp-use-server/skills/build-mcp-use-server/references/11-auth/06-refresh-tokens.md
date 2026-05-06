# Refresh Tokens

Refresh is a client/provider concern. The mcp-use server does not expose a refresh-token callback, token store, or session-extension API; it verifies whatever bearer token arrives on each `/mcp/*` request.

## What the server does

On every authenticated MCP request, mcp-use:

1. Reads `Authorization: Bearer <token>`.
2. Calls the configured provider's `verifyToken(token)`.
3. Builds `ctx.auth` from the verified payload.
4. Returns `401` with `WWW-Authenticate` when the token is missing or invalid.

The server cannot tell whether a valid access token came from the original authorization-code exchange or a refresh-token exchange. Tool handlers just see the current token in `ctx.auth.accessToken`.

## What providers advertise

Provider factories expose supported grants through `getGrantTypesSupported()`. In `mcp-use@1.26.0`, built-in auth providers advertise `refresh_token` support:

| Provider | Default refresh-related settings |
|---|---|
| Auth0 | `grantTypesSupported` includes `refresh_token`; default scopes include `offline_access` |
| WorkOS | `grantTypesSupported` includes `refresh_token`; default scopes include `offline_access` |
| Keycloak | `grantTypesSupported` includes `refresh_token`; default scopes include `offline_access` |
| Better Auth | `grantTypesSupported` includes `refresh_token`; default scopes include `offline_access` |
| Supabase | `grantTypesSupported` includes `refresh_token`; default scopes are minimal |
| Custom | Defaults to `['authorization_code', 'refresh_token']` unless overridden |
| OAuth Proxy | Defaults to `['authorization_code', 'refresh_token']` unless `grantTypes` is set |

Advertising a grant does not force the upstream to issue a `refresh_token`. The upstream provider still decides based on its policy, requested scopes, consent, and client registration.

## How to enable issuance

| Provider | What to configure upstream |
|---|---|
| Auth0 | Request/advertise `offline_access`; configure the API and tenant policy to allow refresh tokens |
| WorkOS | Use the default `offline_access` scope unless your app has a stricter scope list |
| Keycloak | Include `offline_access`; ensure realm/client policy allows refresh-token issuance |
| Better Auth | Configure the OAuth Provider plugin and consent flow to allow refresh grants |
| Supabase | Follow Supabase Auth policy for refresh-token lifetime and rotation |
| Google through `oauthProxy()` | Use provider-specific authorize params such as `access_type=offline` when needed |
| GitHub OAuth App through `oauthProxy()` | Treat access tokens as non-refreshable unless you are using a GitHub flow that issues refresh tokens |

## Client behavior

mcp-use's browser OAuth provider stores OAuth tokens and implements the MCP SDK OAuth client-provider contract. If refresh fails or tokens are revoked, the client must clear invalid credentials and run the authorization flow again.

For custom clients, implement refresh against the authorization server's `token_endpoint` using the standard `grant_type=refresh_token` request. Do not add refresh-specific options to `MCPServer` or server provider configs; they do not exist in `mcp-use@1.26.0`.

## Rotation and persistence

Many providers rotate `refresh_token` on use. A client that receives a replacement refresh token must persist it before the next refresh attempt. The MCP server has no copy of the refresh token and cannot recover from client-side token-store loss.

## Cross-references

- Browser flow: `05-browser-oauth-flow.md`
- Scopes: `07-scopes-supported-config.md`
- Debugging refresh failures: `08-debugging-checklist.md`
