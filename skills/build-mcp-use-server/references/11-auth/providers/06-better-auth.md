# OAuth Provider: Better Auth

*Read this when using Better Auth as your full OAuth provider and authorization server.*

## Import & Factory

```typescript
import { oauthBetterAuthProvider } from "mcp-use/oauth/better-auth";

const oauth = oauthBetterAuthProvider({
  authURL: "https://auth.example.com/api/auth",
});
```

## Required Options

| Option | Type | Example | Notes |
|--------|------|---------|-------|
| `authURL` | `string \| URL` | `"https://auth.example.com/api/auth"` | Full Better Auth issuer URL, including base path |

## Optional Options

```typescript
oauthBetterAuthProvider({
  authURL: "...",
  resource?: string \| URL,             // Full MCP endpoint URL
  requiredScopes?: readonly string[],   // Required by bearer gate
  scopesSupported?: readonly string[],  // Advertised to clients
  resourceName?: string,                // Display name
  serviceDocumentationUrl?: URL,        // Documentation link
})
```

## User Type

```typescript
type BetterAuthOAuthUser = {
  id: string;                 // Better Auth subject ID
  email?: string;
  name?: string;
  picture?: string;
  emailVerified?: boolean;
  sessionId?: string;         // Better Auth session ID
  isAnonymous?: boolean;      // Anonymous session flag
  roles: string[];            // From access token (non-nil, may be empty)
};
```

Access in tools:

```typescript
async (input, ctx) => {
  const userId = ctx.auth.user.id;
  const email = ctx.auth.user.email;
  const isAnonymous = ctx.auth.user.isAnonymous ?? false;
  const roles = ctx.auth.user.roles;
}
```

## Environment Variables

```bash
# .env
BETTER_AUTH_URL=https://auth.example.com/api/auth
```

```typescript
const oauth = oauthBetterAuthProvider({
  authURL: process.env.BETTER_AUTH_URL!,
});
```

## Gotchas

1. **Full authURL**: Include the base path (e.g., `/api/auth`). Issuer is inferred from this URL.

2. **Complete OAuth server**: Better Auth owns registration (DCR), authorization, consent, and token issuance. The MCP server verifies JWTs from Better Auth's JWKS endpoint only.

3. **Anonymous users**: Check `isAnonymous` flag before assuming a authenticated session. Anonymous sessions have limited capabilities.

4. **Session ID**: `sessionId` is provided by Better Auth but not typically needed in stateless MCP context.

5. **Roles array**: Always present but may be empty. Use `roles.includes(...)` to check.

## Typical Setup

```typescript
import { MCPServer, oauthBetterAuthProvider } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "better-auth-server",
  oauth: oauthBetterAuthProvider({
    authURL: process.env.BETTER_AUTH_URL!,
  }),
});

server.tool({
  name: "user-profile",
  description: "Get authenticated user's profile",
  inputSchema: z.object({}),
  async (input, ctx) => {
    if (ctx.auth.user.isAnonymous) {
      return { isError: true, content: [{ type: "text", text: "Anonymous access not allowed" }] };
    }
    return {
      content: [
        {
          type: "text",
          text: `User: ${ctx.auth.user.name || ctx.auth.user.email} (${ctx.auth.user.id})`,
        },
      ],
    };
  },
});

await server.listen(3000);
```
