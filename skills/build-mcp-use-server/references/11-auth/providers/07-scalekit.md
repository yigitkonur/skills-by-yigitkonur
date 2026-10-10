# OAuth Provider: Scalekit

*Read this when integrating Scalekit for B2B enterprise authentication.*

## Import & Factory

```typescript
import { MCPServer } from "mcp-use";
import { oauthScalekitProvider } from "mcp-use/oauth/scalekit";

const server = new MCPServer({
  name: "scalekit-server",
  version: "1.0.0",
  oauth: oauthScalekitProvider(),
});

export default server;
```

## Architecture: Secret-less Resource Server

Use `oauthScalekitProvider` when Scalekit is the authorization server. MCP clients register directly with Scalekit via Dynamic Client Registration (DCR). mcp-use verifies Scalekit access tokens against the resource ID. **The resource server does not hold a client secret.**

## Environment Variables

```bash
MCP_USE_OAUTH_SCALEKIT_ENVIRONMENT_URL=https://your-env.scalekit.dev
MCP_USE_OAUTH_SCALEKIT_RESOURCE_ID=res_your_resource
MCP_URL=https://mcp.example.com/mcp
```

## Options

You can also configure options directly in code:

```typescript
oauthScalekitProvider({
  environmentUrl: "https://your-env.scalekit.dev",
  resourceId: "res_your_resource",
  audience?: string,                    // Extra audience claim that must also appear in aud
  resource?: string | URL,              // Full MCP endpoint URL (default: MCP_URL combined with basePath)
  requiredScopes?: readonly string[],   // Scopes required by bearer gate
  scopesSupported?: readonly string[],  // Scopes advertised to clients
})
```

`resourceId` is the primary JWT audience. Optional `audience` is an extra value that must also appear in `aud`; it does not replace the resource-id check.

Authorization-server metadata advertises the resource-scoped issuer (`{environmentUrl}/resources/{resourceId}`). The verifier accepts both the environment-root issuer and the resource-scoped issuer so tokens issued during Scalekit's issuer migration still verify. A token minted for a different `res_…` in the same environment is rejected.

## Caller Identity Shape

Scalekit maps `sub` to `ctx.auth.user.id`. `subjectType` is `"machine"` only when `sub` equals `client_id` or `azp`. User tokens also carry a host `client_id`, so presence of that claim is not a machine signal. Optional `org_id` and `sid` become `organizationId` and `sessionId`. Token permissions are top-level `ctx.auth.permissions`. Custom claims and every other JWT field are on `ctx.auth.payload`.

```typescript
server.tool(
  {
    name: "whoami",
    description: "Return the authenticated Scalekit caller.",
  },
  async (_args, ctx) => {
    if (ctx.auth.user.subjectType === "machine") {
      return {
        isError: true,
        content: [{ type: "text", text: "User session required" }],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            id: ctx.auth.user.id,
            organizationId: ctx.auth.user.organizationId,
            scopes: ctx.auth.scopes,
            permissions: ctx.auth.permissions,
          }),
        },
      ],
    };
  },
);
```
