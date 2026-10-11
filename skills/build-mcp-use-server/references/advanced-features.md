# Advanced Features

*Authoritative guide for OpenAPI generation, proxying, notifications, subscriptions, and elicitation in mcp-use v2.*

Official documentation:
- [OpenAPI Integration](https://docs.mcp-use.com/v2/typescript/server/openapi)
- [Proxy Servers](https://docs.mcp-use.com/v2/typescript/server/proxy)
- [Notifications](https://docs.mcp-use.com/v2/typescript/server/notifications)
- [Subscriptions](https://docs.mcp-use.com/v2/typescript/server/subscriptions)
- [Elicitation](https://docs.mcp-use.com/v2/typescript/server/elicitation)

---

## 1. OpenAPI-Generated Tools

Use `MCPServer.fromOpenAPI()` with a parsed, dereferenced OpenAPI 3.x document:

```ts
import { MCPServer } from "mcp-use";
import spec from "./openapi.json" with { type: "json" };

const server = await MCPServer.fromOpenAPI({
  name: "petstore-mcp",
  version: "1.0.0",
  spec,
  baseUrl: process.env.API_BASE_URL || "https://api.petstore.com",
  tags: ["pets", "orders"], // include specific tags
  exclude: ["internal-*"],  // exclude operations
});

export default server;
```

---

## 2. Proxy MCP Servers

`server.proxy()` requires `@mcp-use/client`. Call it before `listen()` or the first `fetch()` request:

```ts
import { MCPServer } from "mcp-use";

const server = new MCPServer({ name: "gateway", version: "1.0.0" });

await server.proxy({
  github: {
    url: "https://mcp.github.com/mcp",
    headers: { Authorization: `Bearer ${process.env.GITHUB_PAT}` },
  },
});

export default server;
```

---

## 3. Request-Scoped Notifications

Send notifications only while the originating tool/prompt/resource callback is active:

```ts
await ctx.sendNotification("progress/update", { progress: 50 });
await ctx.reportProgress(50, 100, "Processing items…");
await ctx.sendLog("info", { processed: 25 }, "worker");
```

`reportProgress()` returns `false` when the caller did not supply a progress token.

---

## 4. Subscriptions & Invalidation Broadcasts

Publish cross-request cache invalidations to subscribed clients:

```ts
await server.notifyToolsChanged();
await server.notifyPromptsChanged();
await server.notifyResourcesChanged();
await server.notifyResourceUpdated("resource://inventory/stock");
```

---

## 5. Interactive Elicitation

Elicitation allows a tool to request structured user feedback or external authorization without persistent server sessions. In v2.4.3+, `ctx.elicit()` was removed in favor of explicit protocol primitives:

```ts
import { MCPServer, inputRequired, inputResponse, acceptedContent } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "ops-server", version: "1.0.0" });

const confirmSchema = z.object({
  approve: z.boolean().describe("Approve operation"),
  reason: z.string().optional(),
});

server.tool(
  {
    name: "deploy-service",
    inputSchema: z.object({ serviceId: z.string() }),
  },
  async ({ serviceId }, ctx) => {
    // Check if the user already responded in a retry round
    const response = inputResponse(ctx.inputResponses, "deploy-approval");
    if (response.kind === "elicit" && response.action !== "accept") {
      return { isError: true, content: [{ type: "text", text: "Deployment cancelled by user." }] };
    }

    const confirmation = acceptedContent(ctx.inputResponses, "deploy-approval", confirmSchema);
    if (!confirmation) {
      // 1. Form Mode: Prompt user for confirmation
      return inputRequired({
        inputRequests: {
          "deploy-approval": inputRequired.elicit({
            message: `Deploy service ${serviceId} to production?`,
            requestedSchema: confirmSchema,
          }),
        },
      });
    }

    if (!confirmation.approve) {
      return { isError: true, content: [{ type: "text", text: "Deployment rejected." }] };
    }

    // Side effects execute only after confirmed and validated input
    await deployService(serviceId, confirmation.reason);
    return { content: [{ type: "text", text: `Service ${serviceId} deployed successfully.` }] };
  },
);

export default server;
```

### URL Mode (External Authorization)
When collecting authentication or third-party confirmations, use `inputRequired.elicitUrl()`:
```ts
return inputRequired({
  inputRequests: {
    "oauth-handshake": inputRequired.elicitUrl({
      message: "Please authorize access to your GitHub repository",
      url: `https://github.com/login/oauth/authorize?client_id=...`,
    }),
  },
});
```
