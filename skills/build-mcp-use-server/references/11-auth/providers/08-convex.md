# OAuth Provider: Convex

*Read this when integrating Convex OAuth authentication for an MCP server.*

## Import & Factory

```typescript
import { MCPServer } from "mcp-use";
import { oauthConvexProvider } from "mcp-use/oauth/convex";

const server = new MCPServer({
  name: "convex-server",
  version: "1.0.0",
  oauth: oauthConvexProvider({
    authURL: process.env.MCP_USE_OAUTH_CONVEX_AUTH_URL!,
  }),
});

export default server;
```

## Architecture

Use the Convex provider when hosting your own OAuth authorization server using the Convex OAuth Provider component (`@convex-dev/oauth-provider`). MCP clients register directly with your Convex deployment through Dynamic Client Registration (DCR), and your MCP server verifies Convex-issued access tokens.

The Convex deployment provides the OAuth Provider component, login, consent, and token issuance; Convex Auth alone is not sufficient.

## Environment Variables

```bash
MCP_USE_OAUTH_CONVEX_AUTH_URL=https://your-deployment-name.convex.site/oauth
MCP_URL=https://mcp.example.com/mcp
```

This must be the base URL of your Convex OAuth Provider endpoint, without a trailing slash.

## Options

```typescript
oauthConvexProvider({
  authURL: string | URL,                // Base URL of Convex OAuth Provider component
  audience?: string,                    // Extra audience check
  resource?: string | URL,              // Canonical MCP endpoint URL
  requiredScopes?: readonly string[],   // Scopes required by bearer gate
  scopesSupported?: readonly string[],  // Scopes advertised in metadata
})
```

## User Identity in Tools

Authenticated tool calls receive the verified Convex identity on `ctx.auth`:

```typescript
server.tool(
  {
    name: "whoami",
    description: "Return the verified Convex identity for this request.",
  },
  async (_args, ctx) => {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            id: ctx.auth.user.id,
            clientId: ctx.auth.user.clientId,
            scopes: ctx.auth.scopes,
            permissions: ctx.auth.permissions,
            expiresAt: ctx.auth.expiresAt,
          }),
        },
      ],
    };
  },
);
```
