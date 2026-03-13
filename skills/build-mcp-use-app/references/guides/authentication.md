# Authentication

Secure MCP servers with OAuth 2.0/2.1 using built-in provider functions and bearer token verification.

## Overview

mcp-use ships built-in OAuth provider functions that wrap endpoint discovery, JWT verification, and user-info extraction. Pass a provider to the `oauth` option of `MCPServer` and every tool callback receives verified user identity on `context.auth`.

When OAuth is configured the server automatically exposes:
- `GET /authorize` — initiates the authorization flow (supports PKCE via `code_challenge` + `code_challenge_method=S256`)
- `POST /token` — exchanges an authorization code for an access token
- `GET /.well-known/oauth-authorization-server` and `GET /.well-known/openid-configuration` — discovery metadata

All `/mcp/*` endpoints require a valid `Authorization: Bearer <token>` header.

### Provider Decision Table

| Provider | Function | Best For | Key Feature |
|---|---|---|---|
| Auth0 | `oauthAuth0Provider()` | SaaS apps, B2C | PKCE + JWKS, permissions via Actions |
| WorkOS | `oauthWorkOSProvider()` | Enterprise B2B | AuthKit SSO, org-scoped access, directory sync |
| Supabase | `oauthSupabaseProvider()` | Supabase projects | ES256/HS256 auto-detection, RLS integration |
| Keycloak | `oauthKeycloakProvider()` | Self-hosted IAM | Realm roles + client roles, full RBAC |
| Custom | `oauthCustomProvider()` | Any OIDC provider | Full control over endpoints + verification |

---

## Auth0

