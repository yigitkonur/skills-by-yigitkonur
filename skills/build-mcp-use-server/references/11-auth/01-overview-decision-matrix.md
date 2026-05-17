# Auth — Overview & Decision Matrix

mcp-use exposes three auth modes. Pick one before writing any provider code.

## Modes

| Mode | When | Server holds creds? | Discovery |
|---|---|---|---|
| **None** | Internal/stdio servers; trusted networks | n/a | No `/.well-known/*` |
| **DCR-direct (built-in providers)** | Provider supports Dynamic Client Registration | No — clients register upstream | Passthrough metadata |
| **OAuth Proxy (`oauthProxy`)** | Provider has no DCR (Google, GitHub, Okta, Azure AD) | Yes — `clientId` + `clientSecret` | Server-issued, mediated token exchange |

## Decision matrix

Read top-down; pick the first row that matches your provider.

| If your provider… | …use mode | …use factory |
|---|---|---|
| Is Auth0 with Early Access DCR enabled | DCR | `oauthAuth0Provider()` |
| Is WorkOS AuthKit | DCR | `oauthWorkOSProvider()` |
| Is Keycloak with anonymous DCR or Initial Access Tokens | DCR | `oauthKeycloakProvider()` |
| Is Supabase with OAuth 2.1 server enabled | DCR | `oauthSupabaseProvider()` |
| Is self-hosted via Better Auth's OAuth Provider plugin | DCR | `oauthBetterAuthProvider()` |
| Is any other DCR-capable OIDC IdP | DCR | `oauthCustomProvider()` |
| Is Google, GitHub, Okta, Azure AD, or any non-DCR IdP | Proxy | `oauthProxy()` |
| Is Auth0 Regular Web App (no DCR) | Proxy | `oauthProxy()` |
| Mints opaque (non-JWT) tokens | Proxy or Custom | `oauthProxy()` with custom `verifyToken` |

## What you get when OAuth is configured

- `GET /.well-known/oauth-authorization-server` — discovery (passthrough or server-issued)
- `GET /.well-known/openid-configuration` — OIDC discovery
- `GET /.well-known/oauth-protected-resource` — resource metadata
- `GET /.well-known/oauth-protected-resource/mcp` — scoped resource metadata for `/mcp`
- `GET /authorize`, `POST /token` — only in proxy mode
- All `/mcp/*` requests require `Authorization: Bearer <token>`
- `ctx.auth` is populated on every tool callback — see `03-ctx-auth-object.md`

## Pick the mode in three questions

1. **Does the provider expose `registration_endpoint` in its `.well-known` metadata?** Yes → DCR. No → Proxy.
2. **Are you fine holding `clientSecret` on the server?** Required for Proxy. Not needed for DCR.
3. **Are tokens JWTs you can verify locally with JWKS?** Yes → use `jwksVerifier()`. No → write a custom `verifyToken`.

## Architectural shift

Built-in providers default to **DCR-direct** since v1.25.0. Pre-v1.25.0 servers held shared client credentials in the proxy. If you are migrating, see `02-dcr-vs-proxy-mode.md` and `../28-migration/05-dcr-vs-proxy-mode-shift.md`.

## Cross-references

- Provider configs: `providers/01-auth0.md` through `providers/07-custom.md`
- `ctx.auth` shape and tool guards: `03-ctx-auth-object.md`, `04-permission-guards.md`
- Refresh, scopes, debugging: `06-refresh-tokens.md`, `07-scopes-supported-config.md`, `08-debugging-checklist.md`
- Production hardening (CORS, HTTPS, secret handling): `../24-production/04-error-strategy.md`, `../26-anti-patterns/05-security-and-cors.md`
- Common OAuth/Supabase failures: `../27-troubleshooting/03-oauth-and-supabase-issues.md`

**Canonical doc:** https://manufact.com/docs/typescript/server/authentication
