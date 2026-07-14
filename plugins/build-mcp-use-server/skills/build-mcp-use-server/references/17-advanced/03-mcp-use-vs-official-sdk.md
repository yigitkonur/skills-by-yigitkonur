# mcp-use vs Official SDK

Use this comparison when deciding whether to build directly on `@modelcontextprotocol/sdk` or use `mcp-use/server` as a higher-level wrapper.

---

## Capability Matrix

| Capability | `mcp-use/server` | `@modelcontextprotocol/sdk` |
|---|---|---|
| Base protocol implementation | wraps the official SDK `McpServer` | native implementation |
| Tool API | `server.tool({ name, schema }, handler)` | `server.registerTool(name, config, handler)` |
| Registration replay across HTTP sessions | yes; registrations are stored and replayed per session | not a wrapper feature; you manage server/transport lifecycle |
| Response helpers | `text()`, `object()`, `markdown()`, `error()`, `binary()`, `widget()` | return MCP result objects directly |
| Server composition | `await server.proxy(...)` | no `proxy()` method on `McpServer` |
| HTTP routes and middleware on same instance | Hono-backed `server.use(...)` and `server.get(...)` patterns | wire your own HTTP framework/transport |
| MCP operation middleware | `server.use("mcp:tools/call", handler)` and related patterns | use lower-level request handlers/middleware |
| OAuth helpers | built-in providers and `oauthProxy` exports | lower-level OAuth provider/middleware primitives |
| Redis-backed sessions/streams | `RedisSessionStore`, `RedisStreamManager` | not built into the server wrapper |
| Widgets | MCP Apps and Apps SDK adapters plus `widget()` | not built into the core SDK |

---

## What mcp-use Adds

`mcp-use` does not replace the official SDK; it wraps it and adds production conveniences:

- A Hono app and MCP server on one object.
- Stored registrations that can be replayed into per-session SDK servers.
- Zod-first tool schemas and response helpers.
- `server.proxy()` for namespace-based aggregation of upstream MCP servers.
- OAuth provider helpers, session stores, stream managers, and widget adapters.

Pick the official SDK when you need the thinnest spec-level primitive or are building a reusable library that should not depend on `mcp-use`.

---

## Migration Sketch

```typescript
// Before — @modelcontextprotocol/sdk
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const server = new McpServer({ name: "my-server", version: "1.0.0" });
server.registerTool(
  "greet",
  {
    description: "Greet a user",
    inputSchema: { name: z.string() },
  },
  async ({ name }) => ({
    content: [{ type: "text", text: `Hello, ${name}!` }],
  })
);

// After — mcp-use
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const app = new MCPServer({ name: "my-server", version: "1.0.0" });
app.tool(
  {
    name: "greet",
    description: "Greet a user",
    schema: z.object({ name: z.string().describe("Name to greet") }),
  },
  async ({ name }) => text(`Hello, ${name}!`)
);
```

---

## See Also

- **Migration guide** → `../28-migration/01-from-modelcontextprotocol-sdk.md`
- **Server proxy** → `01-server-proxy-and-gateway.md`
- **Next.js drop-in** → `../19-nextjs-drop-in/01-overview.md`
