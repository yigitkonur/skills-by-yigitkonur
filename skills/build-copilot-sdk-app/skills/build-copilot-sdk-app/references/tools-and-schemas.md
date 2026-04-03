# Custom Tools and Schemas

## defineTool (with Zod)

The recommended way to define tools with full TypeScript inference:

```typescript
import { defineTool } from "@github/copilot-sdk";
import { z } from "zod";

const myTool = defineTool("encrypt_string", {
  description: "Encrypts a string using ROT13",
  parameters: z.object({
    input: z.string().describe("String to encrypt"),
    key: z.number().optional().describe("Encryption key"),
  }),
  handler: async ({ input, key }, invocation) => {
    // invocation.sessionId, invocation.toolCallId, invocation.toolName
    return input.toUpperCase(); // return value sent to model
  },
});
```

`defineTool` signature:
```typescript
function defineTool<T>(
  name: string,
  config: {
    description?: string;
    parameters?: ZodSchema<T> | Record<string, unknown>;
    handler: ToolHandler<T>;
    overridesBuiltInTool?: boolean;
  }
): Tool<T>
```

The SDK detects Zod v4 schemas and calls `toJSONSchema()` before sending to CLI.

### Complex parameter schemas

```typescript
// Nested objects
const searchTool = defineTool("search_code", {
  description: "Search codebase for patterns",
  parameters: z.object({
    query: z.string().describe("Search pattern or regex"),
    fileTypes: z.array(z.string()).optional().describe("File extensions to filter, e.g. ['.ts', '.js']"),
    maxResults: z.number().int().min(1).max(100).default(10).describe("Maximum results to return"),
    options: z.object({
      caseSensitive: z.boolean().default(false),
      includeTests: z.boolean().default(false),
    }).optional().describe("Search options"),
  }),
  handler: async ({ query, fileTypes, maxResults, options }) => {
    // SDK converts Zod schema to JSON Schema via toJSONSchema()
    return { results: [], total: 0 };
  },
});

// Enum parameters
const setMode = defineTool("set_mode", {
  description: "Set the operation mode",
  parameters: z.object({
    mode: z.enum(["plan", "autopilot", "interactive"]).describe("Operation mode"),
  }),
  handler: async ({ mode }) => ({ mode, applied: true }),
});
```

## Tool with raw JSON Schema

```typescript
const tools: Tool[] = [{
  name: "get_secret_number",
  description: "Gets the secret number for a key",
  parameters: {
    type: "object",
    properties: {
      key: { type: "string", description: "Lookup key" },
    },
    required: ["key"],
  },
  handler: async (args: { key: string }) => {
    return args.key === "ALPHA" ? "54321" : "unknown";
  },
}];
```

## Tool interface

```typescript
interface Tool<TArgs = unknown> {
  name: string;
  description?: string;
  parameters?: ZodSchema<TArgs> | Record<string, unknown>;
  handler: ToolHandler<TArgs>;
  overridesBuiltInTool?: boolean; // must be true to replace built-in tools
}
```

## ToolHandler

```typescript
type ToolHandler<TArgs = unknown> = (
  args: TArgs,
  invocation: ToolInvocation,
) => Promise<unknown> | unknown;
```

### ToolInvocation

```typescript
interface ToolInvocation {
  sessionId: string;
  toolCallId: string;
  toolName: string;
  arguments: unknown;
}
```

## Return values

Handlers can return several types:

```typescript
// Plain string — sent directly to model
handler: () => "result text"

// Object — JSON.stringify'd and sent to model
handler: () => ({ cityName: "Paris", temp: 72 })

// null/undefined — sent as empty string
handler: () => null

// Structured result — full control over result type
handler: () => ({
  textResultForLlm: "File created successfully",
  resultType: "success" as const,
})
```

### ToolResultObject

```typescript
type ToolResultObject = {
  textResultForLlm: string;
  binaryResultsForLlm?: ToolBinaryResult[];
  resultType: "success" | "failure" | "rejected" | "denied";
  error?: string;
  sessionLog?: string;
  toolTelemetry?: Record<string, unknown>;
};

type ToolBinaryResult = {
  data: string;        // base64 encoded
  mimeType: string;
  type: string;
  description?: string;
};
```

