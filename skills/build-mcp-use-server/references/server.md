# Server

*Authoritative guide for mcp-use v2 TypeScript MCP Servers.*

Official documentation:
- [Server Overview](https://docs.mcp-use.com/v2/typescript/server)
- [MCPServer API Reference](https://api-reference.mcp-use.com/classes/mcp-use.index.MCPServer.html)
- [Server Tools](https://docs.mcp-use.com/v2/typescript/server/tools)
- [Server Resources](https://docs.mcp-use.com/v2/typescript/server/resources)
- [Server Prompts](https://docs.mcp-use.com/v2/typescript/server/prompts)
- [Server Middleware](https://docs.mcp-use.com/v2/typescript/server/middleware)
- [Server Examples](https://docs.mcp-use.com/v2/typescript/server/examples)

---

## Project & Lifecycle

Import `MCPServer` from `mcp-use`. Default-export the server entry so `mcp-use dev`, `mcp-use build`, and `mcp-use start` can own the listener and View pipeline. Call `server.listen()` only in an explicitly standalone program, or use `server.fetch()` for Web-standard Edge runtimes.

```bash
npx create-mcp-use-app@latest my-server --template mcp-server
```

### Server Configuration Surface (`ServerConfig`)

```ts
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "catalog-server",
  version: "1.0.0",
  title: "Product Catalog",
  description: "Manage product catalog, stock levels, and search items.",
  instructions: "Use lookup-inventory before creating an order. Confirm stock availability.",
  basePath: "/mcp", // default route
  host: "127.0.0.1", // "0.0.0.0" for public hosting
  port: 3000,
  legacy: "stateless", // "stateless" (default) or "reject"
  branding: {
    websiteUrl: "https://example.com",
    icons: [
      { src: "icons/logo.svg", mimeType: "image/svg+xml", sizes: ["20x20"] }
    ],
  },
  skills: true, // Auto-discover skills/ directory (or { directory: "custom" })
  cors: {
    origin: "*",
    credentials: true,
  },
});

export default server;
```

---

## Tools

Use a Standard Schema-compatible validator such as Zod, ArkType, or Valibot. Describe fields when the description helps a client or model choose valid input. Always export static tool refs (`export const myTool = server.tool(...)`).

```ts
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "inventory", version: "1.0.0" });

export const lookupInventory = server.tool(
  {
    name: "lookup-inventory",
    title: "Lookup Inventory",
    description: "Return available inventory for one SKU",
    icons: [
      { src: "icons/inventory.svg", mimeType: "image/svg+xml", sizes: ["20x20"] },
    ],
    inputSchema: z.object({ sku: z.string().describe("Inventory SKU") }),
    outputSchema: z.object({ sku: z.string(), available: z.number().int() }),
    annotations: { readOnlyHint: true, openWorldHint: false },
    visibility: "model", // "model" (default) or "app" (hidden from LLM, visible to Views)
    view: {
      name: "inventory-card",
      description: "Interactive stock display",
    },
  },
  async ({ sku }, ctx) => {
    // Expected operational failure
    if (!sku.startsWith("SKU-")) {
      return {
        isError: true,
        content: [{ type: "text", text: `Invalid SKU format: ${sku}` }],
      };
    }

    const data = { sku, available: 42 };
    return {
      content: [{ type: "text", text: JSON.stringify(data) }],
      structuredContent: data,
      _meta: { lastSync: Date.now() },
    };
  },
);

export default server;
```

### Result Channels
- Put concise model-readable output in `content`.
- Put schema-validated JSON in `structuredContent` when `outputSchema` exists.
- Put invocation-specific, View-only data in result `_meta`; validate or narrow it in the View.
- Return `isError: true` with useful `content` for expected operational failures.
- Throw only for unexpected failures that should surface as protocol errors.

---

## Resources & Prompts

- `server.resource(definition, callback)`: for one stable URI.
- `server.resourceTemplate(definition, callback)`: for a URI family with parameters.
- Return `{ contents: [...] }`; each entry must include its URI and either text or a base64 blob.
- `server.prompt(definition, callback)`: for model-ready messages. Prompt arguments use `schema` (not `inputSchema`), and the callback returns `{ messages: [...] }`. Wrap a string field with `completable()` when clients should receive suggestions without restricting other valid strings.

---

## MCP Middleware & Request Context

Register protocol middleware with `server.use("mcp:<method>", handler)`:

```ts
server.use("mcp:tools/call", async (ctx, next) => {
  const startedAt = Date.now();
  const result = await next();
  console.log(`${ctx.params.name}: ${Date.now() - startedAt}ms`);
  return result;
});
```

Tool, resource, and prompt callbacks receive request-scoped context:
- `ctx.signal`: cancellation signal.
- `ctx.client`: self-reported client capabilities (`ctx.client.views`, `ctx.client.roots`).
- `ctx.auth`: verified identity and grants when OAuth is configured. Never use client metadata for authorization.
- `ctx.requestState`: request-scoped storage.
