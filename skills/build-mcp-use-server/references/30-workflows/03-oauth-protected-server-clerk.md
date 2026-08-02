# Workflow: OAuth-Protected Server with Clerk

*Read this for an end-to-end workflow: scaffold, add Clerk OAuth, test protected endpoints.*

## Prerequisites

- Node.js >= 22
- Clerk account (https://dashboard.clerk.com)
- Clerk project created with Frontend API URL (e.g., `https://example-12345.clerk.accounts.dev`)

## Steps

### 1. Scaffold

```bash
npx create-mcp-use-app@2.0.0-beta.14 my-secure-server --template mcp-server --npm --install
cd my-secure-server
```

**Verify:** Basic server scaffolded.

### 2. Install Clerk Provider

```bash
npm install @mcp-use/oauth@latest
```

Or it may already be included in `mcp-use`; check with `npm ls mcp-use`.

### 3. Configure Server with Clerk OAuth

Edit `index.ts`:

```typescript
import { MCPServer, oauthClerkProvider } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "secure-server",
  version: "1.0.0",
  oauth: oauthClerkProvider({
    frontendApiUrl: process.env.CLERK_FRONTEND_API_URL || "https://example-12345.clerk.accounts.dev",
  }),
});

export const getProfile = server.tool(
  {
    name: "get-profile",
    description: "Get authenticated user profile",
    inputSchema: z.object({}),
    outputSchema: z.object({
      userId: z.string(),
      email: z.string().optional(),
      name: z.string().optional(),
    }),
  },
  async (args, ctx) => {
    // ctx.auth is available because OAuth is configured
    if (!ctx.auth) {
      return { isError: true, content: [{ type: "text", text: "Not authenticated" }] };
    }

    return {
      content: [{ type: "text", text: `User: ${ctx.auth.user.id}` }],
      structuredContent: {
        userId: ctx.auth.user.id,
        email: ctx.auth.user.email,
        name: ctx.auth.user.name,
      },
    };
  }
);

export default server;
server.listen();
```

**Verify:** `npm run typecheck` passes.

### 4. Set Environment Variables

Create `.env.local`:

```bash
CLERK_FRONTEND_API_URL=https://example-12345.clerk.accounts.dev
```

Replace with your actual Clerk Frontend API URL.

### 5. Test Locally

```bash
npm run dev
```

In Inspector (http://127.0.0.1:3000/mcp/inspector):
1. Click **Tools** → **get-profile**.
2. Click **Call** (no input args).

**Expected:** First time: 401 Unauthorized (no token). Client should open Clerk login.

**For CLI testing** (with token):

```bash
# Get a token (requires Clerk token)
# Then test with:
curl -H "Authorization: Bearer YOUR_CLERK_TOKEN" http://localhost:3000/mcp/
```

**Verify:** Response includes `userId`, `email`, `name` from authenticated user.

### 6. Deploy

```bash
npm run deploy
# Set env vars during deploy:
# mcp-use deploy --env CLERK_FRONTEND_API_URL=https://example-12345.clerk.accounts.dev
```

Or use `.env.production`:

```bash
mcp-use deploy --env-file .env.production
```

**Verify:** Deployed server rejects unauthenticated requests with 401.

## Understanding the Flow

1. **Client connects** to `https://my-secure-server.vercel.app/mcp`.
2. **Server responds** with OAuth metadata (Clerk's authorization endpoint).
3. **Client registers** dynamically with Clerk (DCR: Dynamic Client Registration).
4. **Client redirects user** to Clerk login page.
5. **User authorizes** the MCP client.
6. **Clerk issues** access token to client.
7. **Client calls MCP** with `Authorization: Bearer <token>` header.
8. **Server verifies** token via Clerk's JWKS endpoint.
9. **ctx.auth.user` is populated** with user data from token.

## Common Issues

| Issue | Solution |
|-------|----------|
| 401 from server | Ensure `CLERK_FRONTEND_API_URL` is set and correct |
| Inspector won't authenticate | Close Inspector tab; refresh to re-trigger DCR flow |
| User data is empty | Check Clerk project scopes; add `profile email` scopes if needed |
| Token expired | Clerk tokens expire; client should refresh and retry |

## Next

- Read `../11-auth/01-overview.md` for provider decision table.
- Read `../11-auth/providers/01-clerk.md` for Clerk-specific details (scopes, multi-org).
- Add permission guards to protect tools (read `../11-auth/04-permission-guards.md`).
- See `../11-auth/06-debugging-checklist.md` for troubleshooting.