Create an application in [Auth0 Dashboard](https://manage.auth0.com/), create an API (its identifier becomes your audience), and add callback URLs.

```typescript
import { MCPServer, oauthAuth0Provider } from 'mcp-use/server'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthAuth0Provider({
    // Required
    domain: process.env.MCP_USE_OAUTH_AUTH0_DOMAIN!,
    audience: process.env.MCP_USE_OAUTH_AUTH0_AUDIENCE!,
    // Optional
    clientId: process.env.AUTH0_CLIENT_ID,
    clientSecret: process.env.AUTH0_CLIENT_SECRET,
    mode: 'proxy',       // 'proxy' (default) or 'direct'
    verifyJwt: true,     // recommended true in production
    scopes: ['openid', 'profile', 'email', 'offline_access'],
    getUserInfo: (payload) => ({
      userId: payload.sub,
      email: payload.email,
      name: payload.name,
      roles: payload['https://myapp.com/roles'] || [],
      permissions: payload.permissions || [],
    })
  })
})
```

```bash
MCP_USE_OAUTH_AUTH0_DOMAIN=your-tenant.auth0.com           # required
MCP_USE_OAUTH_AUTH0_AUDIENCE=https://your-api.example.com  # required
```

Inject permissions into access tokens via an Auth0 Post Login Action:

```javascript
exports.onExecutePostLogin = async (event, api) => {
  api.accessToken.setCustomClaim('permissions', event.authorization?.permissions || []);
};
```

---

## WorkOS

WorkOS provides enterprise SSO via AuthKit with organization-scoped access and directory sync. Sign up at [WorkOS Dashboard](https://dashboard.workos.com/) and configure redirect URIs. For enterprise SSO, set up connections under **SSO** or **Directory Sync**.

```typescript
import { MCPServer, oauthWorkOSProvider } from 'mcp-use/server'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthWorkOSProvider({
    // Required — full AuthKit domain
    subdomain: process.env.MCP_USE_OAUTH_WORKOS_SUBDOMAIN!,
    // Optional
    apiKey: process.env.MCP_USE_OAUTH_WORKOS_API_KEY,     // for WorkOS API calls
    clientId: process.env.MCP_USE_OAUTH_WORKOS_CLIENT_ID, // pre-registered OAuth client
    verifyJwt: true,
    getUserInfo: (payload) => ({
      userId: payload.sub,
      email: payload.email,
      name: payload.name,
      organizationId: payload.org_id,
      organizationName: payload.org_name,
      roles: payload.roles || [],
      connectionId: payload.connection_id,
    })
  })
})
```

```bash
MCP_USE_OAUTH_WORKOS_SUBDOMAIN=your-company.authkit.app  # required
MCP_USE_OAUTH_WORKOS_API_KEY=sk_live_...                  # optional
MCP_USE_OAUTH_WORKOS_CLIENT_ID=client_...                 # optional
```

Without a `clientId`, WorkOS uses Dynamic Client Registration — MCP clients register themselves automatically. WorkOS tokens include `org_id` for multi-tenant data isolation. Combine with `@workos-inc/node` for directory sync:

```typescript
import { WorkOS } from '@workos-inc/node'
const workos = new WorkOS(process.env.MCP_USE_OAUTH_WORKOS_API_KEY!)

server.tool({
  name: 'get-team',
  cb: async (params, context) => {
    const { data: users } = await workos.directorySync.listUsers({
      directory: context.auth.org_id
    })
    return json({ users })
  }
})
```

---

## Supabase

Create a project in [Supabase Dashboard](https://app.supabase.com/). New projects use ES256 tokens (JWKS auto-detected). Legacy HS256 projects need the JWT secret from **Project Settings** → **API**.

```typescript
import { MCPServer, oauthSupabaseProvider } from 'mcp-use/server'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthSupabaseProvider({
    projectId: process.env.MCP_USE_OAUTH_SUPABASE_PROJECT_ID!,
    // Only for legacy HS256 tokens:
    // jwtSecret: process.env.MCP_USE_OAUTH_SUPABASE_JWT_SECRET!,
    supabaseUrl: 'https://your-project-id.supabase.co', // auto-derived if omitted
    mode: 'proxy',
    verifyJwt: true,
    getUserInfo: (payload) => ({
      userId: payload.sub,
      email: payload.email,
      name: payload.user_metadata?.name,
      roles: payload.app_metadata?.roles || [],
      permissions: payload.app_metadata?.permissions || [],
    })
  })
})
```

```bash
MCP_USE_OAUTH_SUPABASE_PROJECT_ID=your-project-id  # required
MCP_USE_OAUTH_SUPABASE_JWT_SECRET=your-jwt-secret   # optional (HS256 only)
```

---

## Keycloak

Create a realm with an `openid-connect` client, set redirect URIs, create realm roles, and assign them to users.

```typescript
import { MCPServer, oauthKeycloakProvider } from 'mcp-use/server'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthKeycloakProvider({
    serverUrl: process.env.MCP_USE_OAUTH_KEYCLOAK_SERVER_URL!,
    realm: process.env.MCP_USE_OAUTH_KEYCLOAK_REALM!,
    clientId: process.env.MCP_USE_OAUTH_KEYCLOAK_CLIENT_ID!,
    clientSecret: process.env.KEYCLOAK_CLIENT_SECRET,  // optional
    mode: 'proxy',
    verifyJwt: true,
    scopes: ['openid', 'profile', 'email', 'roles'],
    getUserInfo: (payload) => ({
      userId: payload.sub,
      email: payload.email,
      name: payload.name,
      username: payload.preferred_username,
      roles: payload.realm_access?.roles || [],
      clientRoles: payload.resource_access?.['my-mcp-server']?.roles || [],
    })
  })
})
```

```bash
MCP_USE_OAUTH_KEYCLOAK_SERVER_URL=https://keycloak.example.com  # required
MCP_USE_OAUTH_KEYCLOAK_REALM=my-realm                           # required
MCP_USE_OAUTH_KEYCLOAK_CLIENT_ID=my-mcp-server                  # required
```

---

## Custom OAuth Provider

Connect any OIDC-compliant identity provider with full control over endpoints and verification.

```typescript
import { MCPServer, oauthCustomProvider } from 'mcp-use/server'
import { jwtVerify, createRemoteJWKSet } from 'jose'

const JWKS = createRemoteJWKSet(
  new URL('https://auth.example.com/.well-known/jwks.json')
)

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthCustomProvider({
    // Endpoints (required)
    issuer: 'https://auth.example.com',
    authEndpoint: 'https://auth.example.com/oauth/authorize',
    tokenEndpoint: 'https://auth.example.com/oauth/token',
    // Optional endpoints
    userInfoEndpoint: 'https://auth.example.com/oauth/userinfo',
    jwksUri: 'https://auth.example.com/.well-known/jwks.json',
    // Client credentials (optional)
    clientId: process.env.OAUTH_CLIENT_ID,
    clientSecret: process.env.OAUTH_CLIENT_SECRET,
    // Behavior
    mode: 'proxy',
    scopes: ['openid', 'profile', 'email'],
    audience: 'your-api-identifier',
    // Token verification (required)
    async verifyToken(token: string) {
      const { payload } = await jwtVerify(token, JWKS, {
        issuer: 'https://auth.example.com',
        audience: 'your-audience',
      })
      return payload
    },
    // Claim extraction (optional)
    getUserInfo: (payload: any) => ({
      userId: payload.sub,
      email: payload.email,
      name: payload.name,
      roles: payload.roles || [],
    })
  })
})
```

### Non-JWT Tokens (e.g. GitHub)

For opaque tokens, verify by calling the provider API in `verifyToken`:

```typescript
async verifyToken(token: string) {
  const res = await fetch('https://api.github.com/user', {
    headers: { Authorization: `Bearer ${token}` }
  })
  if (!res.ok) throw new Error('Invalid token')
  return await res.json()
},
getUserInfo: (p: any) => ({
  userId: p.id.toString(), username: p.login,
  name: p.name, email: p.email, picture: p.avatar_url,
})
```

---

## User Context — `context.auth`

When OAuth is configured, every tool callback receives a `context.auth` object conforming to `UserInfo`:

```typescript
interface UserInfo {
  userId: string;   email?: string;    name?: string
  username?: string; nickname?: string; picture?: string
  roles?: string[];  permissions?: string[]; scopes?: string[]
  [key: string]: any  // additional provider-specific claims
}
```

### Accessing User Info in Tools

```typescript
server.tool({
  name: 'create-document',
  schema: z.object({ title: z.string(), content: z.string() }),
  cb: async ({ title, content }, context) => {
    const doc = await db.documents.create({
      title, content,
      createdBy: context.auth.userId,
      createdByName: context.auth.name,
    })
    return text(`Document created by ${context.auth.name}`)
  }
})
```

### Custom Claim Extraction via `getUserInfo`

Every provider accepts an optional `getUserInfo` function to reshape JWT claims into the `UserInfo` shape. This lets you map namespaced claims (`https://myapp.com/roles`) or nested metadata (`app_metadata.roles`) to top-level fields.

---

## Permission-Based Tool Guards

Check `context.auth.permissions` or `context.auth.roles` to enforce access control:

```typescript
server.tool({
  name: 'delete-document',
  schema: z.object({ documentId: z.string() }),
  cb: async ({ documentId }, context) => {
    if (!context.auth.permissions?.includes('delete:documents')) {
      return error('Forbidden: delete:documents permission required')
    }
    await db.documents.delete({ id: documentId })
    return text('Document deleted')
  }
})
```

### Role Guard (Keycloak)

```typescript
if (!context.auth.roles?.includes('admin')) {
  return error('Forbidden: admin role required')
}
```

### Organization-Scoped Access (WorkOS)

```typescript
const orgId = context.auth.org_id
if (!orgId) return error('No organization context')
const data = await db.data.findMany({ where: { organizationId: orgId } })
```

---

## Environment Variables Reference

| Provider | Variable | Required | Purpose |
|---|---|---|---|
| Auth0 | `MCP_USE_OAUTH_AUTH0_DOMAIN` | ✅ | Tenant domain |
| Auth0 | `MCP_USE_OAUTH_AUTH0_AUDIENCE` | ✅ | API identifier / audience URI |
| WorkOS | `MCP_USE_OAUTH_WORKOS_SUBDOMAIN` | ✅ | AuthKit domain |
| WorkOS | `MCP_USE_OAUTH_WORKOS_API_KEY` | ❌ | API key for WorkOS API calls |
| WorkOS | `MCP_USE_OAUTH_WORKOS_CLIENT_ID` | ❌ | Pre-registered OAuth client ID |
| Supabase | `MCP_USE_OAUTH_SUPABASE_PROJECT_ID` | ✅ | Project ID |
| Supabase | `MCP_USE_OAUTH_SUPABASE_JWT_SECRET` | ❌ | JWT secret (HS256 only) |
| Keycloak | `MCP_USE_OAUTH_KEYCLOAK_SERVER_URL` | ✅ | Keycloak server URL |
| Keycloak | `MCP_USE_OAUTH_KEYCLOAK_REALM` | ✅ | Realm name |
| Keycloak | `MCP_USE_OAUTH_KEYCLOAK_CLIENT_ID` | ✅ | Client ID |
| Custom | *(inline)* | — | Configured via `oauthCustomProvider()` options |

---

## Security Best Practices

### Token Handling
- **Never log or return raw tokens** in tool responses or logging output.
- **Validate permissions in every tool handler.** Do not rely on the client.

### Transport Security
- **Use HTTPS** in production. OAuth tokens over plain HTTP are vulnerable to interception.
- **Set explicit `allowedOrigins`** to prevent DNS rebinding:

```typescript
const server = new MCPServer({
  name: 'my-server', version: '1.0.0',
  oauth: oauthAuth0Provider({ domain: '...', audience: '...' }),
  allowedOrigins: ['https://app.example.com'],
})
```

### Scope & Data Isolation
- **Scope data queries** to `userId` or `organizationId` from `context.auth`.
- **Request only needed scopes.** Enable `verifyJwt: true` in production.

### Secrets Management
- Store secrets in environment variables, never in source code. Add `.env` to `.gitignore`.

---

## Common Issues

| Issue | Cause | Fix |
|---|---|---|
| `"Unauthorized"` on every call | Missing or expired token | Check provider config and token refresh flow |
| `"Invalid audience"` | Audience mismatch | Set `MCP_USE_OAUTH_AUTH0_AUDIENCE` to match Auth0 API identifier |
| CORS errors on redirect | Callback URL not allowed | Add callback URL to provider dashboard + `allowedOrigins` |
| `context.auth` is `undefined` | No `oauth` option on server | Pass a provider to `MCPServer` constructor |
| `permissions` is empty | Scopes not configured | Add permissions in provider settings or use `getUserInfo` |
| `org_id` is `undefined` | Not using WorkOS or no org | Assign user to a WorkOS organization |

### Debugging Auth Locally

```typescript
// Remove before deploying to production
server.tool({
  name: 'debug-auth',
  cb: async (_params, context) => json({
    hasAuth: !!context.auth,
    userId: context.auth?.userId ?? 'none',
    scopes: context.auth?.scopes ?? [],
  })
})
```

---

## Summary

1. Pick a provider — `oauthAuth0Provider()`, `oauthWorkOSProvider()`, `oauthSupabaseProvider()`, `oauthKeycloakProvider()`, or `oauthCustomProvider()`.
2. Set the required `MCP_USE_OAUTH_*` environment variables.
3. Access verified identity via `context.auth` (`UserInfo`) in tool handlers.
4. Guard operations with `context.auth.permissions` / `context.auth.roles`.
5. Use `getUserInfo` to extract custom claims from any provider.
