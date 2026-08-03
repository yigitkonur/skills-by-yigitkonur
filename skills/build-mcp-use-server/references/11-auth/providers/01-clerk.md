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
  audience?: string,                    // Expected access-token audience (custom claim). Omit for issuer-bound verification.
  resource?: string | URL,              // Full MCP endpoint URL (overrides host header inference)
  requiredScopes?: readonly string[],   // Scopes required by bearer gate (default: none enforced)
  scopesSupported?: readonly string[],  // Scopes advertised to clients (no factory default; provider passes through undefined)
  resourceName?: string,                // Human-readable name for OAuth metadata
  serviceDocumentationUrl?: URL,        // Documentation link in OAuth metadata
})
```

`audience` and issuer-bound verification are mutually exclusive: when `audience` is set, the provider validates that exact `aud` claim; when omitted, it falls back to issuer-bound access-token verification instead of checking `aud`. There is no built-in default for `scopesSupported` — Clerk's factory does not set `["profile"]` or any other value unless you pass it.

## User Type

```typescript
type ClerkOAuthUser = {
  id: string;                 // Clerk sub claim (stable user ID)
  email?: string;             // Primary email
  name?: string;              // Display name
  username?: string;          // Clerk username
  picture?: string;           // Profile image URL
  emailVerified?: boolean;
  organizationId?: string;    // Active Clerk organization (org_id claim)
  organizationRole?: string;  // Role in the active organization (org_role claim, e.g. "admin", "member")
  organizationSlug?: string;  // URL slug of active organization (org_slug claim)
  roles: string[];            // [organizationRole] if present, else [] — always one element or empty, not a multi-role list
};
```

`org_permissions` claims map separately to top-level `ctx.auth.permissions` (not part of `user`) — request the Clerk `user:org:read` scope to get them populated.

Access in tools:

```typescript
async (input, ctx) => {
  const userId = ctx.auth.user.id;
  const org = ctx.auth.user.organizationId;
  const isAdmin = ctx.auth.user.organizationRole === "admin";
  const canReadDocs = ctx.auth.permissions.includes("org:documents:read");
}
```

## Environment Variables

The provider does not read any environment variables itself — `frontendApiUrl` (and `audience`, if used) are plain function arguments. Reading them from `process.env` at startup is application convention, not framework behavior:

```bash
# .env
CLERK_FRONTEND_API_URL=https://verb-noun-42.clerk.accounts.dev
# Optional, only if Clerk emits a dedicated access-token audience:
CLERK_AUDIENCE=https://api.example.com
```

```typescript
const frontendApiUrl = process.env.CLERK_FRONTEND_API_URL;
if (!frontendApiUrl) throw new Error("CLERK_FRONTEND_API_URL is required");

const oauth = oauthClerkProvider({
  frontendApiUrl,
  ...(process.env.CLERK_AUDIENCE ? { audience: process.env.CLERK_AUDIENCE } : {}),
});
```

## Gotchas

1. **Frontend API URL, not API key**: Use the public Frontend API URL from Clerk Dashboard, not your API key. It's safe to embed.

2. **Enable Dynamic Client Registration**: In Clerk Dashboard, enable DCR for the application before MCP clients can register. Request `user:org:read` in the OAuth scope if tools need organization context.

3. **Organization context**: If user is not in an organization, `organizationId`, `organizationRole`, `organizationSlug` are undefined. Check before using:
   ```typescript
   if (!ctx.auth.user.organizationId) {
     return { isError: true, content: [{ type: "text", text: "No organization" }] };
   }
   ```

4. **Roles array**: `roles` derives from a single `org_role` claim — `[role]` or `[]`, never multiple entries. Use `roles.includes("admin")` to check, not truthiness test. For fine-grained permissions, use `ctx.auth.permissions` (mapped from `org_permissions`), not `roles`.

5. **`audience` vs issuer-bound verification**: passing `audience` makes the provider check that exact `aud` claim; omitting it makes the provider trust issuer-bound access tokens instead. Don't assume both checks run together — they're mutually exclusive.

## Typical Setup

```typescript
import { MCPServer } from "mcp-use";
import { oauthClerkProvider } from "mcp-use/oauth/clerk";
import { z } from "zod";

const server = new MCPServer({
  name: "org-server",
  version: "1.0.0",
  oauth: oauthClerkProvider({
    frontendApiUrl: process.env.CLERK_FRONTEND_API_URL!,
    scopesSupported: ["profile", "email", "offline_access", "user:org:read"],
  }),
});

server.tool(
  {
    name: "org-info",
    description: "Get current user's organization",
    inputSchema: z.object({}),
  },
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
);

await server.listen(3000);
```
