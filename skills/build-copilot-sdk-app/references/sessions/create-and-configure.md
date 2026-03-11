# Session Creation and Configuration

## createSession() — Full API

Call `client.createSession(config: SessionConfig)` to open a new conversation session. The method returns a `CopilotSession` instance. Every field in `SessionConfig` is optional except `onPermissionRequest`, which is required.

```typescript
import { CopilotClient, approveAll } from "@github/copilot-sdk";

const client = new CopilotClient();
await client.start();

const session = await client.createSession({
  sessionId: "my-session-001",           // stable ID for resumption; omit for auto-generated
  model: "gpt-4.1",                      // model ID; see client.listModels()
  reasoningEffort: "high",               // "low" | "medium" | "high" | "xhigh"; model must support it
  streaming: true,                        // emit assistant.message_delta / reasoning_delta events
  workingDirectory: "/workspace/myapp",  // tool calls operate relative to this path
  configDir: "/custom/config/dir",       // override default ~/.copilot config location
  clientName: "my-agent-v1",            // included in User-Agent for API requests
  onPermissionRequest: approveAll,       // REQUIRED — see handler section below
});
```

## SessionConfig Field Reference

### Core Identity and Model

| Field | Type | Default | Purpose |
|---|---|---|---|
| `sessionId` | `string` | auto | Stable ID for later `resumeSession()` |
| `model` | `string` | server default | Model ID string, e.g. `"claude-sonnet-4.5"`, `"gpt-4.1"` |
| `reasoningEffort` | `"low" \| "medium" \| "high" \| "xhigh"` | model default | Only for models where `capabilities.supports.reasoningEffort === true` |
| `clientName` | `string` | — | User-Agent identifier for your app |
| `streaming` | `boolean` | `false` | Enable delta events during generation |

### Tools, Agents, MCP, Skills

```typescript
import { defineTool } from "@github/copilot-sdk";
import { z } from "zod";

const session = await client.createSession({
  onPermissionRequest: approveAll,

  // Custom tools the assistant can call
  tools: [
    defineTool("get_weather", {
      description: "Returns current weather for a city",
      parameters: z.object({ city: z.string() }),
      handler: async ({ city }) => `Sunny, 22°C in ${city}`,
    }),
  ],

  // Allowlist: only these built-in tools are available (takes precedence over excludedTools)
  availableTools: ["read_file", "list_directory"],

  // Denylist: disable specific tools while keeping the rest
  excludedTools: ["run_terminal_command"],

  // MCP server configuration
  mcpServers: {
    myServer: {
      type: "local",
      command: "node",
      args: ["./mcp-server.js"],
      tools: ["*"],        // "*" = all tools from this server
      timeout: 30000,
    },
    remoteServer: {
      type: "http",
      url: "https://my-mcp-api.example.com",
      headers: { Authorization: `Bearer ${process.env.MCP_TOKEN}` },
      tools: ["search", "fetch"],
    },
  },

  // Custom agent definitions
  customAgents: [
    {
      name: "code-reviewer",
      displayName: "Code Reviewer",
      description: "Reviews code for quality and security issues",
      prompt: "You are an expert code reviewer. Focus on security, correctness, and maintainability.",
      tools: ["read_file", "list_directory"],  // null/undefined = all tools
      infer: true,
    },
  ],

  // Pre-select an agent by name (must match a name in customAgents)
  agent: "code-reviewer",

  // Directories from which .copilot/skills/ are loaded
  skillDirectories: ["/workspace/.copilot/skills", "/shared/skills"],

  // Skill names to disable
  disabledSkills: ["deprecated-skill"],
});
```

### Hooks

