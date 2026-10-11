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

Import `MCPServer` from `mcp-use`. Default-export the server entry so `mcp-use dev`, `mcp-use build`, and `mcp-use start` can own the listener and View pipeline. Pass the function reference `server.fetch` directly to Web-standard Edge and Fetch-based runtimes (e.g. `export default { fetch: server.fetch }` or `export default server`). Never call `server.fetch()` with zero arguments, as invoking it without a `Request` throws a runtime `TypeError`. The v1 `server.getHandler()` method remains only as a deprecated alias. For custom Node.js HTTP servers or Express, adapt the server with `toNodeHandler(server)` from `mcp-use/node`. Call `server.listen()` only in an explicitly standalone CLI or Node.js program.

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
  basePath: "/mcp", // default route pathname
  host: "127.0.0.1", // "0.0.0.0" for public hosting
  port: 3000,
  legacy: "stateless", // "stateless" (default) or "reject"
  // Top-level branding properties (BaseServerConfig has NO nested branding object)
  websiteUrl: "https://example.com",
  icons: [
    { src: "icons/logo.svg", mimeType: "image/svg+xml", sizes: ["20x20"] }
  ],
  favicon: "icons/logo.svg", // Served at /favicon.ico (defaults to first icon)
  // Request logging configuration (or MCP_USE_LOG_LEVEL env var)
  logging: { enabled: true, level: "info" },
  // Network hardening and security
  allowedHosts: ["catalog.internal"], // Extra allowed Host headers for DNS-rebinding protection
  allowedOrigins: ["https://chatgpt.com"], // Extra allowed origins on non-GET/HEAD requests
  publicLandingPage: false, // Expose unauthenticated HTML landing page when OAuth is enabled
  skills: true, // Auto-discover skills/ directory (or { directory: "custom" })
  // CORS configuration (never combine origin: "*" with credentials: true)
  cors: {
    origin: ["https://chatgpt.com", "https://claude.ai"],
    credentials: true,
  },
});

export default server;
```

> [!NOTE]
> `BaseServerConfig` defines `websiteUrl?: string`, `icons?: Icon[]`, and `favicon?: string` directly at the top level of the configuration object. There is no `branding` configuration property; `server.branding` is a read-only getter on the `MCPServer` instance returning normalized values. Additionally, per the W3C CORS specification, setting `origin: "*"` while `credentials: true` is invalid; specify explicit origins or a validation function whenever credentials are required.

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
      content: [{ type: "text", text: `SKU ${sku}: 42 available in stock` }],
      structuredContent: data,
      _meta: { lastSync: Date.now() },
    };
  },
);

export default server;
```

### Result Channels & Raw Envelopes

Tool callbacks in v2 return raw `CallToolResult` envelopes (`{ content, structuredContent?, isError?, _meta? }`). Response helpers (`text()`, `object()`, `array()`, `widget()`, `error()`) are deprecated upgrade shims (note that native `array()` no longer wraps items in `{ data }`).

- **Token Economy in `content`**: When `outputSchema` is defined, `content` should contain a concise natural language summary for the LLM to minimize prompt token consumption. `structuredContent` delivers the typed JSON payload to both the model and the view. Stringifying the entire JSON object into `content` redundantly bloats LLM context tokens.
- **Typed Output (`structuredContent`)**: When `outputSchema` is declared on a tool, returning matching `structuredContent` is mandatory unless returning `isError: true`.
- **View Metadata (`_meta`)**: Put invocation-specific, View-only data in result `_meta`; validate or narrow it in the View.
- **Operational Failures**: Return `isError: true` with explanatory `content` for expected operational failures (e.g., item not found, validation refusal).
- **Protocol Exceptions**: Throw only for unexpected system failures that should surface as JSON-RPC protocol errors.

---

## Resources & Prompts

