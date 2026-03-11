# Tool Types — `@github/copilot-sdk`

Complete reference for every tool-related type exported by the SDK.

## Import Patterns

```typescript
import { defineTool, approveAll } from "@github/copilot-sdk";
import type {
  Tool, ToolHandler, ToolInvocation, ToolResult, ToolResultObject,
  ToolResultType, ToolBinaryResult, ToolCallRequestPayload,
  ToolCallResponsePayload, ZodSchema, PermissionHandler,
  PermissionRequest, PermissionRequestResult, UserInputHandler,
  UserInputRequest, UserInputResponse,
} from "@github/copilot-sdk";
```

## `Tool<TArgs>`

The core interface for defining a tool that the model can invoke.

```typescript
interface Tool<TArgs = unknown> {
  name: string;                                              // Unique tool name (snake_case)
  description?: string;                                      // Shown to model to decide when to call it
  parameters?: ZodSchema<TArgs> | Record<string, unknown>;   // Zod schema or raw JSON Schema
  handler: ToolHandler<TArgs>;                               // Executes when the model calls the tool
  overridesBuiltInTool?: boolean;                            // Required when replacing a built-in tool
}
```

- `parameters` accepts a **Zod schema** (enables type inference on `args`) or a **raw JSON Schema object** (no inference — cast `args` manually).
- Without `overridesBuiltInTool: true`, a name collision with a built-in tool throws at registration.
## `ToolHandler<TArgs>`

Function signature for tool execution.

```typescript
type ToolHandler<TArgs = unknown> = (
  args: TArgs,               // Parsed arguments matching the parameter schema
  invocation: ToolInvocation  // Metadata about this specific tool call
) => Promise<unknown> | unknown;
```

Return a `string` for simple text results, or a `ToolResultObject` for structured results with status, errors, binary content, or telemetry.
## `ToolInvocation`

Metadata passed to every tool handler as the second argument.

```typescript
interface ToolInvocation {
  sessionId: string;     // Session this tool call belongs to — use for session-specific state
  toolCallId: string;    // Unique ID for this call — correlates with tool execution events
  toolName: string;      // Name of the tool being called (matches Tool.name)
  arguments: unknown;    // Raw arguments from the model, before schema parsing
}
```
## `ToolResult`

```typescript
type ToolResult = string | ToolResultObject;
```

- **`string`** — Simple text sent directly to the model.
- **`ToolResultObject`** — Structured result with status, error info, binary attachments, telemetry, and session logs.
## `ToolResultObject`

Structured tool result with full control over what the model sees and what gets logged.

```typescript
interface ToolResultObject {
  textResultForLlm: string;                     // Text result sent to model
  binaryResultsForLlm?: ToolBinaryResult[];     // Binary attachments (images, audio, etc.)
  resultType: ToolResultType;                    // Outcome status
  error?: string;                               // Error message (typically for "failure")
  sessionLog?: string;                          // Appended to session timeline for audit
  toolTelemetry?: Record<string, unknown>;       // Arbitrary telemetry (match counts, timings)
}
```
## `ToolBinaryResult`

Binary attachment included in a tool result (e.g. screenshots, generated images).

```typescript
type ToolBinaryResult = {
  data: string;           // Base64-encoded binary content
  mimeType: string;       // MIME type, e.g. "image/png", "audio/wav"
  type: string;           // Result type identifier, e.g. "screenshot", "chart"
  description?: string;   // Human-readable description
};
```
## `ToolResultType`

```typescript
type ToolResultType = "success" | "failure" | "rejected" | "denied";
```

| Value | Meaning |
|---|---|
| `"success"` | Tool executed successfully. Result is shown to the model. |
| `"failure"` | Expected failure. Error is shown to the model so it can recover. |
| `"rejected"` | Rejected by policy or hooks before execution. |
| `"denied"` | Denied by the permission handler. |
## `ZodSchema<T>`

