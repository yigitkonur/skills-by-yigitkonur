# OAuth Provider: Auth0

*Read this when integrating Auth0 for authentication.*

## Import & Factory

```typescript
import { oauthAuth0Provider } from "mcp-use/oauth/auth0";

const oauth = oauthAuth0Provider({
  domain: "https://example.us.auth0.com",
});
```

## Required Options

| Option | Type | Example | Notes |
|--------|------|---------|-------|
| `domain` | `string \| URL` | `"https://example.us.auth0.com"` | Auth0 tenant domain or issuer URL |

There is no separate `audience` option — the "audience" concept is handled by the Auth0-side API identifier (see Configure Auth0 below), not by a provider config key.

## Optional Options

```typescript
oauthAuth0Provider({
  domain: "...",
  resource?: string | URL,              // Full MCP endpoint URL (overrides host header inference)
  requiredScopes?: readonly string[],   // Scopes required by bearer gate (default: none enforced)
  scopesSupported?: readonly string[],  // Scopes advertised to clients (no factory default)
  resourceName?: string,                // Human-readable name for OAuth metadata
  serviceDocumentationUrl?: URL,        // Documentation link in OAuth metadata
})
```

## User Type

```typescript
type Auth0OAuthUser = {
  id: string;             // sub claim
  email?: string;
  name?: string;
  nickname?: string;
  picture?: string;
  emailVerified?: boolean; // email_verified claim
  updatedAt?: string;      // updated_at claim
  roles: string[];         // roles claim, normalized to a string array
};
```

Token permissions (the `permissions` claim, e.g. from an RBAC-enabled API) map separately to top-level `ctx.auth.permissions`, not to `user.roles`.

## Environment Variables

The provider does not read any environment variables itself — `domain` is a plain function argument:

```bash
AUTH0_DOMAIN=https://your-tenant.us.auth0.com
```

```typescript
const domain = process.env.AUTH0_DOMAIN;
if (!domain) throw new Error("AUTH0_DOMAIN is required");

const oauth = oauthAuth0Provider({ domain });
```

## Configure Auth0

In the Auth0 Dashboard, before wiring the provider:

1. Enable the Resource Parameter Compatibility Profile.
2. Promote the login connections MCP clients may use to domain-level connections.
3. Create an API whose identifier is the canonical MCP resource (e.g. `https://mcp.example.com/mcp`) — this is what Auth0 calls "audience", configured Auth0-side, not passed to `oauthAuth0Provider`.
4. Use the `rfc9068_profile_authz` token dialect if tools need the `permissions` claim in access tokens.

## Gotchas

1. Domain format includes `https://` scheme and region (`.us.auth0.com`, `.eu.auth0.com`)
2. There is no provider-level `audience` option — the Auth0 API identifier (created in the dashboard) must exactly match the resolved MCP resource, or token verification fails
3. Roles must be enabled in Auth0 Dashboard → Applications → Roles
4. `roles` array is always present but may be empty; check `roles.includes(...)`, and use `ctx.auth.permissions` (not `roles`) for permission-gated tools
