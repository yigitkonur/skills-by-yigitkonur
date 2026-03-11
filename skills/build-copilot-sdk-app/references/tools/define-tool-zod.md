# Tool Definition with Zod Schemas

## `defineTool` Function Signature

```typescript
import { defineTool } from "@github/copilot-sdk";

function defineTool<T = unknown>(
    name: string,
    config: {
        description?: string;
        parameters?: ZodSchema<T> | Record<string, unknown>;
        handler: ToolHandler<T>;
        overridesBuiltInTool?: boolean;
    }
): Tool<T>
```

`defineTool` is a **required** helper when using Zod schemas. Without it, TypeScript cannot infer handler argument types from Zod schemas. The generic `T` is inferred from the `parameters` schema's `_output` type.

The returned `Tool<T>` object: `{ name, description?, parameters?, handler, overridesBuiltInTool? }`.

## Handler Function Signature

```typescript
type ToolHandler<TArgs = unknown> = (
    args: TArgs,
    invocation: ToolInvocation
) => Promise<unknown> | unknown;
```

The `invocation` parameter carries runtime context:
```typescript
interface ToolInvocation {
    sessionId: string;    // ID of the active session
    toolCallId: string;   // Unique ID for this specific call
    toolName: string;     // Name of the tool being invoked
    arguments: unknown;   // Raw unparsed arguments (pre-Zod parsing)
}
```

Use `invocation.sessionId` to correlate tool calls with session state. Use `invocation.toolCallId` for deduplication in retry scenarios.

## Zod v4 Schema Patterns

Install Zod: `npm install zod`. Import: `import { z } from "zod"`.

### Basic scalar fields

```typescript
const tool = defineTool("search_files", {
    description: "Search files by keyword",
    parameters: z.object({
        query: z.string().describe("Search term to match against file contents"),
        maxResults: z.number().describe("Maximum number of results to return"),
        caseSensitive: z.boolean().describe("Whether to match case exactly"),
    }),
    handler: ({ query, maxResults, caseSensitive }) => {
        // query: string, maxResults: number, caseSensitive: boolean — fully typed
        return `Found 0 results for: ${query}`;
    },
});
```

### Optional fields

```typescript
const tool = defineTool("create_file", {
    description: "Create a file with optional content",
    parameters: z.object({
        path: z.string().describe("Absolute path for the new file"),
        content: z.string().optional().describe("Initial file contents"),
        encoding: z.string().optional().describe("File encoding, defaults to utf-8"),
    }),
    handler: ({ path, content, encoding }) => {
        // content: string | undefined
        // encoding: string | undefined
        const body = content ?? "";
        return { created: path, bytes: body.length };
    },
});
```

### Enums

```typescript
const tool = defineTool("set_log_level", {
    description: "Set the application log level",
    parameters: z.object({
        level: z.enum(["debug", "info", "warning", "error"]).describe("Log verbosity level"),
    }),
    handler: ({ level }) => {
        // level: "debug" | "info" | "warning" | "error"
        return `Log level set to ${level}`;
    },
});
```

### Arrays and nested objects

```typescript
const tool = defineTool("db_query", {
    description: "Performs a typed database query",
    parameters: z.object({
        query: z.object({
            table: z.string().describe("Table name to query"),
            ids: z.array(z.number()).describe("List of row IDs to fetch"),
            sortAscending: z.boolean().describe("Sort direction"),
        }),
    }),
    handler: ({ query }, invocation) => {
        // query.table: string, query.ids: number[], query.sortAscending: boolean
        // invocation.sessionId available for session-scoped state
        return [{ id: query.ids[0], name: "example" }];
    },
});
```

### Complex nested schemas

```typescript
const tool = defineTool("send_notification", {
    description: "Send a structured notification",
    parameters: z.object({
        recipient: z.object({
            email: z.string().describe("Recipient email address"),
            name: z.string().optional().describe("Display name"),
        }),
        message: z.object({
            subject: z.string().describe("Notification subject line"),
            body: z.string().describe("Notification body text"),
            priority: z.enum(["low", "normal", "high"]).describe("Delivery priority"),
        }),
        tags: z.array(z.string()).optional().describe("Optional categorization tags"),
    }),
    handler: ({ recipient, message, tags }) => {
        return {
            sent: true,
            to: recipient.email,
            subject: message.subject,
            tagCount: tags?.length ?? 0,
        };
    },
});
```

## Return Value Types

Handlers can return any of these types. The SDK serializes non-string returns to JSON before sending to the model.

### Return a plain string

```typescript
handler: ({ input }) => `Processed: ${input}`
// Sent to model as-is
```

### Return a serializable object

```typescript
handler: ({ city }) => ({
    city,
    temperature: "72°F",
    condition: "sunny",
})
// Serialized to JSON string for the model
```

### Return a `ToolResultObject` for structured results

