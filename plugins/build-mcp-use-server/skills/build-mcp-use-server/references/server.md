# MCPServer Class Reference

*Authoritative API reference for `MCPServer` in mcp-use v2.*

Primary sources:
- [MCPServer API Documentation](https://api-reference.mcp-use.com/classes/mcp-use.index.MCPServer.html)
- [mcp-use Server Guide](https://docs.mcp-use.com/v2/typescript/server)

---

## 1. Constructor

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer<TUser = never, TEnv extends Env = Env>(config: ServerConfig<TUser>);
```

### Constructor Options (`ServerConfig`)

| Option | Type | Default | Description |
|---|---|---|---|
| `name` | `string` | *(required)* | Unique server identifier reported during negotiation. |
| `version` | `string` | *(required)* | Semantic version reported to clients. |
| `title` | `string` | `name` | Display title shown in host client interfaces. |
| `description` | `string` | `undefined` | Server description exposed in client metadata. |
| `instructions` | `string` | `undefined` | System-level workflow guidance returned during init. |
| `basePath` | `string` | `"/mcp"` | URL pathname route prefix where the MCP endpoint is mounted. |
| `host` | `string` | `"127.0.0.1"` | Bind host for `listen()`. Set `"0.0.0.0"` to serve publicly. |
| `port` | `number` | `3000` | Port for `listen()`. Pass `0` for an ephemeral port. |
| `favicon` | `string` | `undefined` | Local path relative to `public/`, or URL served at `/favicon.ico`. |
| `icons` | `Icon[]` | `undefined` | Array of MCP icons reported in implementation metadata. |
| `websiteUrl` | `string` | `undefined` | Documentation or homepage URL. |
| `allowedHosts` | `string[]` | `undefined` | Additional hostnames for DNS-rebinding protection. Setting this also activates Host validation on `server.fetch`. |
| `allowedOrigins` | `string[]` | `undefined` | Extra origins for Origin validation on non-GET/HEAD calls. |
| `legacy` | `"stateless" \| "reject"` | `"stateless"` | Behavior for legacy 2025 non-envelope requests. |
| `publicLandingPage`| `boolean` | `false` | When OAuth is active, allows viewing landing page without bearer token. |
| `logging` | `LoggingOptions` | `{ level: "info" }` | Request logger settings. Level can be `"info"`, `"debug"`, or `"trace"`. |
| `skills` | `boolean \| SkillsOptions` | `true` (auto) | Automatic discovery of `skills/` directory. |
| `requestState` | `ServerOptions["requestState"]` | `undefined` | Codec for cryptographic verification of `ctx.requestState`. |
| `cors` | `CorsOptions` | `undefined` | Automatic CORS header injection across endpoints. |
| `mixedAuth` | `boolean` | `false` | When true with OAuth configured, enables public `tools/list` discovery. |
| `oauth` | `OAuthProvider<TUser>` | `undefined` | OAuth 2.1 identity provider adapter. |

---

## 2. Server Methods

### `server.tool(definition, callback)`
Registers a callable MCP tool. Returns a `ToolRef<Name, Input, Output>` object carrying phantom types for compile-time view type safety.

```typescript
export const myTool = server.tool(
  {
    name: "calculate-total",
    title: "Calculate Order Total",
    description: "Computes subtotal, taxes, and shipping fees.",
    icons: [{ src: "icons/calc.svg", mimeType: "image/svg+xml" }],
    inputSchema: z.object({
      items: z.array(z.object({ price: z.number(), qty: z.number() })),
      taxRate: z.number().default(0.08),
    }),
    outputSchema: z.object({ total: z.number(), tax: z.number() }),
    annotations: { readOnlyHint: true, openWorldHint: false },
    visibility: "model", // "model" (default) or "app"
    view: { name: "order-summary" },
  },
  async ({ items, taxRate }, ctx) => {
    const subtotal = items.reduce((acc, i) => acc + i.price * i.qty, 0);
    const tax = subtotal * taxRate;
    const total = subtotal + tax;
    return {
      content: [{ type: "text", text: `Total: $${total.toFixed(2)}` }],
      structuredContent: { total, tax },
    };
  }
);
```

### `server.settings(options)`
Registers native ChatGPT plugin settings tools (`settings.read` and `settings.update`) and advertises the `openai/settings` capability.

```typescript
server.settings({
  fields: {
    currency: { schema: z.enum(["USD", "EUR", "GBP"]), title: "Default Currency" },
  },
  read: async (ctx) => ({ currency: "USD" }),
  update: async (patch, ctx) => ({ currency: patch.currency ?? "USD" }),
});
```

### `server.resource(definition, callback)`
Registers a static resource reachable at a stable URI:

```typescript
server.resource(
  {
    uri: "config://application",
    name: "Application Config",
    mimeType: "application/json",
  },
  async (uri, ctx) => ({
    contents: [{ uri, mimeType: "application/json", text: JSON.stringify({ env: "production" }) }],
  })
);
```

### `server.resourceTemplate(definition, callback)`
Registers a parameterized resource template with variable substitution:

```typescript
server.resourceTemplate(
  {
    uriTemplate: "users://{userId}/profile",
    name: "User Profile",
    mimeType: "application/json",
  },
  async (uri, { userId }, ctx) => ({
    contents: [{ uri, mimeType: "application/json", text: JSON.stringify({ userId, role: "admin" }) }],
  })
);
```

### `server.prompt(definition, callback)`
Registers a model prompt template with arguments schema:

```typescript
server.prompt(
  {
    name: "code-review",
    title: "Conduct Code Review",
    schema: z.object({
      language: z.string().describe("Programming language"),
      code: z.string().describe("Code snippet"),
    }),
  },
  async ({ language, code }, ctx) => ({
    messages: [
      {
        role: "user",
        content: { type: "text", text: `Review this ${language} code:\n\n${code}` },
      },
    ],
  })
);
```

### `server.use("mcp:<method>", middleware)`
Registers request-scoped MCP protocol middleware:

```typescript
server.use("mcp:tools/call", async (ctx, next) => {
  const start = Date.now();
  const res = await next();
  console.log(`${ctx.params.name} completed in ${Date.now() - start}ms`);
  return res;
});
```

### Notification Invalidation Methods
Publish changes to subscribed clients over Streamable HTTP SSE:
- `await server.notifyToolsChanged()`
- `await server.notifyResourcesChanged()`
- `await server.notifyPromptsChanged()`
- `await server.notifyResourceUpdated(uri: string)`

### `server.listen(port?, options?)`
Starts the Node HTTP listener:
```typescript
const { port, url } = await server.listen(3000);
```

### `server.fetch(request, env?, executionCtx?)`
Standard web-fetch handler for serverless environments (Cloudflare Workers, Vercel, Supabase Functions, Hono).

---

## 3. Request Context (`RequestContext`)

Every callback receives a request-scoped `ctx` object:
- `ctx.signal`: `AbortSignal` aborted if client disconnects or host cancels.
- `ctx.client.capabilities()`: Returns client capabilities object.
- `ctx.client.user()`: Returns client-reported OpenAI user hints (`locale`, `userAgent`, `location`).
- `ctx.client.supportsViews()`: Returns `true` if client supports MCP Apps UI.
- `ctx.auth`: Populated when OAuth is active (`ctx.auth.user`, `ctx.auth.scopes`, `ctx.auth.permissions`, `ctx.auth.accessToken`).
- `ctx.inputResponses`: Responses from prior `input_required` rounds.
- `ctx.requestState`: Opaque state round-tripped across `input_required` turns.
- `await ctx.reportProgress(progress, total?, message?)`: Send tool execution progress.
- `await ctx.sendLog(level, data, logger?)`: Send MCP log messages during execution.
- `await ctx.sendNotification(method, params?)`: Send custom one-way notifications.