Interface that any Zod schema satisfies. Used for type inference and JSON Schema conversion.

```typescript
interface ZodSchema<T = unknown> {
  _output: T;                                      // Phantom type for TypeScript inference
  toJSONSchema(): Record<string, unknown>;          // Converts to JSON Schema for the model
}
```

Zod v4 schemas satisfy this automatically — you never implement this yourself.
## `ToolCallRequestPayload`

Wire format for an incoming tool call from the model.

```typescript
interface ToolCallRequestPayload {
  sessionId: string;      // Session the tool call belongs to
  toolCallId: string;     // Unique identifier for this tool call
  toolName: string;       // Name of the tool being called
  arguments: unknown;     // Raw arguments (unparsed)
}
```
## `ToolCallResponsePayload`

Wire format for a tool call response sent back to the model.

```typescript
interface ToolCallResponsePayload {
  result: ToolResult;     // Plain string or structured ToolResultObject
}
```
## `PermissionHandler`

Callback that decides whether a tool call is allowed to execute.

```typescript
type PermissionRequestResult =
  | { kind: "approved" }
  | { kind: "denied-by-rules"; rules: unknown[] }
  | { kind: "denied-no-approval-rule-and-could-not-request-from-user" }
  | { kind: "denied-interactively-by-user"; feedback?: string }
  | { kind: "denied-by-content-exclusion-policy"; path: string; message: string };

interface PermissionRequest {
  kind: "shell" | "write" | "mcp" | "read" | "url" | "custom-tool";
  toolCallId?: string;
  [key: string]: unknown;  // Kind-specific fields (e.g. command, path)
}

type PermissionHandler = (
  request: PermissionRequest,
  invocation: { sessionId: string }
) => Promise<PermissionRequestResult> | PermissionRequestResult;
```
## `UserInputHandler`

Providing `onUserInputRequest` enables the built-in `ask_user` tool, letting the agent pause and ask the user a question.

```typescript
interface UserInputRequest {
  question: string;          // The question to ask
  choices?: string[];        // Optional list of choices
  allowFreeform?: boolean;   // Whether freeform text is allowed (default: true)
}

interface UserInputResponse {
  answer: string;            // The user's answer
  wasFreeform: boolean;      // Whether the answer was freeform (not from choices)
}

type UserInputHandler = (
  request: UserInputRequest,
  invocation: { sessionId: string }
) => Promise<UserInputResponse> | UserInputResponse;
```
## `defineTool()` Function

Factory that constructs a `Tool` with TypeScript type inference from a Zod schema.

```typescript
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

Without `defineTool`, you must manually annotate the `Tool` generic or cast `args`. It infers `T` from the Zod schema's output type.
## `approveAll` Constant

Convenience `PermissionHandler` that approves every request unconditionally.

```typescript
const approveAll: PermissionHandler = () => ({ kind: "approved" });
```

> **Warning:** Only use in trusted/development contexts. In production, implement a handler that validates each `PermissionRequest`.
## Usage Examples

### 1. `defineTool` with Zod Schema (Type-Safe)

```typescript
import { z } from "zod";
import { defineTool } from "@github/copilot-sdk";

