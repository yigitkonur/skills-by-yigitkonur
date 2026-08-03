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

### 2. Configure the Clerk Frontend API URL

OAuth providers ship inside `mcp-use` itself as subpath exports — there is no separate `@mcp-use/oauth` package to install. Confirm the version already present:

```bash
npm ls mcp-use
```

### 3. Configure Server with Clerk OAuth

Edit `index.ts`:

```typescript
import { MCPServer } from "mcp-use";
import { oauthClerkProvider } from "mcp-use/oauth/clerk";
import { z } from "zod";

const server = new MCPServer({
  name: "secure-server",
  version: "1.0.0",
  oauth: oauthClerkProvider({
    frontendApiUrl: process.env.CLERK_FRONTEND_API_URL || "https://example-12345.clerk.accounts.dev",
    resource: process.env.MCP_RESOURCE_URL, // Full public MCP endpoint in non-local deployments
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
```

Never call `server.listen()` here — the CLI (`mcp-use dev`/`mcp-use start`) owns the listener.

**Verify:** `npm run typecheck` passes.

### 4. Set Environment Variables

Create `.env.local`:

```bash
CLERK_FRONTEND_API_URL=https://example-12345.clerk.accounts.dev
```

Replace with your actual Clerk Frontend API URL. Local loopback serving can infer the resource endpoint. Before any non-local deploy, also set `MCP_RESOURCE_URL` to the full canonical public MCP endpoint (including `/mcp`), or set `MCP_URL` to its public origin. Without one of those, OAuth mounting through `server.fetch()` or a non-local listener fails.

### 5. Test Locally

```bash
npm run dev
```

In Inspector (http://127.0.0.1:3000/mcp/inspector):
1. Click **Tools** → **get-profile**.
2. Click **Call** (no input args).

**Expected:** First time: 401 Unauthorized (no token). Client should open Clerk login.

**Verify the HTTP auth boundary with valid protocol requests:**

```bash
export MCP_ORIGIN="http://localhost:3000"
export MCP_ENDPOINT="${MCP_ORIGIN}/mcp"

# Discovery metadata is public.
curl -i "${MCP_ORIGIN}/.well-known/oauth-protected-resource"

# The MCP route rejects a valid unauthenticated legacy initialize request.
curl -i -X POST "${MCP_ENDPOINT}" \
  -H 'Accept: application/json, text/event-stream' \
  -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'

# With a real Clerk access token, the same request reaches the MCP handler.
curl -i -X POST "${MCP_ENDPOINT}" \
  -H 'Accept: application/json, text/event-stream' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${CLERK_ACCESS_TOKEN}" \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'
```

**Verify:** discovery returns metadata; the unauthenticated POST returns 401 with `WWW-Authenticate`; the authenticated initialize returns a JSON-RPC response. Then complete the Inspector/real-client OAuth flow and call `get-profile` to verify `ctx.auth.user` mapping.

### 6. Deploy

A production OAuth server needs a canonical public resource URL. If you already control a stable domain, deploy with the full endpoint:

```bash
mcp-use deploy \
  --env CLERK_FRONTEND_API_URL=https://example-12345.clerk.accounts.dev \
  --env MCP_RESOURCE_URL=https://mcp.example.com/mcp
```

If using a generated Manufact Cloud domain, use a two-phase setup: create/link the cloud server, copy its exact MCP endpoint from the dashboard, set `MCP_RESOURCE_URL` with `mcp-use servers env set <server-id-or-slug> MCP_RESOURCE_URL=<dashboard-mcp-url>`, then redeploy. Never infer a hostname from the slug.

Capture the deployment ID and apply the terminal-state gate in `../25-deploy/platforms/01-mcp-use-cloud.md`: wait for that exact deployment to succeed and confirm its source revision before testing the dashboard-copied URL.

**Verify after terminal success:** public discovery works; an unauthenticated valid MCP POST returns 401; a real OAuth client completes login and calls `get-profile`; deployed View checks are not applicable because this workflow is tools-only.

## Understanding the Flow

1. **Client connects** to the exact public MCP endpoint copied from the deployment dashboard (never a hostname inferred from the slug).
2. **Server responds** with OAuth metadata (Clerk's authorization endpoint).
3. **Client registers** dynamically with Clerk (DCR: Dynamic Client Registration).
4. **Client redirects user** to Clerk login page.
5. **User authorizes** the MCP client.
6. **Clerk issues** access token to client.
7. **Client calls MCP** with `Authorization: Bearer <token>` header.
8. **Server verifies** token via Clerk's JWKS endpoint.
9. **`ctx.auth.user`** is populated with user data from token.

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
