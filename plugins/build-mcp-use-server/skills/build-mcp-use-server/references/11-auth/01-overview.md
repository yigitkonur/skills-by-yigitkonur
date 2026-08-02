# Authentication Overview

*Read this when you need OAuth protection and want to choose a provider.*

mcp-use v2 uses **Dynamic Client Registration (DCR)** as the primary OAuth model. Your MCP server advertises itself to upstream identity providers (Clerk, Auth0, Keycloak, Supabase, WorkOS, Better Auth), which register it as an OAuth client and issue access tokens. The server verifies bearer tokens and exposes protected endpoints.

Unauthenticated requests to `/.well-known/oauth-authorization-server` and all MCP endpoints (`/mcp/*`, including tools, resources, prompts) are rejected with 401 Unauthorized.

## Provider Decision

| Provider | Best For | Setup |
|----------|----------|-------|
| **Clerk** | Teams + modern orgs | Frontend URL → auto-DCR |
| **Auth0** | Enterprise + flexibility | Tenant domain → DCR |
| **WorkOS** | SSO + enterprise | AuthKit subdomain → DCR |
| **Supabase** | Backend + PostgreSQL | Project ID or URL → JWT verification |
| **Keycloak** | Self-hosted + fine-grained roles | Server URL + realm → DCR |
| **Better Auth** | Full auth control | Better Auth issuer URL → DCR |

See `providers/` for each provider's setup, user fields, and gotchas.

## How It Works

```typescript
import { MCPServer } from "mcp-use/server";
import { oauthClerkProvider } from "mcp-use/oauth/clerk";

const server = new MCPServer({
  name: "secure-server",
  oauth: oauthClerkProvider({
    frontendApiUrl: "https://verb-noun-42.clerk.accounts.dev",
  }),
});

server.tool({
  name: "list-secrets",
  description: "List user's secrets",
  inputSchema: z.object({}),
  async (ctx) => {
    // User is authenticated; ctx.auth.user populated
    return {
      content: [{ type: "text", text: `User: ${ctx.auth.user.id}` }],
    };
  },
});

await server.listen(3000);
```

When a client sends:
```bash
curl -H "Authorization: Bearer <access_token>" https://mcp.example.com/mcp/tools/list-secrets/call
```

The server verifies the token, extracts user info (e.g., Clerk's `id`, `email`, `organizationId`), and makes it available on `ctx.auth.user`.

## Runtime Shape

Every authenticated request populates `ctx.auth`:

```typescript
{
  user: ClerkOAuthUser | Auth0OAuthUser | ...  // provider-specific type
  payload: Record<string, unknown>   // verified token claims
  accessToken: string                // bearer token
  scopes: string[]                   // OAuth scopes on token
  permissions: string[]              // provider-mapped permissions
  clientId?: string                  // client_id or azp claim
  expiresAt: number                  // Unix time (seconds)
  resource?: URL                     // audience claim
}
```

See `references/11-auth/03-ctx-auth-and-user-context.md` for full details.

## Next Steps

1. Pick a provider from the table above
2. Read its `providers/<name>.md` file (env vars, options, user fields, gotchas)
3. Configure options and attach to `MCPServer`
4. Guard tools with permission checks if needed (see `04-permission-guards.md`)
5. Debug with Inspector or curl (see `06-debugging-checklist.md`)