Hooks intercept lifecycle events synchronously before the session processes them. Register all hooks as a single `SessionHooks` object:

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPreToolUse: async (input, { sessionId }) => {
      console.log(`[${sessionId}] About to call tool: ${input.toolName}`);
      // Return { permissionDecision: "deny" } to block the tool call
      // Return { modifiedArgs: newArgs } to rewrite arguments
      // Return { additionalContext: "..." } to inject context before the call
      return undefined; // proceed normally
    },
    onPostToolUse: async (input, { sessionId }) => {
      console.log(`[${sessionId}] Tool ${input.toolName} finished`);
      // Return { modifiedResult: ... } to override what the LLM sees
      return undefined;
    },
    onUserPromptSubmitted: async (input) => {
      // input.prompt is the raw user message
      // Return { modifiedPrompt: "..." } to rewrite before processing
      return undefined;
    },
    onSessionStart: async (input) => {
      // input.source: "startup" | "resume" | "new"
      return undefined;
    },
    onSessionEnd: async (input) => {
      // input.reason: "complete" | "error" | "abort" | "timeout" | "user_exit"
      return { sessionSummary: "Task completed successfully" };
    },
    onErrorOccurred: async (input) => {
      // input.errorContext: "model_call" | "tool_execution" | "system" | "user_input"
      if (input.recoverable) return { errorHandling: "retry", retryCount: 2 };
      return { errorHandling: "abort" };
    },
  },
});
```

### System Message

```typescript
// Append mode (default): your content is appended after the SDK's managed sections
const session = await client.createSession({
  onPermissionRequest: approveAll,
  systemMessage: {
    mode: "append",
    content: "Always respond in British English. Prefer concise answers.",
  },
});

// Replace mode: your content IS the entire system message — SDK guardrails removed
const session2 = await client.createSession({
  onPermissionRequest: approveAll,
  systemMessage: {
    mode: "replace",
    content: "You are a specialized SQL assistant. Only answer database questions.",
  },
});
```

### Early Event Handler

Use `onEvent` when you need to catch events fired during session initialization (e.g. `session.start`). It is registered before the `session.create` RPC is issued:

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  onEvent: (event) => {
    if (event.type === "session.start") {
      console.log("Session started:", event.data);
    }
  },
});
```

## onPermissionRequest — Required Handler

Every session must supply `onPermissionRequest`. When the assistant attempts a potentially dangerous operation (shell command, file write, MCP call, URL fetch, custom tool), this handler is invoked synchronously before execution.

```typescript
import type { PermissionHandler } from "@github/copilot-sdk";

const onPermissionRequest: PermissionHandler = async (request, { sessionId }) => {
  // request.kind: "shell" | "write" | "mcp" | "read" | "url" | "custom-tool"
  // Note: "memory" kind exists in the wire protocol but is not part of the TypeScript type.
  // Handle it in the default branch if encountered at runtime.
  switch (request.kind) {
    case "shell":
      // Auto-approve read-only shell commands; prompt user for destructive ones
      return { kind: "approved" };
    case "write":
      return { kind: "approved" };
    default:
      // Deny everything else without prompting
      return { kind: "denied-no-approval-rule-and-could-not-request-from-user" };
  }
};

// Convenience: approve everything (use in automated/trusted contexts only)
import { approveAll } from "@github/copilot-sdk";
```

## onUserInputRequest — Optional Handler

Register `onUserInputRequest` to enable the `ask_user` tool. Without it, the agent cannot ask clarifying questions.

```typescript
import type { UserInputHandler } from "@github/copilot-sdk";

const onUserInputRequest: UserInputHandler = async (request, { sessionId }) => {
  // request.question: string
  // request.choices?: string[]   — optional multiple-choice options
  // request.allowFreeform?: boolean — default true

  // In a CLI: prompt stdin
  const answer = await promptUser(request.question, request.choices);
  return { answer, wasFreeform: true };
};
```

## Model Selection

### At Creation Time

```typescript
const session = await client.createSession({
  model: "claude-sonnet-4.5",
  onPermissionRequest: approveAll,
});
```

### At Runtime with setModel()

`setModel()` switches models for the next message. Conversation history is preserved.

```typescript
// Start with a fast model for exploration
const session = await client.createSession({ model: "gpt-4.1-mini", onPermissionRequest: approveAll });
await session.sendAndWait({ prompt: "Outline a refactoring plan" });

// Switch to a more capable model for execution
await session.setModel("gpt-4.1");
await session.sendAndWait({ prompt: "Now implement the plan" });
```

List available models before selecting:

```typescript
const models = await client.listModels();
for (const m of models) {
  console.log(m.id, m.capabilities.limits.max_context_window_tokens);
  if (m.capabilities.supports.reasoningEffort) {
    console.log("  reasoning efforts:", m.supportedReasoningEfforts);
  }
}
```

