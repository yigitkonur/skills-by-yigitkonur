# Anti-Patterns (v2)

Common mistakes when building v2 MCP servers. Many come from carrying v1 habits.

## Using v1 import paths

```typescript
// WRONG — v1 single package
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

// RIGHT — v2 split packages
import { McpServer } from "@modelcontextprotocol/server";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
```

## Using raw Zod shapes

```typescript
// WRONG — raw shapes not accepted in v2
server.registerTool("search", {
  inputSchema: { query: z.string(), limit: z.number() },
}, handler);

// RIGHT — full z.object()
server.registerTool("search", {
  inputSchema: z.object({ query: z.string(), limit: z.number() }),
}, handler);
```

## Using v1 handler patterns

```typescript
// WRONG — v1 RequestHandlerExtra patterns
server.registerTool("my-tool", config, async (args, extra) => {
  extra.signal;              // wrong
  extra.authInfo;            // wrong
  extra.sendNotification(n); // wrong
});

// RIGHT — v2 ServerContext patterns
server.registerTool("my-tool", config, async (args, ctx) => {
  ctx.mcpReq.signal;         // correct
  ctx.http?.authInfo;        // correct
  ctx.mcpReq.notify(n);      // correct
});
```

## Using v1 error classes

```typescript
// WRONG — v1 error types
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
throw new McpError(ErrorCode.InvalidParams, "Bad input");

// RIGHT — v2 error types
import { ProtocolError, ProtocolErrorCode } from "@modelcontextprotocol/core";
throw new ProtocolError(ProtocolErrorCode.InvalidParams, "Bad input");
```

## Using v1 request handler registration

```typescript
// WRONG — v1 schema-based registration
import { CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
server.server.setRequestHandler(CallToolRequestSchema, handler);

// RIGHT — v2 string-based registration
server.server.setRequestHandler("tools/call", handler);
```

## Implementing server-side OAuth

```typescript
// WRONG — server-side OAuth removed in v2
import { mcpAuthRouter } from "@modelcontextprotocol/sdk/server/auth/router.js";
app.use(mcpAuthRouter({ provider: myProvider }));

// RIGHT — use external auth library
// v2 removes all server-side OAuth. Use better-auth, passport, etc.
```

## Using SSE server transport

```typescript
// WRONG — removed in v2
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

// RIGHT — use Streamable HTTP
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
```

## Using CommonJS

```typescript
// WRONG — CJS not supported in v2
const { McpServer } = require("@modelcontextprotocol/server");

// RIGHT — ESM only
import { McpServer } from "@modelcontextprotocol/server";
// Also set "type": "module" in package.json
```

## Logging to stdout in stdio servers

```typescript
// WRONG — stdout is JSON-RPC only
console.log("Starting server");

// RIGHT — use stderr
console.error("Starting server");

// BEST — use ctx.mcpReq.log() for structured client-visible logs
await ctx.mcpReq.log("info", "Starting processing");
```

## Missing `as const` on content type

```typescript
// WRONG — TypeScript type error
return { content: [{ type: "text", text: "result" }] };

// RIGHT — literal type assertion
return { content: [{ type: "text" as const, text: "result" }] };
```

## Importing Zod v3

```typescript
// WRONG — v2 uses Zod v4
import { z } from "zod";

// RIGHT — import Zod v4
import * as z from "zod/v4";
```
