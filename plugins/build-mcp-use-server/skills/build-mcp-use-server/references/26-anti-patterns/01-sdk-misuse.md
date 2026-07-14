# SDK misuse

mcp-use wraps `@modelcontextprotocol/sdk` with Zod schema support, Streamable HTTP, session management, middleware, OAuth, widgets, and the inspector. Reaching past it into the raw SDK means re-implementing all of that — usually wrong.

## Don't import from `@modelcontextprotocol/sdk` directly

```typescript
// ❌ raw SDK — manual everything, no Zod, no HTTP
import { MCPServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
server.tool("greet", { name: { type: "string" } }, async ({ name }) => ({
  content: [{ type: "text", text: `Hello ${name}` }],
}));
const transport = new StdioServerTransport();
await server.connect(transport);
```

```typescript
// ✅ mcp-use handles transport, validation, HTTP
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
server.tool(
  { name: "greet", schema: z.object({ name: z.string().describe("User name") }) },
  async ({ name }) => text(`Hello ${name}`)
);
await server.listen(3000);
```

The only legitimate reason to import from `@modelcontextprotocol/sdk` is consuming its **type definitions** that mcp-use re-exports identically — and even then, prefer the mcp-use re-export.

## Don't construct transports manually

`server.listen(port)` sets up Streamable HTTP, sessions, CORS, the inspector, and OAuth metadata routes. Constructing a transport yourself bypasses all of that.

```typescript
// ❌ manual transport — loses sessions, SSE, CORS, middleware
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
const transport = new StdioServerTransport();
await server.connect(transport);
```

```typescript
// ✅ HTTP server
await server.listen(3000);

// ✅ serverless / edge — exported handler
export default { fetch: server.getHandler() };
```

For stdio transport (CLI clients), mcp-use exposes it through configuration, not by hand-constructing `StdioServerTransport`. See `09-transports/`.

## Don't bypass `mcp-use/server` for shared types

`mcp-use/server` re-exports the types you need. Importing the same types from the underlying SDK invites version drift — the next mcp-use upgrade may pin a different SDK.

```typescript
// ❌ direct SDK import for types
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
```

```typescript
// ✅ go through mcp-use/server
import type { CallToolResult } from "mcp-use/server";
```

## Don't build JSON Schema by hand

mcp-use auto-converts Zod schemas to JSON Schema for `tools/list`. Hand-built JSON Schema loses runtime validation, type inference, and the `.describe()` strings that guide the LLM.

```typescript
// ❌ manual JSON Schema — no validation, no types, no LLM hints
server.tool("search", {
  type: "object",
  properties: {
    query: { type: "string" },
    limit: { type: "number" },
  },
  required: ["query"],
}, handler);
```

```typescript
// ✅ Zod — validation + description + inferred types
server.tool(
  {
    name: "search",
    description: "Search records by keyword.",
    schema: z.object({
      query: z.string().describe("Search keyword"),
      limit: z.number().int().min(1).max(100).default(10).describe("Max results"),
    }),
  },
  async ({ query, limit }) => { /* limit is always a number */ }
);
```

See `04-tools/03-zod-schemas.md`.

## Don't skip declaring `zod`

Since v1.21.5, `zod` is a `peerDependency` of `mcp-use`. If you don't list it, npm may not install it and TypeScript reports phantom errors.

```json
// ❌ relying on mcp-use to bring zod
{
  "dependencies": { "mcp-use": "^1.21.5" }
}
```

```json
// ✅ explicit zod
{
  "dependencies": { "mcp-use": "^1.21.5", "zod": "^4.0.0" }
}
```

## Don't reach for `winston` (or other log libs)

Winston was removed in v1.12.0. The built-in `Logger` works in Node and browsers with zero dependencies — the same surface, cross-environment.

```typescript
// ❌ external dependency, Node-only
import winston from "winston";
```

```typescript
// ✅ built-in, cross-env (note: from root package, not /server)
import { Logger } from "mcp-use";
Logger.configure({ level: "info", format: "minimal" });
```

See `15-logging/`.

## Don't import response helpers from `@modelcontextprotocol/sdk`

Response builders (`text`, `object`, `mix`, `error`, `binary`, `image`, `audio`, `stream`, `file`, `resource`, `markdown`, `html`) are mcp-use additions. The raw SDK does not have them.

```typescript
// ❌ wrong package — these don't exist there
import { text, object } from "@modelcontextprotocol/sdk/...";
```

```typescript
// ✅
import { text, object, mix, error, stream, file } from "mcp-use/server";
```

See `05-responses/`.

## Quick checklist

| Symptom | Likely cause |
|---|---|
| Manual `transport.connect()` calls | Skipping `server.listen()` / `getHandler()` |
| `properties: { type: "string" }` literals | Hand-built JSON Schema instead of Zod |
| Importing from `@modelcontextprotocol/sdk/...` paths | Reaching past `mcp-use/server` |
| `winston`, `pino`, etc. in `dependencies` | Not using built-in `Logger` |
| TypeScript errors about Zod types | Missing `zod` in your own `dependencies` |
| Tool schema present but no validation at runtime | Tool registered without Zod object — second arg is plain JSON Schema |
