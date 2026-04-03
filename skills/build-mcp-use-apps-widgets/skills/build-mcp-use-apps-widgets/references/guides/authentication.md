# Authentication

Secure MCP servers with OAuth 2.0/2.1 using built-in provider functions and bearer token verification.

## Overview

mcp-use ships built-in OAuth provider factory functions that handle endpoint discovery, JWT verification, and user-info extraction. Pass a provider to the `oauth` option of `MCPServer` and every tool callback receives verified identity on `context.auth`.

All providers support **zero-config setup** via environment variables — call the factory with no arguments and it reads the required values from `process.env`.

When OAuth is configured the server automatically exposes:
- `GET /authorize` — initiates the authorization flow (supports PKCE via `code_challenge` + `code_challenge_method=S256`)
- `POST /token` — exchanges an authorization code for an access token
- `GET /.well-known/oauth-authorization-server` and `GET /.well-known/openid-configuration` — discovery metadata

All `/mcp/*` endpoints require a valid `Authorization: Bearer <token>` header.

### Provider Decision Table

| Provider | Function | Best For | Key Feature |
|---|---|---|---|
| Auth0 | `oauthAuth0Provider()` | SaaS apps, B2C | PKCE + JWKS, permissions via Actions |
| WorkOS | `oauthWorkOSProvider()` | Enterprise B2B | AuthKit SSO, Dynamic Client Registration, org-scoped access |
| Supabase | `oauthSupabaseProvider()` | Supabase projects | ES256/HS256 auto-detection, RLS integration |
| Keycloak | `oauthKeycloakProvider()` | Self-hosted IAM | Realm roles + client roles, full RBAC |
| Custom | `oauthCustomProvider()` | Any OIDC provider | Full control over endpoints + verification |

---

## Auth0

Create an application in [Auth0 Dashboard](https://manage.auth0.com/), create an API (its identifier becomes your audience), and add callback URLs.

### Zero-Config (via environment variables)

```typescript
import { MCPServer, oauthAuth0Provider } from 'mcp-use/server';

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthAuth0Provider(), // reads MCP_USE_OAUTH_AUTH0_DOMAIN + AUDIENCE from env
});
```

### Explicit Configuration

```typescript
import { MCPServer, oauthAuth0Provider } from 'mcp-use/server';

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthAuth0Provider({
    domain: process.env.MCP_USE_OAUTH_AUTH0_DOMAIN!,    // required
    audience: process.env.MCP_USE_OAUTH_AUTH0_AUDIENCE!, // required
    verifyJwt: true,  // default: true — disable only in local dev
  }),
});
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

WorkOS provides enterprise SSO via AuthKit with organization-scoped access and directory sync. Sign up at [WorkOS Dashboard](https://dashboard.workos.com/) and configure redirect URIs.

WorkOS supports two OAuth modes:
- **Dynamic Client Registration (recommended)** — MCP clients register automatically. Enable DCR in WorkOS Dashboard under Connect → Configuration.
- **Pre-registered OAuth Client** — set `clientId` for a fixed OAuth client.

### Zero-Config (Dynamic Client Registration)

```typescript
import { MCPServer, oauthWorkOSProvider } from 'mcp-use/server';

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthWorkOSProvider(), // reads MCP_USE_OAUTH_WORKOS_SUBDOMAIN from env
});
```

### Explicit Configuration

```typescript
import { MCPServer, oauthWorkOSProvider } from 'mcp-use/server';

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthWorkOSProvider({
    subdomain: process.env.MCP_USE_OAUTH_WORKOS_SUBDOMAIN!, // required — full AuthKit domain
    clientId: process.env.MCP_USE_OAUTH_WORKOS_CLIENT_ID,   // optional — pre-registered client
    apiKey: process.env.MCP_USE_OAUTH_WORKOS_API_KEY,       // optional — for WorkOS API calls
    verifyJwt: true,
  }),
});
```

```bash
MCP_USE_OAUTH_WORKOS_SUBDOMAIN=your-company.authkit.app  # required
MCP_USE_OAUTH_WORKOS_CLIENT_ID=client_...                 # optional
MCP_USE_OAUTH_WORKOS_API_KEY=sk_live_...                  # optional
```

---

## Supabase

Create a project in [Supabase Dashboard](https://app.supabase.com/). New projects use ES256 tokens (JWKS auto-detected). Legacy HS256 projects need the JWT secret from **Project Settings** → **API**.

### Zero-Config

```typescript
import { MCPServer, oauthSupabaseProvider } from 'mcp-use/server';

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthSupabaseProvider(), // reads MCP_USE_OAUTH_SUPABASE_PROJECT_ID from env
});
```

### Explicit Configuration

```typescript
import { MCPServer, oauthSupabaseProvider } from 'mcp-use/server';

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthSupabaseProvider({
    projectId: process.env.MCP_USE_OAUTH_SUPABASE_PROJECT_ID!, // required
    jwtSecret: process.env.MCP_USE_OAUTH_SUPABASE_JWT_SECRET,  // optional — HS256 only
    skipVerification: false, // default: false
  }),
});
```

```bash
MCP_USE_OAUTH_SUPABASE_PROJECT_ID=your-project-id  # required
MCP_USE_OAUTH_SUPABASE_JWT_SECRET=your-jwt-secret   # optional (HS256 only)
```

---

## Keycloak

Create a realm with an `openid-connect` client, set redirect URIs, create realm roles, and assign them to users.

### Zero-Config

```typescript
import { MCPServer, oauthKeycloakProvider } from 'mcp-use/server';

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthKeycloakProvider(), // reads MCP_USE_OAUTH_KEYCLOAK_* from env
});
```

### Explicit Configuration

```typescript
import { MCPServer, oauthKeycloakProvider } from 'mcp-use/server';

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthKeycloakProvider({
    serverUrl: process.env.MCP_USE_OAUTH_KEYCLOAK_SERVER_URL!, // required
    realm: process.env.MCP_USE_OAUTH_KEYCLOAK_REALM!,          // required
    clientId: process.env.MCP_USE_OAUTH_KEYCLOAK_CLIENT_ID,    // optional
    verifyJwt: true,
  }),
});
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
import { MCPServer, oauthCustomProvider } from 'mcp-use/server';
import { jwtVerify, createRemoteJWKSet } from 'jose';

