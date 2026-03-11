# Tool Types Reference

## Import Patterns

```typescript
import { defineTool, approveAll } from "@github/copilot-sdk";
import type {
  Tool,
  ToolHandler,
  ToolInvocation,
  ToolResult,
  ToolResultObject,
  ToolResultType,
  ToolBinaryResult,
  ZodSchema,
  PermissionHandler,
  PermissionRequest,
  PermissionRequestResult,
  UserInputHandler,
  UserInputRequest,
  UserInputResponse,
} from "@github/copilot-sdk";
```

---

## `Tool<TArgs>` Interface

```typescript
interface Tool<TArgs = unknown> {
  name: string;
  description?: string;
  // Parameters can be a Zod schema (enables type inference) or raw JSON Schema.
  parameters?: ZodSchema<TArgs> | Record<string, unknown>;
  handler: ToolHandler<TArgs>;
  // Set true to explicitly override a built-in tool of the same name.
  // Without this, a name clash with a built-in tool returns an error.
  overridesBuiltInTool?: boolean;
}
```

---

## `ToolHandler<TArgs>` Type

```typescript
type ToolHandler<TArgs = unknown> = (
  args: TArgs,
  invocation: ToolInvocation
) => Promise<unknown> | unknown;
```

The return value becomes the tool result sent to the LLM. Return a `string` for simple text results, or a `ToolResultObject` for structured results with metadata.

---

## `ToolInvocation` Interface

```typescript
interface ToolInvocation {
  sessionId: string;
  toolCallId: string;   // Unique ID for this specific tool call
  toolName: string;
  arguments: unknown;   // Raw arguments object from the LLM
}
```

Use `invocation.toolCallId` to correlate with `tool.execution_start` and `tool.execution_complete` events.

---

## `ToolResult` Type

```typescript
type ToolResult = string | ToolResultObject;
```

Return a plain `string` for simple text results. Return a `ToolResultObject` to include result type, error info, binary content, telemetry, or session logs.

---

## `ToolResultObject` Interface

```typescript
type ToolResultType = "success" | "failure" | "rejected" | "denied";

interface ToolResultObject {
  // Text result sent to the LLM for chat completion.
  textResultForLlm: string;
  // Optional binary content (images, audio, etc.) for the LLM.
  binaryResultsForLlm?: ToolBinaryResult[];
  // Indicates whether the tool succeeded, failed, or was blocked.
  resultType: ToolResultType;
  // Human-readable error message (used when resultType is "failure").
  error?: string;
  // Content appended to the session log for audit/debugging.
  sessionLog?: string;
  // Tool-specific telemetry data (e.g., grep match counts, CodeQL results).
  toolTelemetry?: Record<string, unknown>;
}

interface ToolBinaryResult {
  data: string;       // Base64-encoded binary content
  mimeType: string;   // e.g. "image/png", "audio/wav"
  type: string;       // Content category
  description?: string;
}
```

---

## `ZodSchema<T>` Interface

```typescript
// Any object implementing this interface is treated as a Zod schema.
// Zod v4 schemas satisfy this interface automatically.
interface ZodSchema<T = unknown> {
  _output: T;  // Used by TypeScript for type inference only
  toJSONSchema(): Record<string, unknown>;
}
```

---

## `defineTool` Function

`defineTool` is a helper that enables TypeScript to infer the handler's argument types from a Zod schema. Without it, you must cast `args` manually.

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

### Usage with Zod

```typescript
import { z } from "zod";
import { defineTool } from "@github/copilot-sdk";

const searchTool = defineTool("search_files", {
  description: "Search for files matching a pattern",
  parameters: z.object({
    pattern: z.string().describe("Glob pattern to match"),
    directory: z.string().optional().describe("Directory to search in"),
  }),
  handler: async (args, invocation) => {
    // args is typed as { pattern: string; directory?: string }
    const results = await glob(args.pattern, { cwd: args.directory });
    return { textResultForLlm: results.join("\n"), resultType: "success" };
  },
});
```

### Usage with Raw JSON Schema

```typescript
const echoTool = defineTool("echo", {
  description: "Echoes a message",
  parameters: {
    type: "object",
    properties: { message: { type: "string" } },
    required: ["message"],
  },
  handler: (args) => (args as { message: string }).message,
});
```

### Overriding a Built-in Tool

```typescript
const customBash = defineTool("bash", {
  description: "Sandboxed bash execution",
  overridesBuiltInTool: true,
  parameters: z.object({ command: z.string() }),
  handler: async (args) => {
    // Custom implementation
    return { textResultForLlm: "done", resultType: "success" };
  },
});
```

---

## Tool Event Correlation

When the session emits `tool.execution_start`, the `toolCallId` matches the one passed to your handler via `ToolInvocation`. Use this to track execution in event listeners.

```typescript
session.on("tool.execution_start", (e) => {
  // e.data.toolCallId matches invocation.toolCallId in your handler
  // e.data.toolName, e.data.arguments, e.data.mcpServerName (for MCP tools)
});

session.on("tool.execution_complete", (e) => {
  // e.data.toolCallId, e.data.success, e.data.result, e.data.error
});
```

---

## `PermissionHandler` Type

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
  [key: string]: unknown;  // Kind-specific fields
}

type PermissionHandler = (
  request: PermissionRequest,
  invocation: { sessionId: string }
) => Promise<PermissionRequestResult> | PermissionRequestResult;

// Convenience: approve every permission request
const approveAll: PermissionHandler = () => ({ kind: "approved" });
```

---

## `UserInputHandler` Type

Providing `onUserInputRequest` enables the `ask_user` built-in tool, allowing the agent to pause and ask the user a question.

```typescript
interface UserInputRequest {
  question: string;
  choices?: string[];
  allowFreeform?: boolean;  // Default: true
}

interface UserInputResponse {
  answer: string;
  wasFreeform: boolean;
}

type UserInputHandler = (
  request: UserInputRequest,
  invocation: { sessionId: string }
) => Promise<UserInputResponse> | UserInputResponse;
```

---

## Passing Tools to a Session

```typescript
const session = await client.createSession({
  tools: [searchTool, echoTool, customBash],
  onPermissionRequest: approveAll,
  onUserInputRequest: async (req) => {
    const answer = await promptUser(req.question, req.choices);
    return { answer, wasFreeform: !req.choices?.includes(answer) };
  },
});
```