## sendAndWait() vs send()

### sendAndWait() — Block Until Idle

Use `sendAndWait()` when you want to await the complete response before proceeding. Returns the final `AssistantMessageEvent` or `undefined` if no assistant message was produced.

```typescript
// Default timeout: 60,000 ms
const response = await session.sendAndWait({ prompt: "Summarize this file" });
console.log(response?.data.content);

// Custom timeout (ms) — throws if session.idle not received in time
// Note: timeout does NOT abort in-flight agent work; it only stops waiting
const response2 = await session.sendAndWait(
  { prompt: "Refactor the entire module" },
  300_000  // 5 minutes
);
```

### send() — Fire and Observe via Events

Use `send()` when you need non-blocking dispatch, want to send while the session is busy (steering/queueing), or manage your own idle detection.

```typescript
// Non-blocking: message dispatched, returns messageId
const messageId = await session.send({ prompt: "Start a long analysis" });

// Observe progress via event subscription
const unsubscribe = session.on((event) => {
  switch (event.type) {
    case "assistant.message_delta":
      process.stdout.write(event.data.deltaContent ?? "");
      break;
    case "assistant.message":
      console.log("\nFinal:", event.data.content);
      break;
    case "session.idle":
      unsubscribe();
      break;
  }
});
```

### Streaming Deltas

Enable `streaming: true` in `SessionConfig` to receive `assistant.message_delta` and `assistant.reasoning_delta` events. Accumulate `deltaContent` values to build the full response:

```typescript
const session = await client.createSession({
  streaming: true,
  onPermissionRequest: approveAll,
});

let accumulated = "";
session.on("assistant.message_delta", (event) => {
  accumulated += event.data.deltaContent ?? "";
  process.stdout.write(event.data.deltaContent ?? "");
});
```

## abort() — Cancel In-Flight Work

`abort()` signals the CLI to stop the currently processing turn. The session remains valid and can accept new messages immediately after.

```typescript
// Start a long task
await session.send({ prompt: "Analyze every file in /src recursively" });

// Cancel after 10 seconds
const cancelTimer = setTimeout(async () => {
  await session.abort();
  console.log("Aborted. Session still usable.");
}, 10_000);

// If it finishes early, clear the timer
session.on("session.idle", () => clearTimeout(cancelTimer));
```

## disconnect() — Release and Preserve

`disconnect()` releases all in-memory resources (event handlers, tool handlers, permission handlers) and sends `session.destroy` to the CLI. Session data on disk is preserved and can be resumed via `client.resumeSession(sessionId)`.

```typescript
// Using explicit disconnect
try {
  await session.sendAndWait({ prompt: "Complete the task" });
} finally {
  await session.disconnect();  // always clean up
}

// Using Symbol.asyncDispose (TypeScript 5.2+ with useResourceManagement)
await using session2 = await client.createSession({ onPermissionRequest: approveAll });
await session2.sendAndWait({ prompt: "Hello" });
// session2.disconnect() called automatically on scope exit
```

`destroy()` is deprecated — use `disconnect()`. `deleteSession(sessionId)` on the client permanently removes all disk state (irreversible).

## log() — Extension-Safe Logging

Write messages to the session timeline. Non-ephemeral messages are persisted to the session event log on disk.

```typescript
await session.log("Processing started");
await session.log("Disk usage high", { level: "warning" });
await session.log("Connection failed", { level: "error" });
await session.log("Verbose debug info", { ephemeral: true });  // not persisted
```

Level options: `"info"` (default) | `"warning"` | `"error"`. Ephemeral messages appear in the live event stream but are not written to disk.

## getMessages() — Conversation History

Retrieve the complete conversation history including user messages, assistant responses, tool calls, and other session events:

```typescript
const events = await session.getMessages();
for (const event of events) {
  if (event.type === "assistant.message") {
    console.log("Assistant:", event.data.content);
  }
  if (event.type === "external_tool.requested") {
    console.log("Tool called:", event.data.toolName);
  }
}
```

`getMessages()` makes a network request to the CLI each time it is called. Cache the result if you call it in a hot path.