const JWKS = createRemoteJWKSet(
  new URL('https://auth.example.com/.well-known/jwks.json')
);

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthCustomProvider({
    // Required endpoints
    issuer: 'https://auth.example.com',
    authEndpoint: 'https://auth.example.com/oauth/authorize',
    tokenEndpoint: 'https://auth.example.com/oauth/token',
    jwksUrl: 'https://auth.example.com/.well-known/jwks.json',
    // Optional
    scopesSupported: ['openid', 'profile', 'email'],
    grantTypesSupported: ['authorization_code', 'refresh_token'],
    // Token verification (required)
    async verifyToken(token: string) {
      return jwtVerify(token, JWKS, {
        issuer: 'https://auth.example.com',
        audience: 'your-audience',
      });
    },
    // Claim extraction (optional)
    getUserInfo: (payload: any) => ({
      userId: payload.sub,
      email: payload.email,
      name: payload.name,
      roles: payload.roles || [],
    }),
  }),
});
```

### Non-JWT Tokens (e.g. GitHub)

For opaque tokens, verify by calling the provider API in `verifyToken`:

```typescript
async verifyToken(token: string) {
  const res = await fetch('https://api.github.com/user', {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Invalid token');
  return { payload: await res.json() };
},
getUserInfo: (p: any) => ({
  userId: p.id.toString(),
  username: p.login,
  name: p.name,
  email: p.email,
}),
```

---

## Provider Factory Signatures

All factory functions accept an optional partial config object and fall back to environment variables. All parameters are optional if the corresponding env var is set.

```typescript
// Auth0
function oauthAuth0Provider(config?: {
  domain?: string;    // fallback: MCP_USE_OAUTH_AUTH0_DOMAIN
  audience?: string;  // fallback: MCP_USE_OAUTH_AUTH0_AUDIENCE
  verifyJwt?: boolean;
}): OAuthProvider;

// WorkOS
function oauthWorkOSProvider(config?: {
  subdomain?: string;  // fallback: MCP_USE_OAUTH_WORKOS_SUBDOMAIN
  clientId?: string;   // fallback: MCP_USE_OAUTH_WORKOS_CLIENT_ID
  apiKey?: string;     // fallback: MCP_USE_OAUTH_WORKOS_API_KEY
  verifyJwt?: boolean;
}): OAuthProvider;

// Supabase
function oauthSupabaseProvider(config?: {
  projectId?: string;       // fallback: MCP_USE_OAUTH_SUPABASE_PROJECT_ID
  jwtSecret?: string;       // fallback: MCP_USE_OAUTH_SUPABASE_JWT_SECRET
  skipVerification?: boolean;
}): OAuthProvider;

// Keycloak
function oauthKeycloakProvider(config?: {
  serverUrl?: string;  // fallback: MCP_USE_OAUTH_KEYCLOAK_SERVER_URL
  realm?: string;      // fallback: MCP_USE_OAUTH_KEYCLOAK_REALM
  clientId?: string;   // fallback: MCP_USE_OAUTH_KEYCLOAK_CLIENT_ID
  verifyJwt?: boolean;
}): OAuthProvider;

// Custom (all fields required — no env var fallback)
function oauthCustomProvider(config: {
  issuer: string;
  authEndpoint: string;
  tokenEndpoint: string;
  jwksUrl: string;
  scopesSupported?: string[];
  grantTypesSupported?: string[];
  verifyToken: (token: string) => Promise<{ payload: Record<string, unknown> }>;
  getUserInfo?: (payload: Record<string, unknown>) => UserInfo;
}): OAuthProvider;
```

---

## User Context — `context.auth`

When OAuth is configured, every tool callback receives a `context.auth` object with the following shape:

```typescript
// The full auth object on context.auth
interface AuthContext {
  user: UserInfo;                    // verified user identity
  payload: Record<string, unknown>;  // raw decoded JWT payload
  accessToken: string;               // the raw bearer token
  scopes: string[];                  // from the JWT 'scope' claim (space-split)
  permissions: string[];             // from the JWT 'permissions' claim (Auth0 style)
}

// UserInfo — extracted from the JWT payload
interface UserInfo {
  userId: string;        // required — mapped from JWT 'sub' claim
  email?: string;
  name?: string;
  username?: string;
  nickname?: string;
  picture?: string;
  roles?: string[];
  permissions?: string[];
  [key: string]: unknown; // additional provider-specific claims
}
```

### Accessing User Info in Tools

```typescript
import { object } from 'mcp-use/server';
import { z } from 'zod';

server.tool({
  name: 'create-document',
  schema: z.object({ title: z.string(), content: z.string() }),
}, async ({ title, content }, ctx) => {
  const doc = await db.documents.create({
    title,
    content,
    createdBy: ctx.auth.user.userId,
    createdByName: ctx.auth.user.name,
  });
  return text(`Document created by ${ctx.auth.user.name}`);
});
```

### Accessing Raw Token Data

```typescript
server.tool({ name: 'get-user-info' }, async (_args, ctx) =>
  object({
    userId: ctx.auth.user.userId,
    email: ctx.auth.user.email,
    name: ctx.auth.user.name,
    permissions: ctx.auth.permissions,
    scopes: ctx.auth.scopes,
    // raw payload available for provider-specific claims:
    rawSub: ctx.auth.payload.sub,
  })
);
```

### Custom Claim Extraction

The `getUserInfo` option on each provider reshapes JWT claims into the `UserInfo` shape. Use it to map namespaced claims (`https://myapp.com/roles`) or nested metadata (`app_metadata.roles`) to top-level fields.

```typescript
oauth: oauthAuth0Provider({
  domain: 'your-tenant.auth0.com',
  audience: 'https://your-api.com',
  // Note: getUserInfo is not a factory param — use the provider class directly
  // or use the raw payload via ctx.auth.payload for custom claims
}),
```

> **Note:** The factory functions (`oauthAuth0Provider`, etc.) do not accept a `getUserInfo` parameter. To customize claim extraction beyond what the built-in providers provide, use `oauthCustomProvider` and implement `getUserInfo` there, or read from `ctx.auth.payload` directly.

---

## Permission-Based Tool Guards

Check `ctx.auth.permissions` or `ctx.auth.user.roles` to enforce access control:

```typescript
import { error, text } from 'mcp-use/server';

server.tool({
  name: 'delete-document',
  schema: z.object({ documentId: z.string() }),
}, async ({ documentId }, ctx) => {
  if (!ctx.auth.permissions?.includes('delete:documents')) {
    return error('Forbidden: delete:documents permission required');
  }
  await db.documents.delete({ id: documentId });
  return text('Document deleted');
});
```

### Role Guard (Keycloak)

```typescript
if (!ctx.auth.user.roles?.includes('admin')) {
  return error('Forbidden: admin role required');
}
```

### Organization-Scoped Access (WorkOS)

```typescript
const orgId = ctx.auth.payload.org_id as string;
if (!orgId) return error('No organization context');
const data = await db.data.findMany({ where: { organizationId: orgId } });
```

---

## Environment Variables Reference

| Provider | Variable | Required | Purpose |
|---|---|---|---|
| Auth0 | `MCP_USE_OAUTH_AUTH0_DOMAIN` | Yes | Tenant domain |
| Auth0 | `MCP_USE_OAUTH_AUTH0_AUDIENCE` | Yes | API identifier / audience URI |
| WorkOS | `MCP_USE_OAUTH_WORKOS_SUBDOMAIN` | Yes | AuthKit domain |
| WorkOS | `MCP_USE_OAUTH_WORKOS_CLIENT_ID` | No | Pre-registered OAuth client ID |
| WorkOS | `MCP_USE_OAUTH_WORKOS_API_KEY` | No | API key for WorkOS API calls |
| Supabase | `MCP_USE_OAUTH_SUPABASE_PROJECT_ID` | Yes | Project ID |
| Supabase | `MCP_USE_OAUTH_SUPABASE_JWT_SECRET` | No | JWT secret (HS256 only) |
| Keycloak | `MCP_USE_OAUTH_KEYCLOAK_SERVER_URL` | Yes | Keycloak server URL |
| Keycloak | `MCP_USE_OAUTH_KEYCLOAK_REALM` | Yes | Realm name |
| Keycloak | `MCP_USE_OAUTH_KEYCLOAK_CLIENT_ID` | No | Client ID |

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
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthAuth0Provider(),
  allowedOrigins: ['https://app.example.com'],
});
```

### Scope & Data Isolation
- **Scope data queries** to `ctx.auth.user.userId` or organization ID from `ctx.auth.payload`.
- **Enable `verifyJwt: true` in production** (it is the default).

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
| `permissions` is empty | Scopes not configured | Add permissions in provider settings |
| `org_id` missing | Not using WorkOS or no org | Assign user to a WorkOS organization; read from `ctx.auth.payload.org_id` |

### Debugging Auth Locally

```typescript
// Remove before deploying to production
server.tool({
  name: 'debug-auth',
}, async (_params, ctx) => object({
  hasAuth: !!ctx.auth,
  userId: ctx.auth?.user.userId ?? 'none',
  scopes: ctx.auth?.scopes ?? [],
  permissions: ctx.auth?.permissions ?? [],
}));
```

---

## Summary

1. Pick a provider — `oauthAuth0Provider()`, `oauthWorkOSProvider()`, `oauthSupabaseProvider()`, `oauthKeycloakProvider()`, or `oauthCustomProvider()`.
2. Set the required `MCP_USE_OAUTH_*` environment variables (or pass config explicitly).
3. Access verified identity via `ctx.auth.user` (`UserInfo`) in tool handlers.
4. Access raw JWT claims via `ctx.auth.payload` for provider-specific fields.
5. Guard operations with `ctx.auth.permissions` / `ctx.auth.user.roles`.
