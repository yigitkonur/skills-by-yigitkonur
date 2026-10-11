# Advanced Features

*Authoritative guide for OpenAPI generation, Next.js drop-in, Node HTTP bridge, proxying, notifications, subscriptions, and elicitation in mcp-use v2.*

Official documentation:
- [OpenAPI Integration](https://docs.mcp-use.com/v2/typescript/server/openapi)
- [Next.js Drop-in](https://docs.mcp-use.com/v2/typescript/server/nextjs-drop-in)
- [Proxy Servers](https://docs.mcp-use.com/v2/typescript/server/proxy)
- [Notifications](https://docs.mcp-use.com/v2/typescript/server/notifications)
- [Subscriptions](https://docs.mcp-use.com/v2/typescript/server/subscriptions)
- [Elicitation](https://docs.mcp-use.com/v2/typescript/server/elicitation)

---

## 1. OpenAPI-Generated Tools (`MCPServer.fromOpenAPI`)

Use the synchronous static factory `MCPServer.fromOpenAPI()` with a parsed, dereferenced OpenAPI 3.x document:

```ts
import { MCPServer, type OpenAPIDocument } from "mcp-use";
import spec from "./openapi.json" with { type: "json" };

// Synchronous factory returns MCPServer immediately (do not await)
const server = MCPServer.fromOpenAPI({
  name: "petstore-mcp",
  version: "1.0.0",
  spec: spec as OpenAPIDocument,
  baseUrl: process.env.API_BASE_URL || "https://api.petstore.com",
  tags: ["pets", "orders"], // include specific tags
  headers: { "x-api-key": process.env.PETSTORE_API_KEY! },
  // exclude accepts OpenAPIExcludeRule objects matching operationId, path, method, or tags
  exclude: [
    { operationId: /^internal-/ },
    { path: "/internal/*" },
  ],
});

export default server;
```

> [!NOTE]
> `MCPServer.fromOpenAPI` is synchronous and returns an `MCPServer` instance directly. `baseUrl` overrides `spec.servers[0].url`; one of them is required when the document contains operations. The loader does not fetch remote external `$ref` targets; bundle external references into local `#/components/...` references before creating the server.

---

## 2. Next.js Drop-in Integration (`mcp-use/next`)

Mount an MCP server directly within the Next.js App Router using Route Handlers and compiler augmentation:

### Route Handler (`app/api/mcp/[[...path]]/route.ts`)

> [!IMPORTANT]
> Use the optional catch-all segment `[[...path]]` so nested MCP App View asset requests (`/api/mcp/_mcp-use/views/...`) resolve properly. A single-segment `[path]` route will return 404 for view bundles.

```ts
import server from "@/mcp-server";
import { createNextHandler } from "mcp-use/next";

export const { GET, POST, DELETE, OPTIONS } = createNextHandler(server);
```

### Next.js Configuration (`next.config.ts`)

Augment Next.js with `withMcpUse` to enable view compilation, static asset serving, output tracing, and CORS:

```ts
import type { NextConfig } from "next";
import { withMcpUse } from "mcp-use/next";

const nextConfig: NextConfig = {};

export default withMcpUse(nextConfig, {
  entry: "./mcp-server.ts",
  basePath: "/api/mcp",
});
```

---

## 3. Node HTTP Bridge (`mcp-use/node`)

For standalone Node.js `node:http` servers or Express applications, use `toNodeHandler(server)`:

### Vanilla Node.js `http` Server:
```ts
import { createServer } from "node:http";
import server from "./server.js";
import { toNodeHandler } from "mcp-use/node";

const handler = toNodeHandler(server);
createServer(handler).listen(3000, () => {
  console.log("MCP Server running on http://localhost:3000/mcp");
});
```

### Express Application:
```ts
import express from "express";
import server from "./server.js";
import { toNodeHandler } from "mcp-use/node";

const app = express();
// Mount on all methods at the server basePath
app.all("/mcp/*", toNodeHandler(server));
app.listen(3000);
```

---

## 4. Proxy MCP Servers (`server.proxy`)

Compose upstream MCP servers into a unified gateway using `server.proxy()`. Proxying requires the optional peer package `@mcp-use/client` (v2). Call `server.proxy()` before calling `server.listen()` or processing the first request via `server.fetch`:

```ts
import { MCPServer } from "mcp-use";

const server = new MCPServer({ name: "gateway", version: "1.0.0" });

// Automatically namespaces upstream tools (e.g. github_<tool>) and resources (github://...)
await server.proxy({
  github: {
    url: "https://mcp.github.com/mcp",
    authToken: process.env.GITHUB_PAT!, // Dedicated bearer token property
  },
  weather: {
    url: "https://weather.example.com/mcp",
    authToken: process.env.WEATHER_MCP_TOKEN!,
  },
});

export default server;
```

> [!NOTE]
> In `mcp-use` v2, proxying automatically namespaces upstream tools (`<key>_<toolName>`) and resources (`<key>://...`). The v2 proxy implementation does not proxy resource templates, completions, subscriptions, upstream list-change re-synchronization, or legacy push callbacks. Upstream introspection failures are logged and skipped without crashing gateway startup.

---

## 5. Request-Scoped Notifications

Send notifications only while the originating tool, prompt, or resource callback is active:

```ts
// Standard progress notification (notifications/progress)
// Returns false if caller did not supply a progress token
await ctx.reportProgress(50, 100, "Processing items…");

// Standard log notification (notifications/message, replaces deprecated ctx.log)
await ctx.sendLog("info", { processed: 25 }, "worker");

// Application-defined custom notification
await ctx.sendNotification("custom/analytics", { event: "step_completed" });
```

> [!IMPORTANT]
> Request notifications are delivered on the originating request’s active response SSE stream before the final result envelope. Always `await` notification promises before returning from the callback. Because v2 is stateless, there is no session-bound or post-response push channel; notifications cannot be scheduled after the request finishes.

---

## 6. Subscriptions & Invalidation Broadcasts

Publish cross-request cache invalidations to active listener clients via SSE:

```ts
await server.notifyToolsChanged();
await server.notifyPromptsChanged();
await server.notifyResourcesChanged();
await server.notifyResourceUpdated("resource://inventory/stock");
```

> [!NOTE]
> Subscriptions and invalidation broadcasts are strictly listener-bound and non-durable over stateless HTTP. The server does not maintain session-bound queues or replay missed events when a client reconnects.

---

## 7. Interactive Elicitation (`inputRequired`, `inputResponse`, `acceptedContent`)

Elicitation allows a tool to request structured user feedback or external authorization without persistent server sessions. In `mcp-use` **v2.0.0** (August 2026), session-based `ctx.elicit()` was removed in favor of a stateless request/retry round trip:

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
    // 1. Inspect user response from a previous retry round
    const response = inputResponse(ctx.inputResponses, "deploy-approval");
    if (response.kind === "elicit" && response.action !== "accept") {
      return { isError: true, content: [{ type: "text", text: "Deployment cancelled by user." }] };
    }

    // 2. Validate accepted content against schema
    const confirmation = acceptedContent(ctx.inputResponses, "deploy-approval", confirmSchema);
    if (!confirmation) {
      // Form Mode: Prompt user for confirmation
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

    // 3. Side effects MUST execute only AFTER confirmed and validated input
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