### Structured tool results

For fine-grained control over what the model sees:

```typescript
import type { ToolResultObject } from "@github/copilot-sdk";

const readFile = defineTool("read_file", {
  description: "Read a file's contents",
  parameters: z.object({ path: z.string() }),
  handler: async ({ path }): Promise<ToolResultObject> => ({
    textResultForLlm: `Contents of ${path}:\n${fileContent}`,
    resultType: "success",
    toolTelemetry: { bytesRead: fileContent.length },
  }),
});
```

`ToolResultObject` fields:
| Field | Type | Purpose |
|-------|------|---------|
| `textResultForLlm` | `string` | The text the model sees as the tool result |
| `resultType` | `string` | Result status: `"success"`, `"failure"`, `"rejected"`, or `"denied"` |
| `toolTelemetry` | `Record<string, unknown>` | Metadata logged but not sent to model |

## Error handling in tools

If the handler throws, the SDK catches the error and sends a sanitized error to the model. The raw exception message is NOT exposed.

```typescript
handler: async (args) => {
  if (!args.key) {
    throw new Error("Key is required"); // SDK catches this
  }
  return "result";
}
```

## Override built-in tools

Set `overridesBuiltInTool: true` to shadow a built-in tool:

```typescript
const customGrep = defineTool("grep", {
  description: "Custom grep implementation",
  parameters: z.object({
    query: z.string(),
    path: z.string().optional(),
  }),
  handler: ({ query, path }) => `CUSTOM_GREP: ${query} in ${path}`,
  overridesBuiltInTool: true, // required to replace "grep"
});
```

Without `overridesBuiltInTool: true`, registering a tool with a built-in name will error.

## Controlling available tools

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  // Only allow these built-in tools (overrides excludedTools):
  availableTools: ["view", "edit", "bash"],
  // Or exclude specific tools:
  excludedTools: ["grep", "glob"],
  // Custom tools are always available regardless of these lists:
  tools: [myTool],
});
```

- `availableTools` is an allowlist — only listed built-in tools are exposed
- `excludedTools` is a blocklist — listed tools are hidden
- `availableTools` takes precedence over `excludedTools`
- Custom tools registered via `tools` are always available

## Listing available tools

```typescript
const tools = await client.rpc.tools.list({ model: "gpt-4.1" });
// [{ name, namespacedName?, description, parameters?, instructions? }]
```

## Tool execution flow (protocol v3)

1. Server sends `external_tool.requested` session event with `{ requestId, toolName, arguments, toolCallId }`
2. SDK looks up handler by `toolName`
3. Executes handler: `handler(args, { sessionId, toolCallId, toolName, arguments })`
4. Normalizes result to string (JSON.stringify if object)
5. Responds via `session.rpc.tools.handlePendingToolCall({ requestId, result })`
6. On error: responds with `{ requestId, error: message }`

## Multi-client tool architecture

When multiple clients connect to the same session, their tools are **unioned**:

```typescript
// Client 1 registers toolA
const session1 = await client1.createSession({
  tools: [toolA],
  onPermissionRequest: approveAll,
});

// Client 2 joins and registers toolB
const session2 = await client2.resumeSession(session1.sessionId, {
  tools: [toolB],
  onPermissionRequest: approveAll,
});
// Model now sees both toolA and toolB

// If client1 disconnects, toolA is removed; toolB persists
```

## Steering notes

> Common mistakes agents make with custom tools.

- **Zod is required but not bundled**. Install it separately: `npm install zod`. The SDK auto-detects Zod v4+ and calls `toJSONSchema()`.
- **Tool handler errors don't crash your process**. They're caught and sent to the model as error results. But prefer returning structured error objects over throwing.
- **Tool names must be globally unique** across all extensions loaded in the session.
- **Return plain objects** from handlers for simple cases. The SDK auto-wraps them into `ToolResultObject` with `JSON.stringify()` for `textResultForLlm`.
- **`.describe()` matters**. The description strings on Zod fields become the parameter descriptions the model sees. Be specific — "City name (e.g., 'San Francisco')" not just "city".
