# WorkOS

Enterprise SSO via WorkOS AuthKit. DCR-direct — clients register with WorkOS, the server only verifies tokens.

## Prerequisites

1. Sign up at the [WorkOS Dashboard](https://dashboard.workos.com/), create a project.
2. **Connect → Configuration** — enable **Dynamic Client Registration**.
3. **Configuration → Redirects** — add MCP client redirect URIs:
   - `http://localhost:*/oauth/callback`  (dev — Inspector, mcpc)
   - `https://your-app.example.com/oauth/callback`  (prod)

## Environment variables

```bash
MCP_USE_OAUTH_WORKOS_SUBDOMAIN=your-company.authkit.app  # required, full AuthKit domain
```

`apiKey` and `clientId` are not part of OAuth config — store them in any env var if your tool handlers call the WorkOS Management API.

## Server config

```ts
import { MCPServer, oauthWorkOSProvider } from 'mcp-use/server'

// Zero-config
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthWorkOSProvider(),
})

await server.listen(3000)
```

Explicit config:

```ts
oauth: oauthWorkOSProvider({
  subdomain: 'your-company.authkit.app',
  verifyJwt: process.env.NODE_ENV === 'production',
  scopesSupported: ['email', 'offline_access', 'openid', 'profile'],
})
```

## Multi-tenant filtering

WorkOS tokens include `organization_id` (custom claim). Use it to scope data:

```ts
server.tool(
  { name: 'get-documents' },
  async (_args, ctx) => {
    const orgId = ctx.auth.user.organization_id as string | undefined
    if (!orgId) {
      return { content: [{ type: 'text', text: 'Organization context required' }], isError: true }
    }
    const docs = await db.documents.findMany({ where: { organizationId: orgId } })
    return { content: [{ type: 'text', text: JSON.stringify(docs) }] }
  }
)
```

`ctx.auth.user.organization_id` and `ctx.auth.user.roles` are typed as `unknown` — narrow before use.

## User profile claims

```ts
server.tool(
  { name: 'get-profile' },
  async (_args, ctx) => ({
    content: [{ type: 'text', text: JSON.stringify({
      userId: ctx.auth.user.userId,
      email: ctx.auth.user.email,
      name: ctx.auth.user.name,
      organizationId: ctx.auth.user.organization_id,
      roles: ctx.auth.user.roles,
      scopes: ctx.auth.scopes,
    }) }],
  })
)
```

## Calling the WorkOS Management API

For directory sync, audit logs, etc., import the SDK and read your API key from env:

```ts
import { WorkOS } from '@workos-inc/node'
const workos = new WorkOS(process.env.WORKOS_API_KEY!)

server.tool(
  { name: 'list-team' },
  async (_args, ctx) => {
    const orgId = ctx.auth.user.organization_id as string
    const { data } = await workos.directorySync.listUsers({ directory: orgId })
    return { content: [{ type: 'text', text: JSON.stringify(data) }] }
  }
)
```

## Anti-patterns

- Don't try to set `clientId` for first-class DCR — WorkOS issues a per-client `client_id` automatically.
- Don't read `organization_id` without narrowing — it is `unknown` on `payload`.
- Don't use a non-AuthKit WorkOS deployment with `oauthWorkOSProvider` — only AuthKit exposes the necessary OAuth endpoints.

## Cross-references

- Decision matrix: `../01-overview-decision-matrix.md`
- Permission guards: `../04-permission-guards.md`
- Canonical: https://manufact.com/docs/typescript/server/authentication/providers/workos
- WorkOS AuthKit MCP guide: https://workos.com/docs/authkit/mcp