```typescript
import type { ToolResultObject } from "@github/copilot-sdk";

handler: ({ city }): ToolResultObject => ({
    textResultForLlm: `Weather in ${city}: 72°F, sunny`,
    resultType: "success",
    // Optional: attach binary data (images, PDFs, etc.)
    binaryResultsForLlm: [],
    // Optional: structured error message
    error: undefined,
    // Optional: session log for debugging
    sessionLog: `Fetched weather for ${city} at ${Date.now()}`,
    // Optional: telemetry metadata
    toolTelemetry: { apiCallMs: 42 },
})
```

See `tool-results-and-errors.md` for full `ToolResultObject` documentation.

### Return a Promise

```typescript
handler: async ({ url }) => {
    const response = await fetch(url);
    return response.text();
}
// Both sync and async handlers are supported
```

## Registering Multiple Tools in SessionConfig

Pass all tools in the `tools` array when creating a session. The array is typed as `Tool<any>[]`.

```typescript
import { CopilotClient, defineTool, approveAll } from "@github/copilot-sdk";
import { z } from "zod";

const encryptTool = defineTool("encrypt_string", {
    description: "Encrypts a string using ROT13",
    parameters: z.object({
        input: z.string().describe("String to encrypt"),
    }),
    handler: ({ input }) => input.toUpperCase(),
});

const lookupTool = defineTool("lookup_user", {
    description: "Looks up user information by ID",
    parameters: z.object({
        userId: z.number().describe("Numeric user ID"),
        fields: z.array(z.string()).optional().describe("Fields to include"),
    }),
    handler: async ({ userId, fields }) => {
        // async fetching pattern
        return { id: userId, name: "Alice", email: "alice@example.com" };
    },
});

const weatherTool = defineTool("get_weather", {
    description: "Gets current weather for a city",
    parameters: z.object({
        city: z.string().describe("City name"),
        units: z.enum(["celsius", "fahrenheit"]).optional().describe("Temperature units"),
    }),
    handler: ({ city, units }) => ({
        city,
        temp: units === "celsius" ? 22 : 72,
        condition: "sunny",
    }),
});

const client = new CopilotClient();
const session = await client.createSession({
    onPermissionRequest: approveAll,
    tools: [encryptTool, lookupTool, weatherTool],
});
```

## Tool Naming Conventions and Restrictions

- Use **snake_case** exclusively: `get_weather`, `search_files`, `create_record`.
- Names must be unique within a session's tool list.
- Built-in tool names (`grep`, `bash`, `view`, `edit`, `create_file`, `glob`) are **reserved**. Registering a tool with a built-in name without `overridesBuiltInTool: true` causes a runtime error.
- Keep names concise and verb-noun: `send_email`, `query_database`, `read_config`.
- Avoid generic names (`run`, `execute`, `process`) — the model uses the name to decide when to call the tool.

## Common Zod Schema Patterns for SDK Tools

### URL or path parameters

```typescript
parameters: z.object({
    filePath: z.string().describe("Absolute file path (must start with /)"),
    url: z.string().url().describe("Fully-qualified URL including protocol"),
})
```

### Numeric ranges

```typescript
parameters: z.object({
    limit: z.number().int().min(1).max(100).describe("Number of results, 1-100"),
    offset: z.number().int().min(0).describe("Zero-based pagination offset"),
})
```

### Discriminated unions

```typescript
parameters: z.object({
    action: z.discriminatedUnion("type", [
        z.object({ type: z.literal("create"), name: z.string() }),
        z.object({ type: z.literal("delete"), id: z.number() }),
    ]).describe("Action to perform"),
})
```

### Default values

```typescript
parameters: z.object({
    format: z.enum(["json", "csv", "text"]).default("json").describe("Output format"),
    verbose: z.boolean().default(false).describe("Enable verbose output"),
})
```

## Tool Without Parameters

Omit `parameters` entirely for side-effect-only tools:

```typescript
const statusTool = defineTool("check_service_status", {
    description: "Checks if the backend service is reachable",
    // No parameters field
    handler: async () => {
        const ok = await ping("https://api.example.com/health");
        return ok ? "Service is up" : "Service is down";
    },
});
```

## Type Inference Verification

Verify Zod inference works correctly by checking `typeof` in the handler:

```typescript
const tool = defineTool("calculate", {
    description: "Math operations",
    parameters: z.object({
        operation: z.enum(["add", "subtract", "multiply"]),
        a: z.number(),
        b: z.number(),
    }),
    handler: ({ operation, a, b }) => {
        // TypeScript infers: operation: "add" | "subtract" | "multiply"
        // a: number, b: number
        switch (operation) {
            case "add": return String(a + b);
            case "subtract": return String(a - b);
            case "multiply": return String(a * b);
        }
    },
});
```

If handler argument types appear as `unknown`, ensure you are using `defineTool` (not constructing `Tool` objects directly) and that your Zod schema implements the `ZodSchema<T>` interface (`_output: T` and `toJSONSchema(): Record<string, unknown>`).
