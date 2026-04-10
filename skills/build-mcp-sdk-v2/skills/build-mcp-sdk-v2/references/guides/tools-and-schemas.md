# Tools and Schemas (v2)

Tools are the primary capability of MCP servers. v2 uses Zod v4 exclusively — no raw shapes, no Zod v3 compatibility.

## registerTool API

```typescript
server.registerTool<OutputArgs extends AnySchema, InputArgs extends AnySchema | undefined>(
  name: string,
  config: {
    title?: string,
    description?: string,
    inputSchema?: InputArgs,        // z.object({...}) — full Zod v4 schema
    outputSchema?: OutputArgs,      // enables structuredContent validation
    annotations?: ToolAnnotations,
    _meta?: Record<string, unknown>,
  },
  cb: ToolCallback<InputArgs>
): RegisteredTool
```

### v2 schema rules

**v2 requires full `z.object()` — raw shapes are NOT accepted:**

```typescript
import * as z from "zod/v4";

// WRONG — raw shapes don't work in v2
server.registerTool("search", {
  inputSchema: { query: z.string() },  // TypeError
}, handler);

// RIGHT — full Zod v4 schema
server.registerTool("search", {
  inputSchema: z.object({
    query: z.string().min(1).max(200).describe("Search query"),
    limit: z.number().min(1).max(100).default(20).describe("Max results"),
  }),
}, handler);
```

### Handler signature — `(args, ctx)` pattern

```typescript
// With inputSchema — handler gets (args, ctx)
server.registerTool("search", {
  inputSchema: z.object({ query: z.string() }),
}, async ({ query }, ctx) => {
  // query is typed as string (inferred from Zod)
  // ctx is ServerContext
  await ctx.mcpReq.log("info", `Searching: ${query}`);
  return { content: [{ type: "text" as const, text: "results..." }] };
});

// Without inputSchema — handler gets only (ctx)
server.registerTool("status", {
  description: "Get server status",
}, async (ctx) => {
  return { content: [{ type: "text" as const, text: "OK" }] };
});
```

### ServerContext fields available in handlers

```typescript
ctx.sessionId                     // Session ID (if HTTP transport)
ctx.mcpReq.id                    // JSON-RPC request ID
ctx.mcpReq.signal                // AbortSignal for cancellation
ctx.mcpReq.log(level, data)      // Send structured log to client
ctx.mcpReq.notify(notification)  // Send notification
ctx.mcpReq.send(request, schema) // Send sub-request (sampling, elicitation)
ctx.mcpReq.elicitInput(params)   // Request user input
ctx.mcpReq.requestSampling(params) // Request LLM completion
ctx.http?.authInfo               // OAuth auth info (HTTP only)
ctx.http?.closeSSE?.()           // Close SSE stream (polling pattern)
ctx.task?.store                  // Task store (experimental)
```

### Tool annotations

```typescript
annotations: {
  readOnlyHint: true,       // Does not modify state
  destructiveHint: false,   // Does not delete data
  idempotentHint: true,     // Repeated calls safe
  openWorldHint: false,     // No external interactions
}
```

Defaults from spec: `readOnlyHint: false`, `destructiveHint: true`, `idempotentHint: false`, `openWorldHint: true`. Set all four explicitly.

### Structured output with outputSchema

```typescript
server.registerTool("get-weather", {
  inputSchema: z.object({ city: z.string() }),
  outputSchema: z.object({
    temperature: z.number(),
    conditions: z.enum(["sunny", "cloudy", "rainy"]),
  }),
}, async ({ city }) => ({
  content: [{ type: "text" as const, text: `Weather for ${city}: 72F sunny` }],
  structuredContent: { temperature: 72, conditions: "sunny" },
}));
```

When `outputSchema` is set, `structuredContent` is validated automatically. The handler MUST return `structuredContent`.

### Returning results

```typescript
// Text
return { content: [{ type: "text" as const, text: "result" }] };

// Image
return { content: [{ type: "image" as const, data: base64, mimeType: "image/png" }] };

// Resource link (lazy reference)
return { content: [{ type: "resource_link" as const, uri: "file:///report.md", name: "Report" }] };

// Error (LLM can self-correct)
return { content: [{ type: "text" as const, text: "Error: not found" }], isError: true };
```

### RegisteredTool handle

```typescript
const tool = server.registerTool("feature", config, handler);

tool.enable();   // Show in tool list
tool.disable();  // Hide from tool list (stays registered)
tool.remove();   // Permanently unregister
tool.update({    // Update without re-registering
  name?: string | null,
  title?: string,
  description?: string,
  paramsSchema?: AnySchema,
  outputSchema?: AnySchema,
  annotations?: ToolAnnotations,
  callback?: ToolCallback,
  enabled?: boolean,
});
```

### Tool name validation

Regex: `/^[A-Za-z0-9._-]{1,128}$/`

Names outside this range trigger warnings but don't block registration. Use `service_action_resource` format (e.g., `github_search_repos`).

### Completable schemas (autocomplete)

```typescript
import { completable } from "@modelcontextprotocol/server";
import * as z from "zod/v4";

server.registerTool("deploy", {
  inputSchema: z.object({
    environment: completable(
      z.string().describe("Target environment"),
      async (value) => ["staging", "production", "dev"].filter(e => e.startsWith(value))
    ),
  }),
}, async ({ environment }) => { /* ... */ });
```

### Common v1 mistakes to avoid in v2

| v1 pattern (wrong in v2) | v2 pattern (correct) |
|---|---|
| `inputSchema: { name: z.string() }` | `inputSchema: z.object({ name: z.string() })` |
| `async (args, extra) => { extra.signal }` | `async (args, ctx) => { ctx.mcpReq.signal }` |
| `extra.authInfo` | `ctx.http?.authInfo` |
| `extra.sendNotification(n)` | `ctx.mcpReq.notify(n)` |
| `throw new McpError(ErrorCode.InvalidParams, msg)` | `throw new ProtocolError(ProtocolErrorCode.InvalidParams, msg)` |
| `import { z } from "zod"` | `import * as z from "zod/v4"` |
