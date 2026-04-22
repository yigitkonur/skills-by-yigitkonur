# Tools and Schemas

Tools are the primary capability of most MCP servers. Each tool has a name, description, input schema (Zod), optional output schema, annotations, and an async handler. Source-verified against `v1.x` branch.

## registerTool API

```typescript
server.registerTool(
  name: string,
  config: ToolConfig,
  handler: (args, extra: RequestHandlerExtra) => CallToolResult | Promise<CallToolResult>
): RegisteredTool
```

### ToolConfig fields

| Field | Type | Required | Purpose |
|---|---|---|---|
| `title` | `string` | No | Human-readable display name |
| `description` | `string` | Yes (in practice) | LLM reads this to decide when to call the tool |
| `inputSchema` | `ZodRawShape \| ZodSchema` | No | Zod schema for input validation |
| `outputSchema` | `ZodRawShape \| ZodSchema` | No | Zod schema for structured output validation |
| `annotations` | `ToolAnnotations` | No | Behavioral hints for the LLM |
| `_meta` | `Record<string, unknown>` | No | Custom metadata |

### inputSchema patterns

**ZodRawShape (preferred for simple inputs):**

```typescript
server.registerTool("search", {
  description: "Search for items",
  inputSchema: {
    query: z.string().min(1).max(200).describe("Search query"),
    limit: z.number().min(1).max(100).default(20).describe("Max results"),
    offset: z.number().min(0).default(0).describe("Pagination offset"),
  },
}, async ({ query, limit, offset }) => {
  // args are typed: { query: string, limit: number, offset: number }
});
```

The SDK wraps `ZodRawShape` into `z.object(shape)` automatically. Handler args are correctly typed.

**Full ZodSchema (for transforms, refinements, discriminated unions):**

```typescript
const InputSchema = z.object({
  date: z.string().transform((s) => new Date(s)),
  mode: z.enum(["full", "summary"]),
}).refine((data) => data.date <= new Date(), "Date cannot be in the future");

server.registerTool("report", {
  description: "Generate a report",
  inputSchema: InputSchema,
}, async (args) => {
  // args.date is a Date object (transformed)
});
```

**No input (parameterless tools):**

```typescript
server.registerTool("status", {
  description: "Get server status",
}, async (extra) => ({
  // When no inputSchema, handler receives only `extra`
  content: [{ type: "text", text: "OK" }],
}));
```

### outputSchema for structured content

When you set `outputSchema`, the handler must return `structuredContent` and the SDK validates it:

```typescript
server.registerTool("get-user", {
  description: "Get user details",
  inputSchema: { id: z.string() },
  outputSchema: {
    name: z.string(),
    email: z.string().email(),
    role: z.enum(["admin", "user", "guest"]),
  },
}, async ({ id }) => ({
  content: [{ type: "text", text: `User ${id} found` }],
  structuredContent: { name: "Alice", email: "alice@example.com", role: "admin" },
}));
```

## Tool annotations

Annotations are behavioral hints — not security guarantees, but LLMs use them to assess risk:

```typescript
annotations: {
  readOnlyHint: true,       // Does not modify external state
  destructiveHint: false,   // Does not delete data
  idempotentHint: true,     // Repeated calls have no additional effect
  openWorldHint: false,     // Does not interact with external services
}
```

| Annotation | When true | When false |
|---|---|---|
| `readOnlyHint` | GET/read operations | POST/PUT/DELETE/write operations |
| `destructiveHint` | Deletes, overwrites, or drops data | Creates or reads without side effects |
| `idempotentHint` | Can be safely retried (GET, PUT with same data) | Creates new records on each call |
| `openWorldHint` | Calls external APIs, sends emails, interacts with outside world | Only accesses local or internal state |

Set annotations on every tool. Be accurate — incorrect annotations can lead LLMs to execute destructive operations without confirmation.

## Writing good tool descriptions

The description is what the LLM reads to decide whether to call the tool. Write it for an LLM, not a human:

**Do:**
- Describe what the tool does and what it returns
- Mention key input parameters and their purpose
- Include the domain context ("Search GitHub repositories", not just "Search")

