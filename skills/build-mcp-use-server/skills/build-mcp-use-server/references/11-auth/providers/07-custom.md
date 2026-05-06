# Custom Provider

Use `oauthCustomProvider()` for any DCR-capable OIDC provider not covered by a built-in factory. You write the `verifyToken` function and the discovery metadata.

## When to write a custom provider

| Reason | Use custom provider? |
|---|---|
| Provider supports DCR but isn't built-in | Yes |
| You need fine-grained control over JWT verification (custom claims, extra checks) | Yes |
| Provider exposes JWKS at a non-standard path | Yes |
| Provider issues opaque (non-JWT) tokens | If it also lacks DCR, use `oauthProxy` with a custom `verifyToken`; otherwise keep custom and call the provider API in `verifyToken` |
| You want to run a self-hosted IdP | Use `oauthBetterAuthProvider` instead |

## Minimal config

```ts
import { MCPServer, oauthCustomProvider } from 'mcp-use/server'
import { jwtVerify, createRemoteJWKSet } from 'jose'

const JWKS = createRemoteJWKSet(
  new URL('https://auth.example.com/.well-known/jwks.json')
)

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthCustomProvider({
    issuer: 'https://auth.example.com',
    authEndpoint: 'https://auth.example.com/oauth/authorize',
    tokenEndpoint: 'https://auth.example.com/oauth/token',

    async verifyToken(token: string) {
      const { payload } = await jwtVerify(token, JWKS, {
        issuer: 'https://auth.example.com',
        audience: 'your-api-identifier',
      })
      return { payload: payload as Record<string, unknown> }
    },
  }),
})
```

## All options

```ts
oauthCustomProvider({
  // Required
  issuer: 'https://auth.example.com',
  authEndpoint: 'https://auth.example.com/oauth/authorize',
  tokenEndpoint: 'https://auth.example.com/oauth/token',
  async verifyToken(token: string) {
    // must return { payload: Record<string, unknown> }
    const { payload } = await jwtVerify(token, JWKS, { issuer: '...' })
    return { payload: payload as Record<string, unknown> }
  },

  // Optional
  jwksUrl: 'https://auth.example.com/.well-known/jwks.json',  // advertised in discovery
  userInfoEndpoint: 'https://auth.example.com/userinfo',
  scopesSupported: ['openid', 'profile', 'email'],
  grantTypesSupported: ['authorization_code', 'refresh_token'],
  audience: 'your-api-identifier',

  getUserInfo(payload) {
    return {
      userId: payload.sub as string,
      email: payload.email as string | undefined,
      name: payload.name as string | undefined,
      roles: (payload.roles as string[]) ?? [],
    }
  },
})
```

## JWKS-backed verification

The standard pattern — fetch keys, verify signature, check `iss` and `aud`:

```ts
import { jwtVerify, createRemoteJWKSet } from 'jose'

const JWKS = createRemoteJWKSet(
  new URL('https://auth.example.com/.well-known/jwks.json')
)

async verifyToken(token: string) {
  const { payload } = await jwtVerify(token, JWKS, {
    issuer: 'https://auth.example.com',
    audience: 'your-api-identifier',
    algorithms: ['RS256', 'ES256'],
    clockTolerance: 30, // seconds
  })
  return { payload: payload as Record<string, unknown> }
}
```

## Symmetric (HS256) verification

Avoid in production. If the provider uses HS256:

```ts
import { jwtVerify } from 'jose'
const secret = new TextEncoder().encode(process.env.JWT_SECRET!)

async verifyToken(token: string) {
  const { payload } = await jwtVerify(token, secret, { issuer: '...' })
  return { payload: payload as Record<string, unknown> }
}
```

## Custom claim normalization

Use `getUserInfo` to map provider-specific claim shapes onto `UserInfo`:

```ts
getUserInfo(payload) {
  return {
    userId: payload.sub as string,
    email: payload.email as string | undefined,
    name: payload.name as string | undefined,
    // Auth0 namespaced claim
    roles: (payload['https://myapp.com/roles'] as string[]) ?? [],
    // Nested metadata
    permissions: ((payload.app_metadata as any)?.permissions as string[]) ?? [],
  }
}
```

## Multi-issuer trust

To accept tokens from multiple issuers (e.g. a federation):

```ts
import { jwtVerify, createRemoteJWKSet, decodeJwt } from 'jose'

const JWKS_A = createRemoteJWKSet(new URL('https://idp-a.example.com/jwks'))
const JWKS_B = createRemoteJWKSet(new URL('https://idp-b.example.com/jwks'))

async verifyToken(token: string) {
  const decoded = decodeJwt(token)
  const issuer = decoded.iss as string

  if (issuer === 'https://idp-a.example.com') {
    const { payload } = await jwtVerify(token, JWKS_A, { issuer })
    return { payload: payload as Record<string, unknown> }
  }
  if (issuer === 'https://idp-b.example.com') {
    const { payload } = await jwtVerify(token, JWKS_B, { issuer })
    return { payload: payload as Record<string, unknown> }
  }
  throw new Error(`Unknown issuer: ${issuer}`)
}
```

## Anti-patterns

- Don't return the raw verification result — `verifyToken` must return `{ payload: ... }`.
- Don't skip `audience` check — it prevents tokens minted for another resource being accepted.
- Don't catch verification errors silently — let them throw so mcp-use returns 401.
- Don't roll your own signature verification — always use `jose` or an equivalent maintained library.

## Cross-references

- Decision matrix: `../01-overview-decision-matrix.md`
- For non-DCR providers: `06-oauth-proxy.md`
- For self-hosted IdP: `02-better-auth.md`
- Canonical: https://manufact.com/docs/typescript/server/authentication/providers/custom
- jose: https://github.com/panva/jose
