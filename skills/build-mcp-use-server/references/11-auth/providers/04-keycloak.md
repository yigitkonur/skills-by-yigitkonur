# Keycloak

Self-hosted IAM with full RBAC. DCR-direct — Keycloak supports both anonymous and Initial-Access-Token DCR.

## Realm setup

1. Create a realm (or use `master`). Avoid `master` for production.
2. **Realm settings → Client registration** — enable **Anonymous Client Registration** (dev only) or generate an **Initial Access Token** (prod).
3. Create realm roles: **Realm settings → Roles → Add role** (`admin`, `user`, etc.).
4. Assign roles to users: **Users → <user> → Role mapping**.
5. Optional: per-client roles via **Clients → <client> → Roles**. These come through as `ctx.auth.permissions` formatted `client:role`.

## Audience mapper (production)

Keycloak doesn't put the resource server in `aud` by default. To enforce audience:

1. **Client scopes → <scope> → Mappers → Add → Audience**.
2. Set **Included Custom Audience** to your MCP server URL (e.g. `https://my-mcp-server.example.com/mcp`).
3. Add the scope to the client's **Default Client Scopes**.

Without the mapper, do not enable `audience` in the provider config — every token will fail verification.

## Environment variables

```bash
MCP_USE_OAUTH_KEYCLOAK_SERVER_URL=https://keycloak.example.com  # required
MCP_USE_OAUTH_KEYCLOAK_REALM=my-realm                           # required
MCP_USE_OAUTH_KEYCLOAK_AUDIENCE=https://my-mcp-server.example.com/mcp  # optional, requires Audience mapper
```

## Server config

```ts
import { MCPServer, oauthKeycloakProvider } from 'mcp-use/server'

// Zero-config
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthKeycloakProvider(),
})

await server.listen(3000)
```

Explicit config:

```ts
oauth: oauthKeycloakProvider({
  serverUrl: 'https://keycloak.example.com',
  realm: 'demo',
  audience: 'https://my-mcp-server.example.com/mcp',  // requires Audience mapper
  verifyJwt: process.env.NODE_ENV === 'production',
  scopesSupported: ['openid', 'profile', 'email'],
})
```

## Flow

```
MCP Client ──(1) GET /.well-known/oauth-protected-resource   ─▶ MCP Server
MCP Client ──(2) GET /.well-known/oauth-authorization-server ─▶ MCP Server ─▶ Keycloak
MCP Client ──(3) POST /clients-registrations/openid-connect  ─▶ Keycloak    (DCR)
MCP Client ──(4) GET  /protocol/openid-connect/auth          ─▶ Keycloak    (PKCE)
MCP Client ──(5) POST /protocol/openid-connect/token         ─▶ Keycloak
MCP Client ──(6) MCP request + Bearer <token>                ─▶ MCP Server  (verifies via JWKS)
```

## Roles in `ctx.auth`

| Source | mcp-use field |
|---|---|
| `realm_access.roles` | `ctx.auth.user.roles` |
| `resource_access.{client}.roles` | `ctx.auth.permissions` as `client:role` strings |
| `scope` | `ctx.auth.scopes` |

```ts
server.tool({ name: 'admin-action' }, async (_args, ctx) => {
  if (!ctx.auth.user.roles?.includes('admin')) {
    return { content: [{ type: 'text', text: 'Forbidden: admin role required' }], isError: true }
  }
  // ...
})
```

For per-client roles:

```ts
if (!ctx.auth.permissions.includes('billing-api:write')) {
  return { content: [{ type: 'text', text: 'Forbidden' }], isError: true }
}
```

## Calling Keycloak userinfo

```ts
server.tool({ name: 'keycloak-userinfo' }, async (_args, ctx) => {
  const url = `${process.env.MCP_USE_OAUTH_KEYCLOAK_SERVER_URL}/realms/${process.env.MCP_USE_OAUTH_KEYCLOAK_REALM}/protocol/openid-connect/userinfo`
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${ctx.auth.accessToken}` },
  })
  return { content: [{ type: 'text', text: JSON.stringify(await res.json()) }] }
})
```

## Production notes

- **HTTPS** for both Keycloak and MCP server. Anonymous DCR over HTTP is unsafe.
- **Disable anonymous DCR** in production. Issue Initial Access Tokens and require clients to use them.
- **Audience mapper** is mandatory if you set `audience` in config or `MCP_USE_OAUTH_KEYCLOAK_AUDIENCE`.
- **Realm-level roles only on `ctx.auth.user.roles`** — per-client roles live in `ctx.auth.permissions`.

## Cross-references

- Decision matrix: `../01-overview-decision-matrix.md`
- Permission guards: `../04-permission-guards.md`
- Canonical: https://manufact.com/docs/typescript/server/authentication/providers/keycloak
- Keycloak DCR docs: https://www.keycloak.org/securing-apps/client-registration
