# OAuth Provider: Keycloak

*Read this when integrating self-hosted or managed Keycloak for fine-grained authentication and authorization.*

## Import & Factory

```typescript
import { oauthKeycloakProvider } from "mcp-use/oauth/keycloak";

const oauth = oauthKeycloakProvider({
  serverUrl: "https://keycloak.example.com",
  realm: "production",
});
```

## Required Options

| Option | Type | Example | Notes |
|--------|------|---------|-------|
| `serverUrl` | `string \| URL` | `"https://keycloak.example.com"` | Base Keycloak server URL (no trailing slash) |
| `realm` | `string` | `"production"` | Realm that issues accepted access tokens |

## Optional Options

```typescript
oauthKeycloakProvider({
  serverUrl: "...",
  realm: "...",
  resource?: string \| URL,             // Full MCP endpoint URL
  requiredScopes?: readonly string[],   // Required by bearer gate (default: ["openid", "profile"])
  scopesSupported?: readonly string[],  // Advertised to clients
  resourceName?: string,                // Display name
  serviceDocumentationUrl?: URL,        // Documentation link
})
```

## User Type

```typescript
type KeycloakOAuthUser = {
  id: string;                 // Keycloak subject ID
  email?: string;
  name?: string;
  preferredUsername?: string;
  givenName?: string;
  familyName?: string;
  emailVerified?: boolean;
  roles: string[];            // Realm roles from realm_access.roles (non-nil, may be empty)
  realmAccess?: Record<string, unknown>;       // Raw realm_access claim
  resourceAccess?: Record<string, unknown>;    // Raw resource_access claim
};
```

Access in tools:

```typescript
async (input, ctx) => {
  const userId = ctx.auth.user.id;
  const username = ctx.auth.user.preferredUsername;
  const isAdmin = ctx.auth.user.roles.includes("admin");
  
  // Fine-grained resource roles (e.g., "mcp-server" app)
  const appRoles = ctx.auth.user.resourceAccess?.["mcp-server"]?.roles;
}
```

## Environment Variables

```bash
# .env
KEYCLOAK_SERVER_URL=https://keycloak.example.com
KEYCLOAK_REALM=production
```

```typescript
const oauth = oauthKeycloakProvider({
  serverUrl: process.env.KEYCLOAK_SERVER_URL!,
  realm: process.env.KEYCLOAK_REALM!,
});
```

## Gotchas

1. **Server URL**: No trailing slash. Issuer is auto-derived as `https://keycloak.example.com/realms/production`.

2. **Realm matters**: Tokens from a different realm won't verify. Double-check realm name matches your Keycloak setup.

3. **Roles structure**: `roles` contains only realm roles. For app-specific roles, extract from `resourceAccess`:
   ```typescript
   const mcpRoles = ctx.auth.user.resourceAccess?.["my-mcp-app"]?.roles ?? [];
   ```

4. **Default scopes**: If you don't set `requiredScopes` or `scopesSupported`, Keycloak advertises `["openid", "profile"]` by default.

## Typical Setup

```typescript
import { MCPServer, oauthKeycloakProvider } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "keycloak-server",
  oauth: oauthKeycloakProvider({
    serverUrl: process.env.KEYCLOAK_SERVER_URL!,
    realm: process.env.KEYCLOAK_REALM!,
    scopesSupported: ["openid", "profile", "email"],
  }),
});

server.tool({
  name: "admin-panel",
  description: "Admin tools (realm admins only)",
  inputSchema: z.object({}),
  async (input, ctx) => {
    if (!ctx.auth.user.roles.includes("admin")) {
      return { isError: true, content: [{ type: "text", text: "admin role required" }] };
    }
    return { content: [{ type: "text", text: "Admin access granted" }] };
  },
});

await server.listen(3000);
```
