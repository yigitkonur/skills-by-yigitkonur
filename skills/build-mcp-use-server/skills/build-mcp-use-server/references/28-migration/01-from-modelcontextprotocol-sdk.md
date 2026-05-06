# Migrating from `@modelcontextprotocol/sdk` to `mcp-use/server`

What changes when moving from the raw SDK to mcp-use's higher-level `MCPServer`. mcp-use wraps the SDK and adds Hono, Zod helpers, sessions, OAuth, widgets, and the `mcp-use` CLI.

---

## 1. The mental shift

| Raw SDK                        | mcp-use                              |
|--------------------------------|--------------------------------------|
| `Server` from `@modelcontextprotocol/sdk/server/index.js` | `MCPServer` from `mcp-use/server` |
| Manual `setRequestHandler` with `CallToolRequestSchema` | `server.tool(meta, handler)` |
| Manual transport wiring (`StdioServerTransport`, `SSEServerTransport`) | `server.listen()` (auto-detects runtime) |
| Hand-rolled OAuth                                    | `oauth*Provider()` + DCR-direct (default since v1.25.0) |
| You own session storage                               | `InMemorySessionStore`, `RedisSessionStore`, custom |
| Manually serve widget HTML                            | `resources/` directory auto-registered as widgets |

You keep using Zod schemas. You keep returning the same MCP content shape. Most existing logic transfers directly.

---

## 2. API delta

### Server construction

```typescript
// Raw SDK
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server({ name: "my-server", version: "1.0.0" }, {
  capabilities: { tools: {} },
});
const transport = new StdioServerTransport();
await server.connect(transport);
```

```typescript
// mcp-use
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
await server.listen();
```

`listen()` auto-detects the runtime (Node, Deno, Workers) and picks the right transport. For HTTP, `listen(port)`. For Workers/Deno Deploy, `export default { fetch: server.getHandler() }`.

### Tool registration

```typescript
// Raw SDK
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{ name: "greet", description: "...", inputSchema: { ... } }],
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  if (req.params.name === "greet") {
    return { content: [{ type: "text", text: `Hello, ${req.params.arguments.name}` }] };
  }
});
```

```typescript
// mcp-use
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

server.tool(
  { name: "greet", description: "...", schema: z.object({ name: z.string() }) },
  async ({ name }) => text(`Hello, ${name}`),
);
```

`server.tool()` handles `tools/list` and `tools/call` for you. `text()`, `error()`, `object()`, `array()`, `markdown()`, `mix()` are response helpers for the standard content shapes.

### Resources

```typescript
// Raw SDK — manual handler for ReadResourceRequestSchema
server.setRequestHandler(ReadResourceRequestSchema, async (req) => { ... });
```

```typescript
// mcp-use
server.resource(
  { name: "config", uri: "config://app" },
  async () => ({ contents: [{ uri: "config://app", text: "..." }] }),
);
```

Or use response helpers (since v1.16.4): resources can return `text()` / `object()` and mcp-use converts to `ReadResourceResult`.

### Prompts

```typescript
// mcp-use
server.prompt(
  { name: "summarize", description: "...", schema: z.object({ topic: z.string() }) },
  async ({ topic }) => text(`Summarize ${topic} in 3 bullets.`),
);
```

---

## 3. Common gotchas

| Gotcha | Detail |
|---|---|
| **Zod versions.** | mcp-use uses Zod v4 (`peerDependency` since v1.21.5). The SDK historically used Zod v3. Install `zod@^4.0.0` explicitly. |
| **Imports.** | Always `mcp-use/server`. Never reach into the underlying `@modelcontextprotocol/sdk/*` from app code. |
| **`tsconfig.json`.** | Set `"module": "node16"`, `"moduleResolution": "node16"`, `"target": "ES2022"`. mcp-use uses subpath exports — older resolutions can't find them. |
| **`package.json` type.** | `"type": "module"`. ESM-only. |
| **Session state.** | The SDK's transport gives you nothing for sessions. mcp-use ships `InMemorySessionStore` and `RedisSessionStore`. Pick one for HTTP. |
| **Tool registration order.** | Register all tools **before** `server.listen()`. The SDK was forgiving about late registration; mcp-use is not. |
| **OAuth.** | The SDK has no OAuth helpers. mcp-use has built-in providers (Auth0, WorkOS, Supabase, Keycloak, Better Auth) and `oauthProxy()`. Default since v1.25.0 is DCR-direct — see `05-dcr-vs-proxy-mode-shift.md`. |
| **CORS.** | Pass `cors` to the `MCPServer` constructor. Don't wire Hono middleware by hand for the basic case. |
| **`allowedOrigins`.** | New in v1.18.0. Set explicit origins to enable DNS rebinding protection. |
| **Stdio servers.** | If you used `StdioServerTransport`, switch to `await server.listen()` — mcp-use detects no `PORT` env and falls back to stdio cleanly. Do **not** `console.log` to stdout on stdio — that corrupts JSON-RPC frames. |

---

## 4. What you gain

- **CLI**: `mcp-use dev`, `mcp-use build`, `mcp-use start`, `mcp-use deploy` — replaces hand-rolled scripts.
- **Inspector**: `npx @mcp-use/inspector` — replaces `curl`-driven debug.
- **HMR**: `mcp-use dev` hot-reloads tools and widgets.
- **Widget framework**: drop React components into `resources/`; auto-registered as `ui://widget/*`.
- **Sessions**: in-memory or Redis, no hand-roll.
- **OAuth**: built-in providers and DCR.
- **Type generation**: `mcp-use generate-types` produces types from your tools for typed client-side usage.

---

## 5. Migration steps

1. Add `mcp-use` and `zod@^4.0.0` to `dependencies`. Keep the SDK during transition only if you have customizations on top.
2. Replace `new Server(...)` and `setRequestHandler` calls with `new MCPServer(...)` and `server.tool(...)`.
3. Replace `new StdioServerTransport()`/`SSEServerTransport()` and `server.connect(transport)` with `await server.listen()` (or `getHandler()` on Workers/Deno).
4. Move OAuth handling to a built-in provider or `oauthProxy()`.
5. Switch session storage to `InMemorySessionStore` / `RedisSessionStore`.
6. Run the Inspector against the migrated server, confirm every tool listed and callable.
7. Run `mcp-use generate-types` if you have a typed client.

---

## 6. Choosing v1 vs v2 of the underlying SDK

mcp-use abstracts over both `@modelcontextprotocol/sdk` v1 and v2. You shouldn't need to care. If you do — see `build-mcp-server-sdk-v1` and `build-mcp-server-sdk-v2` skills for direct-SDK paths.

For a typical TypeScript MCP server, **use mcp-use**. Direct SDK is a power-user choice for atypical runtimes or when you need explicit control of the transport layer.
