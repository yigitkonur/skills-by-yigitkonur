# OAuth Provider: WorkOS

*Read this when integrating WorkOS for enterprise SSO and authentication.*

## Import & Factory

```typescript
import { oauthWorkOSProvider } from "mcp-use/oauth/workos";

const oauth = oauthWorkOSProvider({
  subdomain: "example.authkit.app",
});
```

## Required Options

| Option | Type | Example | Notes |
|--------|------|---------|-------|
| `subdomain` | `string` | `"example.authkit.app"` | WorkOS AuthKit subdomain (scheme optional) |

## Optional Options

```typescript
oauthWorkOSProvider({
  subdomain: "...",
  resource?: string \| URL,             // Full MCP endpoint URL
  requiredScopes?: readonly string[],   // Required by bearer gate
  scopesSupported?: readonly string[],  // Advertised to clients
  resourceName?: string,                // Display name
  serviceDocumentationUrl?: URL,        // Documentation link
})
```

## User Type

```typescript
type WorkOSOAuthUser = {
  id: string;                 // WorkOS subject ID
  email?: string;
  emailVerified?: boolean;
  name?: string;
  preferredUsername?: string;
  firstName?: string;
  lastName?: string;
  picture?: string;
  roles: string[];            // From access token (non-nil, may be empty)
  organizationId?: string;    // Active WorkOS organization
  sessionId?: string;         // WorkOS session ID
};
```

Access in tools:

```typescript
async (input, ctx) => {
  const userId = ctx.auth.user.id;
  const org = ctx.auth.user.organizationId;
  const roles = ctx.auth.user.roles;
}
```

## Environment Variables

```bash
# .env
WORKOS_SUBDOMAIN=example.authkit.app
```

```typescript
const oauth = oauthWorkOSProvider({
  subdomain: process.env.WORKOS_SUBDOMAIN!,
});
```

## Gotchas

1. **Subdomain only**: Pass just the subdomain (e.g., `example.authkit.app`), not a full URL. The scheme is inferred.

2. **No clientId/clientSecret needed**: WorkOS AuthKit uses subdomain-based registration; no manual client credentials required.

3. **Organization context**: If user is not in an organization, `organizationId` is undefined. Check before using.

4. **Roles array**: Always present but may be empty. Use `roles.includes(...)` to check.

## Typical Setup

```typescript
import { MCPServer, oauthWorkOSProvider } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "workos-server",
  oauth: oauthWorkOSProvider({
    subdomain: process.env.WORKOS_SUBDOMAIN!,
  }),
});

server.tool({
  name: "org-users",
  description: "List users in organization",
  inputSchema: z.object({}),
  async (input, ctx) => {
    const orgId = ctx.auth.user.organizationId;
    if (!orgId) {
      return { isError: true, content: [{ type: "text", text: "No organization" }] };
    }
    return { content: [{ type: "text", text: `Org: ${orgId}` }] };
  },
});

await server.listen(3000);
```