const searchFiles = defineTool("search_files", {
  description: "Search for files matching a glob pattern",
  parameters: z.object({
    pattern: z.string().describe("Glob pattern to match"),
    directory: z.string().optional().describe("Base directory"),
  }),
  handler: async (args) => {
    // args is typed as { pattern: string; directory?: string }
    const results = await glob(args.pattern, { cwd: args.directory });
    return results.join("\n");
  },
});
```

### 2. `defineTool` with Raw JSON Schema

```typescript
const echoTool = defineTool("echo_message", {
  description: "Echoes back the provided message",
  parameters: {
    type: "object",
    properties: { message: { type: "string", description: "Message to echo" } },
    required: ["message"],
  },
  handler: (args) => {
    const { message } = args as { message: string }; // Must cast — no inference
    return message;
  },
});
```

### 3. Tool Returning `ToolResultObject` with Error Handling

```typescript
const readDatabase = defineTool("read_database", {
  description: "Query a database table by ID",
  parameters: z.object({ table: z.string(), id: z.string() }),
  handler: async (args): Promise<ToolResultObject> => {
    try {
      const row = await db.query(args.table, args.id);
      if (!row) {
        return {
          textResultForLlm: `No record found in ${args.table} with id ${args.id}`,
          resultType: "failure",
          error: "Record not found",
        };
      }
      return {
        textResultForLlm: JSON.stringify(row, null, 2),
        resultType: "success",
        sessionLog: `Queried ${args.table}:${args.id}`,
        toolTelemetry: { table: args.table, rowCount: 1 },
      };
    } catch (err) {
      return {
        textResultForLlm: "Database query failed",
        resultType: "failure",
        error: err instanceof Error ? err.message : String(err),
      };
    }
  },
});
```

### 4. Tool with Binary Result (Screenshot)

```typescript
const takeScreenshot = defineTool("take_screenshot", {
  description: "Capture a screenshot of a URL",
  parameters: z.object({ url: z.string().url().describe("URL to screenshot") }),
  handler: async (args): Promise<ToolResultObject> => {
    const buffer = await captureScreenshot(args.url);
    return {
      textResultForLlm: `Screenshot captured for ${args.url}`,
      resultType: "success",
      binaryResultsForLlm: [{
        data: buffer.toString("base64"),
        mimeType: "image/png",
        type: "screenshot",
        description: `Screenshot of ${args.url}`,
      }],
    };
  },
});
```

### 5. `overridesBuiltInTool` Pattern

```typescript
const sandboxedBash = defineTool("bash", {
  description: "Execute a shell command in a sandboxed environment",
  overridesBuiltInTool: true,
  parameters: z.object({ command: z.string().describe("Shell command") }),
  handler: async (args, invocation) => {
    const allowed = await validateCommand(args.command);
    if (!allowed) {
      return { textResultForLlm: "Command not allowed", resultType: "rejected" } satisfies ToolResultObject;
    }
    const output = await runInSandbox(args.command);
    return {
      textResultForLlm: output,
      resultType: "success",
      sessionLog: `[${invocation.sessionId}] bash: ${args.command}`,
    } satisfies ToolResultObject;
  },
});
```
## Passing Tools to a Session

```typescript
const session = await client.createSession({
  tools: [searchFiles, echoTool, readDatabase, takeScreenshot],
  onPermissionRequest: approveAll,
  onUserInputRequest: async (req) => {
    const answer = await promptUser(req.question, req.choices);
    return { answer, wasFreeform: !req.choices?.includes(answer) };
  },
});
```
## Important Caveats

1. **String vs. ToolResultObject** — Handlers can return a plain `string` (simple text) or a `ToolResultObject` (structured with status, errors, binary content, telemetry). Both are valid `ToolResult` values.

2. **Thrown errors are NOT exposed to the model** — If your handler throws, the SDK catches it internally but does **not** pass the error to the model. For expected failures, return a `ToolResultObject` with `resultType: "failure"` and an `error` string.

3. **`overridesBuiltInTool: true` is required** — When your tool's `name` matches a built-in (e.g. `bash`, `edit_file`), you must set this flag. Otherwise the SDK throws at registration.

4. **Zod enables type inference; raw JSON Schema does not** — With Zod, `defineTool` infers `args` type automatically. With JSON Schema, `args` is `unknown` and requires manual casting.

5. **`invocation.sessionId` for session-specific state** — Use the session ID to key per-session caches, rate limiters, or state stores inside handlers.

6. **Tool names: short, specific, snake_case** — The model sees tool names in context. Prefer `search_files` or `run_query` over generic names.

7. **`approveAll` is for development only** — In production, implement a `PermissionHandler` that inspects each request and applies proper security policies.
