# Authentication

Secure MCP servers with OAuth providers using built-in authentication support.

## Overview

mcp-use ships with first-class OAuth integration for common identity providers. Configure a provider once and every tool handler receives an `ctx.auth` object containing user identity, permissions, and the raw token—no manual token parsing required.

Supported providers:
- **Auth0** — `oauthAuth0Provider()`
- **WorkOS** — `oauthWorkOSProvider()`
- **Supabase** — `oauthSupabaseProvider()`
- **Custom OAuth** — `oauthCustomProvider()` for any OIDC-compliant issuer

---

## OAuth Provider Setup

### Auth0

Auth0 is the most common setup. The provider reads configuration from environment variables automatically.

```typescript
import { MCPServer, oauthAuth0Provider, object } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth: oauthAuth0Provider(),
  // Reads environment variables:
  // MCP_USE_OAUTH_AUTH0_DOMAIN
  // MCP_USE_OAUTH_AUTH0_AUDIENCE
});

server.tool(
  { name: "get-user" },
  async (_args, ctx) => object({
    userId: ctx.auth.user.userId,
    email: ctx.auth.user.email,
    permissions: ctx.auth.permissions,
  })
);
```

Set the required environment variables before starting the server:

```bash
export MCP_USE_OAUTH_AUTH0_DOMAIN="your-tenant.auth0.com"
export MCP_USE_OAUTH_AUTH0_AUDIENCE="https://api.example.com"
```

### WorkOS

WorkOS provides enterprise SSO and organization-scoped authentication.

```typescript
import { MCPServer, oauthWorkOSProvider } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth: oauthWorkOSProvider(),
  // Reads: MCP_USE_OAUTH_WORKOS_SUBDOMAIN
});
```

```bash
export MCP_USE_OAUTH_WORKOS_SUBDOMAIN="your-app"
```

WorkOS tokens include `organization_id` on the user object, enabling multi-tenant authorization patterns.

### Supabase

Use Supabase Auth for projects already built on the Supabase platform.

```typescript
import { MCPServer, oauthSupabaseProvider } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth: oauthSupabaseProvider(),
  // Reads: MCP_USE_OAUTH_SUPABASE_* env vars
});
```

```bash
export MCP_USE_OAUTH_SUPABASE_URL="https://your-project.supabase.co"
export MCP_USE_OAUTH_SUPABASE_ANON_KEY="your-anon-key"
```

### Custom OAuth

Connect any OIDC-compliant identity provider with `oauthCustomProvider()`.

```typescript
import { MCPServer, oauthCustomProvider } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth: oauthCustomProvider({
    issuerUrl: "https://auth.example.com",
    audience: "https://api.example.com",
    // Additional custom config
  }),
});
```

The `issuerUrl` must expose a `/.well-known/openid-configuration` endpoint. The provider uses OIDC discovery to resolve token validation keys and endpoints automatically.

---

## Accessing Auth Context

Every tool handler receives authentication data through `ctx.auth`. The shape of the auth object depends on the provider but follows a consistent pattern.

```typescript
server.tool(
  { name: "protected-action" },
  async (_args, ctx) => {
    // User identity
    const userId = ctx.auth.user.userId;
    const email = ctx.auth.user.email;

    // Permissions/scopes from the token
    const perms = ctx.auth.permissions;

    // Organization (WorkOS)
    const orgId = ctx.auth.user.organization_id;

    // Raw JWT for downstream API calls
    const token = ctx.auth.token;
  }
);
```

### Auth Object Reference

| Property | Type | Description |
|---|---|---|
| `ctx.auth.user.userId` | `string` | Unique user identifier from the provider |
| `ctx.auth.user.email` | `string` | User email address |
| `ctx.auth.permissions` | `string[]` | Granted permissions or scopes |
| `ctx.auth.user.organization_id` | `string \| undefined` | Organization ID (WorkOS) |
| `ctx.auth.token` | `string` | Raw bearer token for forwarding to downstream services |

### Passing Tokens to Downstream APIs

Use the raw token to call external services on behalf of the authenticated user:

```typescript
server.tool(
  { name: "fetch-orders" },
  async (_args, ctx) => {
    const response = await fetch("https://api.example.com/orders", {
      headers: {
        Authorization: `Bearer ${ctx.auth.token}`,
      },
    });
    const orders = await response.json();
    return object({ orders });
  }
);
```

---

## Permission-Based Tool Access

Check `ctx.auth.permissions` to conditionally allow or deny tool execution based on the user's granted scopes.

### Inline Permission Checks

```typescript
server.tool(
  { name: "delete-record" },
  async (args, ctx) => {
    if (!ctx.auth.permissions.includes("records:delete")) {
      return object({
        error: "Forbidden",
        message: "You do not have the 'records:delete' permission.",
      });
    }

    await db.records.delete(args.recordId);
    return object({ success: true });
  }
);
```

### Reusable Permission Guard

Extract a helper to keep tool handlers clean:

