# Better Auth

Self-hosted OAuth 2.1 authorization server, embedded directly in the MCP server's Hono app. Better Auth handles authorization, token issuance, and JWKS; mcp-use only verifies the resulting JWTs.

## When to use

- You want a fully self-hosted IdP with no third-party dashboard.
- You already use Better Auth for app authentication and want to expose its OAuth server to MCP clients.
- You need full control over login UI, consent UI, and token claims.

## Install

```bash
npm install better-auth @better-auth/oauth-provider better-sqlite3
npm install mcp-use
```

## Configure Better Auth

`auth.ts`:

```ts
import { betterAuth } from 'better-auth'
import { jwt } from 'better-auth/plugins'
import { oauthProvider } from '@better-auth/oauth-provider'
import Database from 'better-sqlite3'

export const auth = betterAuth({
  authURL: 'http://localhost:3000',
  basePath: '/api/auth',
  secret: process.env.BETTER_AUTH_SECRET!,
  database: new Database('./sqlite.db'),

  socialProviders: {
    github: {
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    },
  },

  plugins: [
    jwt(), // required: signs JWTs
    oauthProvider({
      loginPage: '/sign-in',
      consentPage: '/consent',
      allowDynamicClientRegistration: true,
      allowUnauthenticatedClientRegistration: true,
      validAudiences: ['http://localhost:3000/mcp'],
      customAccessTokenClaims: async ({ user }) => ({
        email: user?.email,
        name: user?.name,
        picture: user?.image,
      }),
    }),
  ],
})
```

## Run migrations

```bash
npx auth@latest generate
npx auth@latest migrate
```

## Configure the MCP server

```ts
import { MCPServer, oauthBetterAuthProvider } from 'mcp-use/server'
import {
  oauthProviderAuthServerMetadata,
  oauthProviderOpenIdConfigMetadata,
} from '@better-auth/oauth-provider'
import { auth } from './auth.js'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthBetterAuthProvider({
    authURL: 'http://localhost:3000/api/auth',
  }),
})

// Mount Better Auth handlers
server.app.on(['GET', 'POST'], '/api/auth/**', (c) => auth.handler(c.req.raw))

// Discovery — CORS required for browser clients
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET',
}
const authMeta = oauthProviderAuthServerMetadata(auth, { headers: corsHeaders })
server.app.get('/.well-known/oauth-authorization-server', (c) => authMeta(c.req.raw))
server.app.get('/.well-known/oauth-authorization-server/api/auth', (c) => authMeta(c.req.raw))

const oidcMeta = oauthProviderOpenIdConfigMetadata(auth, { headers: corsHeaders })
server.app.get('/.well-known/openid-configuration', (c) => oidcMeta(c.req.raw))
server.app.get('/.well-known/openid-configuration/api/auth', (c) => oidcMeta(c.req.raw))

await server.listen(3000)
```

## Login & consent pages

Better Auth requires you to host these. Minimal sign-in:

```ts
server.app.get('/sign-in', (c) => {
  const qs = new URL(c.req.url).search
  return c.html(`<!DOCTYPE html>
<button onclick="signIn()">Sign in with GitHub</button>
<script>
  async function signIn() {
    const res = await fetch('/api/auth/sign-in/social', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        provider: 'github',
        callbackURL: '/api/auth/oauth2/authorize${qs}',
      }),
    })
    const data = await res.json()
    if (data.url) window.location.href = data.url
  }
</script>`)
})
```

Minimal consent page:

```ts
server.app.get('/consent', (c) => {
  const scope = new URL(c.req.url).searchParams.get('scope') || 'openid'
  return c.html(`<!DOCTYPE html>
<p>Requested scopes: ${scope}</p>
<button onclick="decide(true)">Allow</button>
<button onclick="decide(false)">Deny</button>
<script>
  async function decide(accept) {
    const oauth_query = window.location.search.slice(1)
    const res = await fetch('/api/auth/oauth2/consent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ accept, oauth_query }),
    })
    const data = await res.json()
    if (data.url) window.location.href = data.url
  }
</script>`)
})
```

## Environment variables

```bash
BETTER_AUTH_SECRET=<random secret, change in production>
GITHUB_CLIENT_ID=<from github oauth app>
GITHUB_CLIENT_SECRET=<from github oauth app>
```

GitHub callback URL: `http://localhost:3000/api/auth/callback/github`.

## Configuration options

```ts
oauthBetterAuthProvider({
  authURL: 'https://yourapp.com/api/auth',           // required
  verifyJwt: process.env.NODE_ENV === 'production',  // optional
  scopesSupported: ['openid', 'profile', 'email', 'offline_access'],
  getUserInfo: (payload) => ({
    userId: payload.sub as string,
    email: payload.email as string,
    name: payload.name as string,
    roles: (payload.roles as string[]) || [],
  }),
})
```

## Cross-references

- Decision matrix: `../01-overview-decision-matrix.md`
- Canonical: https://manufact.com/docs/typescript/server/authentication/providers/better-auth
- Runnable example: https://github.com/mcp-use/mcp-use/tree/main/libraries/typescript/packages/mcp-use/examples/server/oauth/better-auth
