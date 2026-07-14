# Auth0

DCR-direct via Auth0's Early Access Dynamic Client Registration. For non-DCR Auth0 (Regular Web Apps), use the OAuth Proxy — see `06-oauth-proxy.md`.

## Prerequisites

1. Join Auth0's MCP Early Access program (DCR is gated).
2. In **Settings → Advanced**, enable **Resource Parameter Compatibility Profile**.
3. Promote at least one connection to domain-level so third-party MCP clients can use it:

```bash
auth0 api get connections
auth0 api patch connections/<connection_id> --data '{"is_domain_connection": true}'
```

## Create an API

```bash
auth0 api post resource-servers --data '{
  "identifier": "https://your-api.example.com",
  "name": "MCP Tools API",
  "signing_alg": "RS256",
  "token_dialect": "rfc9068_profile_authz",
  "enforce_policies": true,
  "scopes": [
    {"value": "read:data", "description": "Read data"},
    {"value": "write:data", "description": "Write data"}
  ]
}'
```

The `rfc9068_profile_authz` token dialect puts a `permissions` claim in access tokens, which mcp-use surfaces as `ctx.auth.permissions`.

## Environment variables

```bash
MCP_USE_OAUTH_AUTH0_DOMAIN=your-tenant.auth0.com           # required
MCP_USE_OAUTH_AUTH0_AUDIENCE=https://your-api.example.com  # required — must match API identifier
```

## Server config

```ts
import { MCPServer, oauthAuth0Provider } from 'mcp-use/server'

// Zero-config: reads both env vars
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthAuth0Provider(),
})

await server.listen(3000)
```

Explicit config:

```ts
oauth: oauthAuth0Provider({
  domain: 'your-tenant.auth0.com',
  audience: 'https://your-api.example.com',
  verifyJwt: process.env.NODE_ENV === 'production',  // disable only in dev
  scopesSupported: ['openid', 'profile', 'email', 'offline_access', 'read:data', 'write:data'],
})
```

## Redirect URIs

Add MCP client URIs in **Applications → APIs → your API → Authorized Callback URLs**, or — for DCR — leave callbacks open at the tenant level. Common entries:

- `http://localhost:*/inspector/oauth/callback`  (Inspector dev)
- `http://localhost:*/oauth/callback`            (mcpc / Claude Desktop)
- `https://your-app.example.com/oauth/callback`  (production)

## Permissions in access tokens (Post Login Action)

Inject permissions via an Action:

```js
// Auth0 Action — Post Login
exports.onExecutePostLogin = async (event, api) => {
  api.accessToken.setCustomClaim(
    'permissions',
    event.authorization?.permissions || []
  )
}
```

`ctx.auth.permissions` will then be populated. Combine with `04-permission-guards.md` for tool gating.

## Working example

```ts
import { MCPServer, oauthAuth0Provider, error, text } from 'mcp-use/server'
import { z } from 'zod'

const server = new MCPServer({
  name: 'auth0-demo',
  version: '1.0.0',
  oauth: oauthAuth0Provider(),
})

server.tool(
  {
    name: 'whoami',
    description: 'Return the authenticated user',
  },
  async (_args, ctx) => text(`User: ${ctx.auth.user.name} <${ctx.auth.user.email}>`)
)

server.tool(
  {
    name: 'delete-data',
    schema: z.object({ id: z.string() }),
  },
  async ({ id }, ctx) => {
    if (!ctx.auth.permissions.includes('delete:data')) {
      return error('Forbidden: delete:data required')
    }
    await db.delete(id)
    return text(`Deleted ${id}`)
  }
)

await server.listen(3000)
```

## Anti-patterns

- Don't use `signing_alg: 'HS256'` — opaque-secret HS256 cannot be JWKS-verified.
- Don't skip `enforce_policies: true` — without it, Auth0 will not include `permissions`.
- Don't request opaque tokens (no API created) — they cannot be verified locally.

## Cross-references

- Decision matrix: `../01-overview-decision-matrix.md`
- Permissions: `../04-permission-guards.md`
- If DCR is unavailable: `06-oauth-proxy.md` (Auth0 Regular Web App section)
- Canonical: https://manufact.com/docs/typescript/server/authentication/providers/auth0