```typescript
function requirePermission(ctx: any, permission: string): void {
  if (!ctx.auth.permissions.includes(permission)) {
    throw new Error(`Missing required permission: ${permission}`);
  }
}

server.tool(
  { name: "create-invoice" },
  async (args, ctx) => {
    requirePermission(ctx, "invoices:create");
    const invoice = await billing.createInvoice(args);
    return object({ invoice });
  }
);

server.tool(
  { name: "void-invoice" },
  async (args, ctx) => {
    requirePermission(ctx, "invoices:void");
    await billing.voidInvoice(args.invoiceId);
    return object({ success: true });
  }
);
```

### Organization-Scoped Access (WorkOS)

Restrict data access to the user's organization:

```typescript
server.tool(
  { name: "list-team-members" },
  async (_args, ctx) => {
    const orgId = ctx.auth.user.organization_id;
    if (!orgId) {
      return object({ error: "No organization context" });
    }

    const members = await db.users.findMany({
      where: { organizationId: orgId },
    });
    return object({ members });
  }
);
```

---

## Environment Variables

Each provider reads its configuration from environment variables. Set these before starting the server.

| Provider | Required Environment Variables | Purpose |
|---|---|---|
| Auth0 | `MCP_USE_OAUTH_AUTH0_DOMAIN` | Auth0 tenant domain (e.g. `your-tenant.auth0.com`) |
| Auth0 | `MCP_USE_OAUTH_AUTH0_AUDIENCE` | API identifier / audience URI |
| WorkOS | `MCP_USE_OAUTH_WORKOS_SUBDOMAIN` | WorkOS application subdomain |
| Supabase | `MCP_USE_OAUTH_SUPABASE_URL` | Supabase project URL |
| Supabase | `MCP_USE_OAUTH_SUPABASE_ANON_KEY` | Supabase anonymous/public key |
| Custom | Provider-specific | Configured inline via `oauthCustomProvider()` options |

Use a `.env` file for local development and add it to `.gitignore`. Never commit secrets to version control.

---

## Security Best Practices

Follow these guidelines for production-ready authenticated servers.

### Token Handling
- **Never log tokens or credentials.** Redact `ctx.auth.token` in any logging or error output.
- **Never return raw tokens** to the client in tool responses.
- **Use environment variables** for all secrets—domain, audience, API keys.

### Transport Security
- **Use HTTPS** for all production HTTP transports. OAuth tokens sent over plain HTTP are vulnerable to interception.
- **Set explicit CORS origins.** Avoid wildcard (`*`) origins on authenticated endpoints.
- **Enable DNS rebinding protection** when serving on localhost to prevent browser-based attacks.

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth: oauthAuth0Provider(),
  http: {
    cors: {
      origin: ["https://app.example.com"],
    },
    dnsRebindingProtection: true,
  },
});
```

### Authorization
- **Validate permissions in every tool handler.** Do not rely on the client to enforce access control.
- **Scope data queries to the authenticated user.** Always filter by `userId` or `organizationId`.
- **Apply the principle of least privilege.** Request only the scopes your tools actually need.

### Secrets Management
- **Never commit `.env` files.** Add them to `.gitignore`.
- **Use platform-level secrets** in production (e.g., Cloudflare secrets, Vercel environment variables).

---

## Common Auth Issues

| Issue | Cause | Fix |
|---|---|---|
| `"Unauthorized"` on every call | Missing or expired token | Verify OAuth provider config and check token refresh flow |
| `"Invalid audience"` | Audience env var does not match the API identifier | Set `MCP_USE_OAUTH_AUTH0_AUDIENCE` to the exact API identifier in your Auth0 dashboard |
| CORS errors on OAuth redirect | Redirect URI not in allowed origins | Add the OAuth callback URL to your CORS `origin` list and provider dashboard |
| `ctx.auth` is `undefined` | No `oauth` option passed to `MCPServer` | Add the provider to the server constructor |
| `permissions` is empty | Scopes not configured in provider | Add permissions/scopes in the Auth0 API settings or WorkOS role config |
| `organization_id` is `undefined` | Not using WorkOS or user not in an org | Ensure the user is assigned to a WorkOS organization |
| Token validation fails after deploy | Clock skew or wrong issuer URL | Sync server clock (NTP) and verify `issuerUrl` matches the provider exactly |

### Debugging Auth Locally

Inspect the auth context without exposing sensitive data:

```typescript
server.tool(
  { name: "debug-auth" },
  async (_args, ctx) => object({
    hasAuth: !!ctx.auth,
    userId: ctx.auth?.user?.userId ?? "none",
    permissionCount: ctx.auth?.permissions?.length ?? 0,
    tokenPrefix: ctx.auth?.token?.substring(0, 10) + "...",
  })
);
```

Remove this tool before deploying to production.

---

## Summary

1. Pick a provider — `oauthAuth0Provider()`, `oauthWorkOSProvider()`, `oauthSupabaseProvider()`, or `oauthCustomProvider()`.
2. Set the required environment variables.
3. Access user identity and permissions via `ctx.auth` in every tool handler.
4. Guard destructive operations with explicit permission checks.
5. Follow transport and secrets best practices for production deployments.
