# OAuth Provider: Clerk

*Read this when integrating Clerk for authentication.*

## Import & Factory

```typescript
import { oauthClerkProvider } from "mcp-use/oauth/clerk";

const oauth = oauthClerkProvider({
  frontendApiUrl: "https://verb-noun-42.clerk.accounts.dev",
});
```

## Required Options

| Option | Type | Example | Notes |
|--------|------|---------|-------|
| `frontendApiUrl` | `string \| URL` | `"https://verb-noun-42.clerk.accounts.dev"` | From Clerk Dashboard → Apps → Frontend API URL |

## Optional Options

```typescript
oauthClerkProvider({
  frontendApiUrl: "...",
  audience?: string,                    // Expected access-token audience (custom claim)
  resource?: string \| URL,             // Full MCP endpoint URL (overrides host header inference)
  requiredScopes?: readonly string[],   // Scopes required by bearer gate (default: none)
  scopesSupported?: readonly string[],  // Scopes advertised to clients (default: ["profile"])
  resourceName?: string,                // Human-readable name for OAuth metadata
  serviceDocumentationUrl?: URL,        // Documentation link in OAuth metadata
})
```

## User Type

```typescript
type ClerkOAuthUser = {
  id: string;                 // Stable user ID
  email?: string;             // Primary email
  name?: string;              // Display name
  username?: string;          // Clerk username
  picture?: string;           // Profile image URL
  emailVerified?: boolean;
  organizationId?: string;    // Active Clerk organization
  organizationRole?: string;  // Role in organization (e.g., "admin", "member")
  organizationSlug?: string;  // URL slug of organization
  roles: string[];            // Organization roles as array (non-nil, may be empty)
};
```

Access in tools:

```typescript
async (input, ctx) => {
  const userId = ctx.auth.user.id;
  const org = ctx.auth.user.organizationId;
  const isAdmin = ctx.auth.user.organizationRole === "admin";
}
```

## Environment Variables

Clerk's `frontendApiUrl` is typically read from env during server startup:

```bash
# .env
CLERK_FRONTEND_API_URL=https://verb-noun-42.clerk.accounts.dev
```

```typescript
const oauth = oauthClerkProvider({
  frontendApiUrl: process.env.CLERK_FRONTEND_API_URL!,
});
```

## Gotchas

1. **Frontend API URL, not API key**: Use the public Frontend API URL from Clerk Dashboard, not your API key. It's safe to embed.

2. **Organization context**: If user is not in an organization, `organizationId`, `organizationRole`, `organizationSlug` are undefined. Check before using:
   ```typescript
   if (!ctx.auth.user.organizationId) {
     return { isError: true, content: [{ type: "text", text: "No organization" }] };
   }
   ```

3. **Roles array**: `roles` is always present but may be empty. Use `roles.includes("admin")` to check, not truthiness test.

## Typical Setup

```typescript
import { MCPServer } from "mcp-use/server";
import { oauthClerkProvider } from "mcp-use/oauth/clerk";
import { z } from "zod";

const server = new MCPServer({
  name: "org-server",
  oauth: oauthClerkProvider({
    frontendApiUrl: process.env.CLERK_FRONTEND_API_URL!,
    scopesSupported: ["profile", "email"],
  }),
});

server.tool({
  name: "org-info",
  description: "Get current user's organization",
  inputSchema: z.object({}),
  async (input, ctx) => {
    return {
      content: [
        {
          type: "text",
          text: `Org: ${ctx.auth.user.organizationSlug} (${ctx.auth.user.organizationRole})`,
        },
      ],
    };
  },
});

await server.listen(3000);
```
