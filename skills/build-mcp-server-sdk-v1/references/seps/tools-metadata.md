# SEPs — Tools, Metadata, and Advanced Features

## SEP-986: Tool Name Format

**Status:** Final

Standardizes tool naming:
- Length: SHOULD be 1-64 characters
- Allowed characters: `A-Z`, `a-z`, `0-9`, `_`, `-`, `.`, `/`
- Case-sensitive
- SHOULD be unique within namespace
- Forward slash `/` and dot `.` support hierarchical/namespaced patterns

**Valid examples:** `getUser`, `user-profile/update`, `DATA_EXPORT_v2`, `admin.tools.list`

**Migration:** Non-conforming names SHOULD be supported as aliases for at least one major version with deprecation warnings.

**SDK impact:** Tool registration should validate names against these rules. The TypeScript SDK's Zod-based validation should enforce the character set.

## SEP-973: Icons for Tools, Resources, Prompts, Implementations

**Status:** Final

Adds optional `icons` array and `websiteUrl` to `Implementation`, `Tool`, `Resource`, `ResourceTemplate`, and `Prompt`.

**Icon interface:**
```typescript
interface Icon {
  src: string;          // URI (HTTPS or data:)
  mimeType?: string;    // image/png, image/svg+xml, etc.
  sizes?: string[];     // ["48x48"] or ["any"] for SVG
  theme?: "light" | "dark";
}
```

**Required client support:** `image/png`, `image/jpeg`
**Recommended:** `image/svg+xml`, `image/webp`

**Security:**
- MUST use HTTPS or `data:` URIs only
- MUST reject `javascript:`, `file:`, `ftp:`, `ws:` schemes
- Fetch without credentials
- Exercise caution with SVGs (may contain JavaScript)

**SDK usage:**
```typescript
server.registerTool("deploy", {
  description: "Deploy to production",
  icons: [{ src: "https://example.com/deploy.png", mimeType: "image/png", sizes: ["48x48"] }],
  inputSchema: { env: z.string() },
}, handler);
```

## SEP-1303: Input Validation Errors as Tool Execution Errors

**Status:** Final

Reclassifies tool input validation errors from Protocol Errors (`-32602`) to Tool Execution Errors (`isError: true`). The LLM can see tool execution errors and self-correct; protocol errors are invisible to the model.

**Before (bad — model can't see the error):**
```typescript
throw new McpError(ErrorCode.InvalidParams, "Date must be in the future");
```

**After (good — model reads the error and corrects itself):**
```typescript
return {
  content: [{ type: "text", text: "Date must be in the future. Current date is 2025-08-05." }],
  isError: true,
};
```

**Rule:** Reserve `McpError` for protocol-level failures (unknown tool, server crash). Use `isError: true` for anything the LLM could fix by adjusting its input.

## SEP-1577: Sampling with Tools (Agentic Tool-Use Loops)

**Status:** Final

Adds `tools` and `toolChoice` parameters to `sampling/createMessage`, enabling servers to run agentic multi-turn tool-use loops via the client's LLM.

**Capability:** Client must declare `sampling.tools`:
```json
{ "capabilities": { "sampling": { "tools": {} } } }
```

**Flow:**
1. Server sends `sampling/createMessage` with `tools` array
2. Client's LLM responds with `ToolUseContent` (`stopReason: "toolUse"`)
3. Server executes the tool
4. Server sends another `sampling/createMessage` with `ToolResultContent` appended
5. Loop continues until `stopReason: "endTurn"` or similar

**Tool choice modes:**
- `{ "mode": "auto" }` — model decides (default)
- `{ "mode": "required" }` — must use at least one tool
- `{ "mode": "none" }` — must not use tools (force text response)

**Message constraints:**
- User messages with `tool_result` content MUST contain ONLY tool results
- Every `ToolUseContent` MUST be matched by a `ToolResultContent` with matching `toolUseId`

**Also soft-deprecates:** `includeContext` values `"thisServer"` and `"allServers"` (fenced behind `sampling.context` capability).

## SEP-1686: Tasks (Durable Long-Running Operations)

**Status:** Final (experimental in SDK)

Wraps any supported request in a durable state machine for long-running operations. The requestor adds `task: { ttl: 60000 }` to params; the receiver returns a `CreateTaskResult` immediately and the actual result is retrieved later via `tasks/result`.

**Task states:** `working` → `input_required` | `completed` | `failed` | `cancelled`

**Methods:**
| Method | Purpose |
|---|---|
| `tasks/get` | Poll current status |
| `tasks/result` | Retrieve final result (blocks if non-terminal) |
| `tasks/cancel` | Cancel a task |
| `tasks/list` | List all tasks (paginated) |
| `notifications/tasks/status` | Optional push on status change |

**Tool-level opt-in** via `execution.taskSupport`:
- `"forbidden"` (default) — MUST NOT invoke as task
- `"optional"` — MAY invoke as task or normal
- `"required"` — MUST invoke as task

**Server capability:**
```json
{ "capabilities": { "tasks": { "list": {}, "cancel": {}, "requests": { "tools": { "call": {} } } } } }
```

**SDK impact:** Use `server.experimental.tasks` — API may change. Task IDs must be cryptographically secure. Tasks should be bound to auth context.

## SEP-414: OpenTelemetry Trace Context Propagation

**Status:** Final

Documents the convention for propagating W3C Trace Context via `_meta` in MCP messages. Keys `traceparent`, `tracestate`, and `baggage` are used WITHOUT DNS prefixing (exception to general `_meta` key rules).

```json
{
  "params": {
    "name": "get_weather",
    "arguments": { "location": "NYC" },
    "_meta": {
      "traceparent": "00-0af7651916cd43dd8448eb211c80319c-00f067aa0ba902b7-01"
    }
  }
}
```

**SDK impact:** Low — for observability. If implementing distributed tracing, propagate `traceparent` in `_meta` exactly as shown. Already used in C# SDK, Python SDK, and OpenInference MCP TypeScript instrumentation.