- `server.resource(definition, callback)`: for one stable URI.
- `server.resourceTemplate(definition, callback)`: for a URI family with parameters.
- Return `{ contents: [...] }`; each entry must include its URI and either text or a base64 blob.
- `server.prompt(definition, callback)`: for model-ready messages. Prompt arguments use `schema` (not `inputSchema`), and the callback returns `{ messages: [...] }`. Wrap a string field with `completable()` when clients should receive suggestions without restricting other valid strings.

---

## MCP Middleware, Observers & Request Context

### MCP Middleware (`server.use`)

Register protocol middleware using `server.use("mcp:<pattern>", handler)`. Middleware execution follows specific matching rules:
- **Pass-Through Wildcard (`mcp:*`)**: The `mcp:*` global wildcard is strictly pass-through. It can inspect incoming operations, log metrics, call `await next()`, or throw an error to abort the request. It **cannot** modify or replace downstream results.
- **Method-Specific Middleware**: Exact patterns (`mcp:tools/call`, `mcp:tools/list`, `mcp:resources/read`, `mcp:resources/list`, `mcp:prompts/get`, `mcp:prompts/list`) can inspect parameters, call `await next()`, and inspect or transform the method-specific result.

```ts
// 1. Pass-through audit logging
server.use("mcp:*", async (ctx, next) => {
  const startedAt = Date.now();
  await next(); // Must call next() or throw; do NOT return replacement result
  console.log(`[MCP] ${ctx.method} completed in ${Date.now() - startedAt}ms`);
});

// 2. Tool result transformation & permission check
server.use("mcp:tools/call", async (ctx, next) => {
  if (ctx.params.name.startsWith("admin_") && !ctx.auth?.permissions.includes("admin")) {
    throw new Error("Forbidden: admin permission required");
  }
  const result = await next();
  return result; // Method-specific middleware may inspect or replace result
});
```

### MCP Observers (`server.on`)

Attach read-only, non-blocking event listeners with `server.on("mcp:<pattern>", handler)`. Observers support `:complete` suffixes (e.g. `mcp:tools/call:complete`) to inspect outcomes after responses are prepared. Observer errors are logged and do not abort requests.

```ts
server.on("mcp:tools/call:complete", (event) => {
  console.log(`Tool ${event.params.name} finished with error: ${event.result.isError}`);
});
```

### Request Context (`RequestContext`)

Tool, resource, and prompt callbacks receive request-scoped context (`ctx`):
- `ctx.request`: The HonoRequest representation of the active HTTP request (replaces deprecated `ctx.req`). Raw Web Request is available at `ctx.request.raw`.
- `ctx.signal`: `AbortSignal` for client cancellation.
- `ctx.client`: `RequestClientContext` representing client capabilities. Exposes:
  - `ctx.client.supportsViews(): boolean`: Checks if the client supports interactive MCP App React views (replaces deprecated v1 `supportsApps()`).
  - `ctx.client.user(): UserContext | undefined`: Client-reported, unverified user hints (location, locale, conversation ID). **Never** use for authorization.
  - `ctx.client.info(): Partial<Implementation>`: Client implementation metadata.
- `ctx.auth`: `OAuthAuth<TUser>` representing verified OAuth identity, scopes, and permissions when OAuth is configured (`ctx.auth.user`, `ctx.auth.scopes`, `ctx.auth.permissions`).
- `ctx.requestState`: `RequestStateAccessor` for reading opaque state echoed across `input_required` elicitation rounds (`ctx.requestState.get()`). It is **not** generic request storage. Multi-request state belongs in an external database; intra-request middleware state uses `ctx.state` (`Map<string, unknown>`).
- `ctx.inputResponses`: Array of user input responses from previous elicitation retry rounds.
- `ctx.sendNotification(method, params)`: Sends custom notifications over the active response SSE stream before the callback completes. Must be awaited before returning.
- `ctx.reportProgress(progress, total?, message?)`: Standard progress notification (`notifications/progress`). Returns `false` if the client did not provide a progress token.
- `ctx.sendLog(level, data?, logger?)`: Sends an MCP log notification (replaces deprecated `ctx.log`).