**Don't:**
- Be vague ("Does stuff with data")
- Duplicate the tool name as the entire description
- Include implementation details the LLM doesn't need

```typescript
// Good
description: "Search for GitHub repositories by name, topic, or language. Returns repository name, description, stars, and URL for up to 30 results."

// Bad
description: "Search"
```

## Returning results

### Text content (most common)

```typescript
return {
  content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
};
```

For LLM consumption, prefer structured text (markdown tables, numbered lists) over raw JSON.

### Image content

```typescript
import { readFileSync } from "node:fs";

return {
  content: [{
    type: "image",
    data: readFileSync("chart.png").toString("base64"),
    mimeType: "image/png",
  }],
};
```

### Multiple content items

```typescript
return {
  content: [
    { type: "text", text: "## Analysis Results\n\n" + summary },
    { type: "image", data: chartBase64, mimeType: "image/png" },
    { type: "text", text: "\n\n## Raw Data\n\n" + JSON.stringify(data) },
  ],
};
```

### Resource links

Point the LLM to a resource it can read later:

```typescript
return {
  content: [{
    type: "resource_link",
    uri: "file:///path/to/report.md",
    name: "Full Report",
    mimeType: "text/markdown",
  }],
};
```

### Error results

For recoverable errors the LLM can handle (API rate limits, not-found, etc.):

```typescript
return {
  content: [{ type: "text", text: `Error: User "${id}" not found. Try searching by email instead.` }],
  isError: true,
};
```

For protocol-level errors (invalid params, internal failures):

```typescript
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";

throw new McpError(ErrorCode.InvalidParams, `Invalid date format: "${date}". Use ISO 8601.`);
```

Error messages should guide the LLM toward solutions. Include what went wrong and what to try instead.

## RegisteredTool handle

`registerTool` returns a handle for dynamic management:

```typescript
const tool = server.registerTool("feature-x", config, handler);

// Temporarily hide from tool list:
tool.disable();

// Re-enable:
tool.enable();

// Permanently remove:
tool.remove();

// Update configuration without re-registering:
tool.update({
  description: "Updated description",
  annotations: { readOnlyHint: false },
});
```

All handle methods automatically fire `sendToolListChanged()` so connected clients refresh their tool list.

## Autocomplete with completable schemas

Provide argument completion suggestions for LLMs and UIs:

```typescript
import { completable } from "@modelcontextprotocol/sdk/server/completable.js";

server.registerTool("deploy", {
  description: "Deploy to an environment",
  inputSchema: {
    environment: completable(
      z.string().describe("Target environment"),
      async (value) => ["staging", "production", "dev"].filter(e => e.startsWith(value))
    ),
  },
}, async ({ environment }) => { /* ... */ });
```

## Pagination pattern

For tools that return lists, implement cursor-based or offset-based pagination:

```typescript
server.registerTool("list-items", {
  description: "List items with pagination",
  inputSchema: {
    limit: z.number().min(1).max(100).default(20).describe("Items per page"),
    cursor: z.string().optional().describe("Pagination cursor from previous response"),
  },
}, async ({ limit, cursor }) => {
  const { items, nextCursor } = await fetchItems(limit, cursor);

  return {
    content: [{
      type: "text",
      text: JSON.stringify({
        items,
        nextCursor,
        hasMore: !!nextCursor,
      }, null, 2),
    }],
  };
});
```

## Common mistakes

| Mistake | Why it fails | Fix |
|---|---|---|
| Using `tool()` instead of `registerTool()` | Deprecated API, will be removed in v2 | Use `registerTool()` with config object |
| Raw JSON Schema instead of Zod | No runtime validation, no type inference | Use Zod schemas — SDK converts to JSON Schema |
| Missing `describe()` on Zod fields | LLM doesn't understand the parameter | Add `.describe()` to every field |
| Throwing generic `Error` | LLM can't recover from protocol errors | Use `McpError` with specific `ErrorCode` or `isError: true` |
| No annotations | LLM can't assess risk before calling | Set all 4 annotations on every tool |
| Returning bare strings | Not a valid `CallToolResult` | Wrap in `{ content: [{ type: "text", text: "..." }] }` |
