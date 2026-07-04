# OAuth Proxy

Use `oauthProxy()` when the upstream provider does **not** support Dynamic Client Registration. The MCP server holds pre-registered client credentials and mediates the OAuth flow.

## When to reach for the proxy

All of these must be true:

- Provider requires registering an app in a dashboard, returning fixed `clientId` / `clientSecret`.
- Provider does **not** expose `registration_endpoint` in its OAuth metadata.
- You are willing to hold the client secret on the server.

Common targets: **Google, GitHub, Okta, Azure AD (Microsoft Entra ID), Auth0 Regular Web Apps.**

## How it works

```
MCP Client ──(1) POST /register                  ─▶ MCP Server   (returns server's clientId)
MCP Client ──(2) GET  /authorize                 ─▶ MCP Server   ──▶ Upstream IdP (PKCE)
MCP Client ──(3) POST /token                     ─▶ MCP Server   ──▶ Upstream IdP
                                                    (server injects clientId + clientSecret)
MCP Client ──(4) MCP request + Bearer <token>    ─▶ MCP Server   (verifyToken runs)
```

Server holds the credentials. Tokens are passthrough — the proxy does not mint its own.

## Configuration

```ts
oauthProxy({
  // Required: upstream endpoints
  authEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
  tokenEndpoint: 'https://oauth2.googleapis.com/token',
  issuer: 'https://accounts.google.com',

  // Required: pre-registered credentials (clientSecret optional for public clients)
  clientId: process.env.CLIENT_ID!,
  clientSecret: process.env.CLIENT_SECRET,

  // Required: token verifier — see jwksVerifier helper below
  verifyToken: jwksVerifier({ jwksUrl: '...', issuer: '...', audience: '...' }),

  // Optional
  scopes: ['openid', 'email', 'profile'],                              // requested scopes
  grantTypes: ['authorization_code', 'refresh_token'],
  extraAuthorizeParams: { access_type: 'offline', prompt: 'consent' }, // forwarded to upstream
  getUserInfo: (payload) => ({ userId: payload.sub as string, /* ... */ }),
})
```

## `jwksVerifier` helper

For JWT providers, `jwksVerifier` does signature + issuer + (optional) audience checks against a remote JWKS:

```ts
verifyToken: jwksVerifier({
  jwksUrl: '...',
  issuer: '...',
  audience: '...',  // optional but recommended
})
```

For non-JWT providers, write a custom `verifyToken` (see GitHub below).

## Provider configs

### Google

```ts
oauthProxy({
  authEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
  tokenEndpoint: 'https://oauth2.googleapis.com/token',
  issuer: 'https://accounts.google.com',
  clientId: process.env.GOOGLE_CLIENT_ID!,
  clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
  scopes: ['openid', 'email', 'profile'],
  extraAuthorizeParams: { access_type: 'offline' },  // required for refresh tokens
  verifyToken: jwksVerifier({
    jwksUrl: 'https://www.googleapis.com/oauth2/v3/certs',
    issuer: 'https://accounts.google.com',
    audience: process.env.GOOGLE_CLIENT_ID!,
  }),
})
```

### Okta / Azure AD

