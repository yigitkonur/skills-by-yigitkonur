# Authentication

Secure MCP servers with OAuth 2.0/2.1 using built-in provider functions, custom providers, and permission-aware tool guards.

---

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
    verifyJwt: true,     // recommended true in production
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
    clientId: process.env.MCP_USE_OAUTH_WORKOS_CLIENT_ID,
    apiKey: process.env.MCP_USE_OAUTH_WORKOS_API_KEY,
    verifyJwt: true,
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
    return object({ users })
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
    // skipVerification: false,  // default: verify JWT
  })
})
```

Supabase tokens include `sub` (user ID), `email`, and `role`. Access via `context.auth`:

```typescript
// Example: accessing Supabase user info from a tool handler
// context.auth contains the verified JWT payload with userId: payload.sub,
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
    // Required
    serverUrl: process.env.MCP_USE_OAUTH_KEYCLOAK_SERVER_URL!,
    realm: process.env.MCP_USE_OAUTH_KEYCLOAK_REALM!,
    // Optional
    clientId: process.env.MCP_USE_OAUTH_KEYCLOAK_CLIENT_ID,
    verifyJwt: true,
  })
})
```

```bash
MCP_USE_OAUTH_KEYCLOAK_SERVER_URL=https://keycloak.example.com  # required
MCP_USE_OAUTH_KEYCLOAK_REALM=my-realm                           # required
MCP_USE_OAUTH_KEYCLOAK_CLIENT_ID=my-mcp-server                  # optional
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
    // Required
    issuer: 'https://auth.example.com',
    authEndpoint: 'https://auth.example.com/oauth/authorize',  // NOT authorizationEndpoint
    tokenEndpoint: 'https://auth.example.com/oauth/token',
    jwksUrl: 'https://auth.example.com/.well-known/jwks.json', // NOT jwksUri
    // Token verification (required)
    async verifyToken(token: string) {
      const { payload } = await jwtVerify(token, JWKS, {
        issuer: 'https://auth.example.com',
        audience: 'your-audience',
      })
      return payload
    },
    // Optional
    scopesSupported: ['openid', 'profile', 'email'],  // NOT scopes
    getUserInfo: (payload: any) => ({
      userId: payload.sub,
      email: payload.email,
      name: payload.name,
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
  cb: async (_params, context) => object({
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


---

## Browser OAuth Flow

When OAuth is enabled, MCP clients can hand off authorization to the user's browser, complete the provider login flow, and return with an authorization code that the server exchanges for tokens. This is the best fit for web apps, desktop apps that can open a browser, and any integration that supports PKCE.

### Typical sequence

| Step | Actor | Description |
|---|---|---|
| 1 | Client | Starts OAuth authorization request |
| 2 | Server | Redirects to provider or proxies the flow |
| 3 | Browser | User signs in, approves scopes, completes MFA |
| 4 | Provider | Redirects back with authorization code |
| 5 | Server | Exchanges code for tokens |
| 6 | Tool handler | Receives verified `ctx.auth` |

```typescript
import { MCPServer, oauthAuth0Provider, text } from 'mcp-use/server'

const server = new MCPServer({
  name: 'browser-auth-server',
  version: '1.0.0',
  oauth: oauthAuth0Provider({
    domain: process.env.MCP_USE_OAUTH_AUTH0_DOMAIN!,
    audience: process.env.MCP_USE_OAUTH_AUTH0_AUDIENCE!,
    scopes: ['openid', 'profile', 'email', 'offline_access'],
  }),
  allowedOrigins: ['https://app.example.com'],
})

server.tool({
  name: 'profile',
  description: 'Return the signed-in user profile.',
}, async (_args, ctx) => text(`Hello ${ctx.auth?.name ?? 'anonymous'}`))
```

### Browser-flow considerations

| Concern | Recommendation |
|---|---|
| Redirect URIs | Register exact callback URLs in the provider |
| PKCE | Enable it for public clients |
| `offline_access` | Request only when refresh tokens are needed |
| Origin protection | Combine OAuth with `allowedOrigins` |
| HTTPS | Required in production |

❌ **BAD** — Use wildcards for redirect URIs in production because it is "easier":

```text
https://*.example.com/callback
```

✅ **GOOD** — Register exact callback URLs per environment:

```text
https://app.example.com/oauth/callback
https://staging.example.com/oauth/callback
```

---

## Token Refresh and Long-Lived Sessions

OAuth access tokens are intentionally short-lived. If your client needs continuity beyond the access token lifetime, enable refresh tokens and make the expiry story explicit.

### Refresh token checklist

| Item | Why |
|---|---|
| Request `offline_access` only when needed | Limits token power |
| Store refresh tokens securely | They often outlive access tokens |
| Rotate refresh tokens when the provider supports it | Reduces replay risk |
| Align session timeout with token strategy | Avoid confusing partial expiry |

### Auth0 refresh example

```typescript
const server = new MCPServer({
  name: 'refresh-aware-server',
  version: '1.0.0',
  oauth: oauthAuth0Provider({
    domain: process.env.MCP_USE_OAUTH_AUTH0_DOMAIN!,
    audience: process.env.MCP_USE_OAUTH_AUTH0_AUDIENCE!,
    scopes: ['openid', 'profile', 'email', 'offline_access'],
  }),
})
```

### Refresh behavior guidance

- Treat refresh as a **client concern** unless your deployment deliberately proxies OAuth for clients.
- If the server participates in token exchange, log metadata only — never raw refresh tokens.
- Re-check `ctx.auth.permissions`, `ctx.auth.roles`, and org context on every tool call even after refresh.

❌ **BAD** — Assume a valid session means a still-valid access token:

```typescript
if (ctx.session) return doSensitiveWork()
```

✅ **GOOD** — Base access control on verified auth context for every request:

```typescript
if (!ctx.auth?.permissions?.includes('reports:read')) {
  return error('Missing reports:read permission.')
}
```

---

## Additional Provider Patterns

The built-in providers cover the most common production cases, and `oauthCustomProvider()` lets you integrate any OIDC-compliant system. In practice, teams often use the custom provider hook for Okta, AWS Cognito, Google Identity, Microsoft Entra ID, or a self-hosted identity gateway.

### Provider mapping guide

| Identity system | Recommended setup |
|---|---|
| Auth0 | `oauthAuth0Provider()` |
| WorkOS | `oauthWorkOSProvider()` |
| Supabase | `oauthSupabaseProvider()` |
| Keycloak | `oauthKeycloakProvider()` |
| Okta / Entra / Cognito / Google | `oauthCustomProvider()` |

### Example: custom provider for Okta-style OIDC

```typescript
import { MCPServer, oauthCustomProvider } from 'mcp-use/server'

const server = new MCPServer({
  name: 'okta-style-server',
  version: '1.0.0',
  oauth: oauthCustomProvider({
    issuer: 'https://acme.okta.com/oauth2/default',
    authorizationEndpoint: 'https://acme.okta.com/oauth2/default/v1/authorize',
    tokenEndpoint: 'https://acme.okta.com/oauth2/default/v1/token',
    jwksUri: 'https://acme.okta.com/oauth2/default/v1/keys',
    scopes: ['openid', 'profile', 'email'],
    getUserInfo: (payload) => ({
      userId: payload.sub,
      email: payload.email,
      name: payload.name,
      roles: payload.groups ?? [],
      permissions: payload.permissions ?? [],
    }),
  }),
})
```

### `oauthCustomProvider()` parameter table

| Option | Required | Purpose |
|---|---|---|
| `issuer` | usually | Canonical issuer for token validation |
| `authorizationEndpoint` | yes | Browser authorization URL |
| `tokenEndpoint` | yes | Authorization code exchange |
| `jwksUri` | recommended | JWT verification keys |
| `clientId` | optional | Pre-registered client ID |
| `clientSecret` | optional | Confidential client secret |
| `scopes` | optional | Default requested scopes |
| `getUserInfo` | highly recommended | Map provider claims to `ctx.auth` |

### Choosing between built-in and custom providers

| Use built-in when... | Use custom when... |
|---|---|
| The provider already has a maintained helper | Your identity provider is OIDC-compliant but not bundled |
| You want the fewest moving parts | You need custom claim mapping or nonstandard endpoints |
| The docs cover your exact setup | You are integrating internal auth infrastructure |

---

## Working with `ctx.auth`

Every authenticated tool or resource callback should treat `ctx.auth` as the source of truth for user identity and authorization. Design your handlers so **all sensitive decisions** flow from this object.

### Common `ctx.auth` fields

| Field | Meaning |
|---|---|
| `userId` | Stable subject / user identifier |
| `email` | User email when available |
| `name` | Human-friendly display name |
| `roles` | Role list from the provider |
| `permissions` | Fine-grained allowed actions |
| `organizationId` | Org / tenant context when the provider supplies it |
| `scopes` | OAuth scopes granted by the token |

```typescript
server.tool(
  {
    name: 'account-summary',
    description: 'Return account details for the signed-in user.',
  },
  async (_args, ctx) => object({
    userId: ctx.auth?.userId ?? null,
    email: ctx.auth?.email ?? null,
    roles: ctx.auth?.roles ?? [],
    permissions: ctx.auth?.permissions ?? [],
  })
)
```

### Permission-based access patterns

| Pattern | Example |
|---|---|
| Role gate | `ctx.auth?.roles?.includes('admin')` |
| Permission gate | `ctx.auth?.permissions?.includes('billing:write')` |
| Org scoping | Query only data for `ctx.auth.organizationId` |
| Ownership check | Match `ctx.auth.userId` against the resource owner |

### Protecting tools

```typescript
server.tool(
  {
    name: 'delete-report',
    description: 'Delete a report by id.',
    schema: z.object({ id: z.string().describe('Report id to delete') }),
  },
  async ({ id }, ctx) => {
    if (!ctx.auth?.permissions?.includes('reports:delete')) {
      return error('Missing reports:delete permission.')
    }

    await deleteReport(id, { actorId: ctx.auth.userId })
    return text(`Deleted report ${id}.`)
  }
)
```

### Protecting resources and prompts

```typescript
server.resource(
  {
    name: 'billing-ledger',
    uri: 'billing://ledger',
    title: 'Billing Ledger',
  },
  async (_uri, ctx) => {
    if (!ctx.auth?.roles?.includes('finance')) {
      return error('Finance role required.')
    }
    return object(await loadBillingLedger(ctx.auth.organizationId))
  }
)
```

❌ **BAD** — Trust a user id passed from the client body:

```typescript
schema: z.object({ userId: z.string().describe('Who to read') })
```

✅ **GOOD** — Derive identity from `ctx.auth` and accept only resource selectors:

```typescript
schema: z.object({ reportId: z.string().describe('Report to read') })
```

❌ **BAD** — Check only for authentication, not authorization:

```typescript
if (!ctx.auth) return error('Unauthorized')
```

✅ **GOOD** — Authenticate first, then authorize the specific action:

```typescript
if (!ctx.auth) return error('Unauthorized')
if (!ctx.auth.permissions?.includes('reports:write')) return error('Forbidden')
```

---

## Protecting Specific Capabilities

Not every endpoint needs the same policy. Split protections by sensitivity level.

### Capability matrix

| Capability | Typical requirement |
|---|---|
| Read-only public metadata | No auth or weak auth |
| User profile / private documents | Any authenticated user |
| Billing / admin / destructive tools | Explicit role or permission |
| Organization-wide exports | Org membership + export permission |
| OAuth debugging / introspection | Development only or admin-only |

### Resource-specific example

```typescript
server.resourceTemplate(
  {
    name: 'org-settings',
    uriTemplate: 'org://{orgId}/settings',
    title: 'Organization settings',
  },
  async (_uri, { orgId }, ctx) => {
    if (ctx.auth?.organizationId !== orgId && !ctx.auth?.roles?.includes('super-admin')) {
      return error('You cannot read settings for this organization.')
    }
    return object(await getOrgSettings(orgId))
  }
)
```

### Prompt-specific example

```typescript
server.prompt(
  {
    name: 'draft-security-brief',
    description: 'Generate a security brief for privileged users.',
    schema: z.object({ audience: z.string().describe('Audience for the brief') }),
  },
  async ({ audience }, ctx) => {
    if (!ctx.auth?.permissions?.includes('security:brief:generate')) {
      return error('Missing security:brief:generate permission.')
    }
    return text(`Draft a security brief for ${audience}.`)
  }
)
```

---

## Auth Debugging Checklist

| Symptom | Check first |
|---|---|
| `ctx.auth` is undefined | Was `oauth` configured on `MCPServer`? |
| Login works but roles are empty | Did your provider include role claims? |
| Browser redirect fails | Are callback URLs and allowed origins exact? |
| Auth works on one tool only | Are other tools using `ctx.auth` instead of request args? |
| Refresh fails unexpectedly | Did the client request `offline_access` and store the refresh token correctly? |

## Recommended defaults

1. Prefer a **built-in provider** when available.
2. Use **`oauthCustomProvider()`** for any other OIDC-compliant identity service.
3. Use **browser OAuth + PKCE** for public clients.
4. Treat **refresh tokens** as an explicit design choice, not a default.
5. Base authorization on **`ctx.auth`**, not client-submitted identity fields.
