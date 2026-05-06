# DCR vs OAuth Proxy

Two structurally different auth flows. Pick the right one for your provider — they do not behave the same.

## DCR-direct (preferred)

Clients register and authenticate **directly with the upstream provider**. The MCP server only verifies bearer tokens.

```
MCP Client ──(1) GET /.well-known/oauth-authorization-server ─▶ MCP Server (passthrough)
MCP Client ──(2) POST <upstream registration_endpoint>       ─▶ Upstream IdP   (DCR)
MCP Client ──(3) GET  <upstream authorization_endpoint>      ─▶ Upstream IdP   (PKCE)
MCP Client ──(4) POST <upstream token_endpoint>              ─▶ Upstream IdP
MCP Client ──(5) MCP request + Bearer <token>                ─▶ MCP Server    (verifies JWT)
```

**Server holds:** nothing client-specific. No `clientId`, no `clientSecret`.
**Server exposes:** `.well-known/*` metadata that passes through the upstream's `registration_endpoint`, `authorization_endpoint`, `token_endpoint`.
**Verification:** local JWT signature check via JWKS.

## OAuth Proxy

The MCP server **mediates** the OAuth flow with pre-registered credentials.

```
MCP Client ──(1) POST /register                  ─▶ MCP Server (returns server's clientId)
MCP Client ──(2) GET  <upstream authorize>       ─▶ Upstream IdP (PKCE)
MCP Client ──(3) POST /token                     ─▶ MCP Server ─▶ Upstream IdP
                                                    (server injects clientId + clientSecret)
MCP Client ──(4) MCP request + Bearer <token>    ─▶ MCP Server (verifies via verifyToken)
```

**Server holds:** `clientId` and `clientSecret` from the upstream provider's dashboard.
**Server exposes:** `/register`, `/authorize`, `/token` endpoints that wrap the upstream.
**Verification:** custom `verifyToken` (use `jwksVerifier()` for JWTs, write your own for opaque tokens).

## When each mode is required

| Provider | Why DCR or Proxy |
|---|---|
| WorkOS AuthKit | DCR — first-class support |
| Keycloak | DCR — supports anonymous or Initial-Access-Token DCR |
| Supabase (OAuth 2.1 server) | DCR — provider-issued tokens, JWKS exposed |
| Better Auth | DCR — Better Auth's plugin issues JWTs |
| Auth0 (Early Access DCR) | DCR — opt-in feature |
| Google, GitHub, Okta, Azure AD | Proxy — no `registration_endpoint` |
| Auth0 Regular Web App | Proxy — no DCR on classic apps |

## Why DCR is preferred

- No shared secret on the server. Lower blast radius if the server is compromised.
- Each MCP client gets its own `client_id`. Per-client revocation is possible upstream.
- Token verification is local (JWKS) — no proxied request to upstream on every tool call.
- `.well-known` is a passthrough — provider rotations propagate without server changes.

## Architectural shift in v1.25.0

Pre-v1.25.0, all built-in providers defaulted to a server-mediated proxy. v1.25.0 made DCR-direct the default for built-in providers; a single shared client credential is no longer held by the server.

Migration impact:
- Servers configured with `clientId` + `clientSecret` env vars for built-in providers (other than the dedicated proxy) must remove those vars and enable DCR upstream.
- Clients that previously authenticated against the server's `/authorize` now authenticate against the upstream's authorize URL discovered via `.well-known` passthrough.
- `oauthProxy()` is now the explicit escape hatch — see `providers/06-oauth-proxy.md`.

Full migration steps live in `../28-migration/05-dcr-vs-proxy-mode-shift.md` — do not duplicate the content here. Cross-link only.

## Picking the right mode

Pseudo-decision:

```
upstream has registration_endpoint?
├── yes → DCR — pick a built-in provider or oauthCustomProvider
└── no  → Proxy — oauthProxy with clientId/clientSecret + verifyToken
```

If your provider straddles both (Auth0), default to DCR if the feature is enabled; otherwise Proxy.