```ts
// Okta
const oktaDomain = process.env.OKTA_DOMAIN!
oauthProxy({
  authEndpoint: `${oktaDomain}/oauth2/default/v1/authorize`,
  tokenEndpoint: `${oktaDomain}/oauth2/default/v1/token`,
  issuer: `${oktaDomain}/oauth2/default`,
  clientId: process.env.OKTA_CLIENT_ID!,
  clientSecret: process.env.OKTA_CLIENT_SECRET,
  scopes: ['openid', 'email', 'profile'],
  verifyToken: jwksVerifier({
    jwksUrl: `${oktaDomain}/oauth2/default/v1/keys`,
    issuer: `${oktaDomain}/oauth2/default`,
  }),
})

// Azure AD / Microsoft Entra ID
const tenantId = process.env.AZURE_TENANT_ID!
const base = `https://login.microsoftonline.com/${tenantId}/v2.0`
oauthProxy({
  authEndpoint: `${base}/oauth2/v2.0/authorize`,
  tokenEndpoint: `${base}/oauth2/v2.0/token`,
  issuer: base,
  clientId: process.env.AZURE_CLIENT_ID!,
  clientSecret: process.env.AZURE_CLIENT_SECRET,
  scopes: ['openid', 'profile', 'email'],
  verifyToken: jwksVerifier({
    jwksUrl: 'https://login.microsoftonline.com/common/discovery/v2.0/keys',
    issuer: base,
    audience: process.env.AZURE_CLIENT_ID!,
  }),
})
```

### Auth0 Regular Web App (no DCR)

When your Auth0 tenant doesn't have Early Access DCR:

```ts
const domain = process.env.AUTH0_DOMAIN!
const audience = process.env.AUTH0_AUDIENCE!
oauthProxy({
  authEndpoint: `https://${domain}/authorize`,
  tokenEndpoint: `https://${domain}/oauth/token`,
  issuer: `https://${domain}/`,
  clientId: process.env.AUTH0_CLIENT_ID!,
  clientSecret: process.env.AUTH0_CLIENT_SECRET,
  scopes: ['openid', 'email', 'profile'],
  extraAuthorizeParams: { audience },
  verifyToken: jwksVerifier({
    jwksUrl: `https://${domain}/.well-known/jwks.json`,
    issuer: `https://${domain}/`,
    audience,
  }),
})
```

### GitHub (opaque tokens)

GitHub does not issue JWTs. Verify by calling the GitHub API:

```ts
oauthProxy({
  authEndpoint: 'https://github.com/login/oauth/authorize',
  tokenEndpoint: 'https://github.com/login/oauth/access_token',
  issuer: 'https://github.com',
  clientId: process.env.GITHUB_CLIENT_ID!,
  clientSecret: process.env.GITHUB_CLIENT_SECRET!,
  scopes: ['read:user', 'user:email'],

  async verifyToken(token) {
    const res = await fetch('https://api.github.com/user', {
      headers: {
        Authorization: `Bearer ${token}`,
        'User-Agent': 'my-mcp-server',
      },
    })
    if (!res.ok) throw new Error('Invalid GitHub token')
    const user = await res.json()
    return { payload: { sub: String(user.id), ...user } }
  },

  getUserInfo(payload) {
    return {
      userId: payload.sub as string,
      username: payload.login as string | undefined,
      name: payload.name as string | undefined,
      email: payload.email as string | undefined,
      picture: payload.avatar_url as string | undefined,
    }
  },
})
```

GitHub OAuth Apps do not issue refresh tokens. Use a GitHub App if refresh is required.

## Credential env vars

mcp-use does not read fixed proxy env vars. Pass `clientId` and `clientSecret` explicitly from whichever names fit the provider (`CLIENT_ID`, `CLIENT_SECRET`, `GOOGLE_CLIENT_ID`, `OKTA_CLIENT_ID`, etc.).

## Anti-patterns

- Don't ship `clientSecret` to the client — the proxy keeps it server-side. Public-client mode (`clientSecret: undefined`) is allowed only when the upstream supports PKCE without a secret.
- Don't skip `verifyToken` — without it, any bearer token is accepted.
- Don't use the proxy when DCR is available — it adds a credential management surface for no benefit.

## Cross-references

- Decision matrix: `../01-overview-decision-matrix.md`
- DCR vs Proxy: `../02-dcr-vs-proxy-mode.md`
- Custom verifier patterns: `07-custom.md`
- Canonical: https://manufact.com/docs/typescript/server/authentication/providers/oauth-proxy
- Runnable Auth0 proxy example: https://github.com/mcp-use/mcp-use/tree/main/libraries/typescript/packages/mcp-use/examples/server/oauth/auth0-proxy
