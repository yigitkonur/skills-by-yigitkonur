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

## Optional Options

```typescript
oauthAuth0Provider({
  domain: "...",
  resource?: string \| URL,             // Full MCP endpoint URL
  requiredScopes?: readonly string[],   // Required by bearer gate
  scopesSupported?: readonly string[],  // Advertised to clients
  resourceName?: string,                // Display name
  serviceDocumentationUrl?: URL,        // Documentation link
})
```

## User Type

```typescript
type Auth0OAuthUser = {
  id: string;             // Auth0 subject ID
  email?: string;
  name?: string;
  nickname?: string;
  picture?: string;
  emailVerified?: boolean;
  updatedAt?: string;     // ISO timestamp of most recent update
  roles: string[];        // From access token's roles claim (non-nil, may be empty)
};
```

Access in tools:

```typescript
async (input, ctx) => {
  const userId = ctx.auth.user.id;
  const isAdmin = ctx.auth.user.roles.includes("admin");
}
```

## Environment Variables

```bash
# .env
AUTH0_DOMAIN=https://example.us.auth0.com
```

```typescript
const oauth = oauthAuth0Provider({
  domain: process.env.AUTH0_DOMAIN!,
});
```

## Gotchas

1. **Domain format**: Include the `https://` scheme and region (e.g., `.us.auth0.com`, `.eu.auth0.com`). Verify in Auth0 Dashboard → Settings → Domain.

2. **Roles from access token**: Auth0 includes roles in the access token only if you configure the application to do so. In Auth0 Dashboard → Applications → [Your App] → Roles, ensure "Add Roles to Access Token" is enabled.

3. **Roles array is always present**: Check `roles.length > 0` or `roles.includes(...)` before assuming a role.

## Typical Setup

```typescript
import { MCPServer, oauthAuth0Provider } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "auth0-server",
  oauth: oauthAuth0Provider({
    domain: process.env.AUTH0_DOMAIN!,
    scopesSupported: ["openid", "profile", "email"],
  }),
});

server.tool({
  name: "user-profile",
  description: "Get authenticated user's profile",
  inputSchema: z.object({}),
  async (input, ctx) => {
    return {
      content: [
        {
          type: "text",
          text: `User: ${ctx.auth.user.name} (${ctx.auth.user.id})`,
        },
      ],
    };
  },
});

await server.listen(3000);
```
