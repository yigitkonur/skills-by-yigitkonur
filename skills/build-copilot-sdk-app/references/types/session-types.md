# Session Types Reference

## Import Patterns

```typescript
import { CopilotSession } from "@github/copilot-sdk";
import type {
  SessionConfig,
  ResumeSessionConfig,
  MessageOptions,
  SessionEvent,
  SessionEventHandler,
  SessionEventType,
  SessionEventPayload,
  TypedSessionEventHandler,
  SystemMessageConfig,
  SystemMessageAppendConfig,
  SystemMessageReplaceConfig,
  ProviderConfig,
  InfiniteSessionConfig,
  CustomAgentConfig,
  MCPServerConfig,
  PermissionHandler,
  PermissionRequest,
  PermissionRequestResult,
  UserInputHandler,
  SessionHooks,
  ReasoningEffort,
} from "@github/copilot-sdk";
```

---

## `SessionConfig` Interface

```typescript
interface SessionConfig {
  // Custom session ID. If omitted, server generates one.
  sessionId?: string;

  // App name included in User-Agent header.
  clientName?: string;

  // Model identifier, e.g. "claude-sonnet-4.5". Use client.listModels() to enumerate.
  model?: string;

  // Reasoning effort. Only valid when model.capabilities.supports.reasoningEffort is true.
  reasoningEffort?: ReasoningEffort; // "low" | "medium" | "high" | "xhigh"

  // Override config directory for storing session state.
  configDir?: string;

  // Custom tools exposed to the CLI server.
  tools?: Tool<any>[];

  // System message configuration. Controls how system prompt is built.
  systemMessage?: SystemMessageConfig;

  // Allowlist: only these tools are available. Takes precedence over excludedTools.
  availableTools?: string[];

  // Denylist: these tools are disabled. Ignored if availableTools is set.
  excludedTools?: string[];

  // BYOK custom provider configuration.
  provider?: ProviderConfig;

  // REQUIRED: handles permission requests from the server.
  onPermissionRequest: PermissionHandler;

  // Enables ask_user tool; handler receives questions from the agent.
  onUserInputRequest?: UserInputHandler;

  // Lifecycle hook handlers.
  hooks?: SessionHooks;

  // Working directory for tool operations.
  workingDirectory?: string;

  // Enable streaming of assistant.message_delta and assistant.reasoning_delta events.
  // Default: false.
  streaming?: boolean;

  // MCP server configurations. Keys are server names.
  mcpServers?: Record<string, MCPServerConfig>;

  // Custom agent configurations.
  customAgents?: CustomAgentConfig[];

  // Name of the custom agent to activate at session start.
  // Must match one of the names in customAgents.
  agent?: string;

  // Directories to load skills from.
  skillDirectories?: string[];

  // Skill names to disable.
  disabledSkills?: string[];

  // Infinite session configuration. Default: enabled with standard thresholds.
  infiniteSessions?: InfiniteSessionConfig;

  // Event handler registered before session.create RPC is issued.
  // Guarantees early events (e.g. session.start) are not missed.
  onEvent?: SessionEventHandler;
}
```

---

## `ResumeSessionConfig` Type

`ResumeSessionConfig` is a `Pick` of `SessionConfig` fields (excluding `sessionId`), plus one extra field:

```typescript
type ResumeSessionConfig = Pick<SessionConfig,
  | "clientName" | "model" | "tools" | "systemMessage"
  | "availableTools" | "excludedTools" | "provider" | "streaming"
  | "reasoningEffort" | "onPermissionRequest" | "onUserInputRequest"
  | "hooks" | "workingDirectory" | "configDir" | "mcpServers"
  | "customAgents" | "agent" | "skillDirectories" | "disabledSkills"
  | "infiniteSessions" | "onEvent"
> & {
  // Skip emitting session.resume event on reconnect. Default: false.
  disableResume?: boolean;
};
```

---

## `SystemMessageConfig` Types

```typescript
// Append mode (default): SDK foundation + optional appended content.
interface SystemMessageAppendConfig {
  mode?: "append";
  content?: string;  // Appended after SDK-managed sections.
}

// Replace mode: caller provides the entire system message.
// WARNING: removes all SDK guardrails including security restrictions.
interface SystemMessageReplaceConfig {
  mode: "replace";
  content: string;  // Complete system message.
}

type SystemMessageConfig = SystemMessageAppendConfig | SystemMessageReplaceConfig;
```

---

## `ProviderConfig` Interface (BYOK)

```typescript
interface ProviderConfig {
  type?: "openai" | "azure" | "anthropic";  // Default: "openai"
  wireApi?: "completions" | "responses";     // openai/azure only. Default: "completions"
  baseUrl: string;
  apiKey?: string;
  // Bearer token auth. Takes precedence over apiKey when both set.
  bearerToken?: string;
  azure?: {
    apiVersion?: string;  // Default: "2024-10-21"
  };
}
```

---

## `InfiniteSessionConfig` Interface

```typescript
interface InfiniteSessionConfig {
  // Default: true
  enabled?: boolean;
  // 0.0-1.0 threshold to start background compaction. Default: 0.80
  backgroundCompactionThreshold?: number;
  // 0.0-1.0 threshold to block until compaction completes. Default: 0.95
  bufferExhaustionThreshold?: number;
}
```

---

## `MessageOptions` Interface

```typescript
interface MessageOptions {
  prompt: string;
  attachments?: Array<
    | { type: "file"; path: string; displayName?: string }
    | { type: "directory"; path: string; displayName?: string }
    | {
        type: "selection";
        filePath: string;
        displayName: string;
        selection?: {
          start: { line: number; character: number };
          end: { line: number; character: number };
        };
        text?: string;
      }
  >;
  // "enqueue" adds to queue (default). "immediate" sends immediately.
  mode?: "enqueue" | "immediate";
}
```

---

## `CopilotSession` Public API

`CopilotSession` is returned by `client.createSession()` and `client.resumeSession()`. Do not instantiate directly.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `sessionId` | `string` | The session identifier. |
| `rpc` | `ReturnType<createSessionRpc>` | Typed RPC proxy for session-scoped RPC calls. See rpc-methods.md. |

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `send` | `(options: MessageOptions): Promise<string>` | Sends a message to the session. Returns the message ID. |
| `sendAndWait` | `(options: MessageOptions, timeout?: number): Promise<AssistantMessageEvent \| undefined>` | Sends and waits for the assistant's complete response. Returns `undefined` if no assistant message was produced. |
| `abort` | `(): Promise<void>` | Aborts the current turn. |
| `on` | `(handler: SessionEventHandler): () => void` | Subscribes to all session events. Returns unsubscribe function. |
| `on<T>` | `(type: T, handler: TypedSessionEventHandler<T>): () => void` | Subscribes to a specific event type. |
| `disconnect` | `(): Promise<void>` | Releases in-memory resources and preserves session state on disk. |
| `setModel` | `(modelId: string): Promise<void>` | Switches the model for subsequent messages. |
| `log` | `(message: string, options?: { level?: string; ephemeral?: boolean }): Promise<void>` | Emits a log entry into the session event stream. |

---

## Event Handler Types

```typescript
// Handles all events
type SessionEventHandler = (event: SessionEvent) => void;

// Handles one specific event type; event is narrowed to that type's shape
type TypedSessionEventHandler<T extends SessionEventType> = (
  event: SessionEventPayload<T>
) => void;

// Extract the event type string union
type SessionEventType = SessionEvent["type"];

// Extract the full event shape for a given type string
type SessionEventPayload<T extends SessionEventType> = Extract<SessionEvent, { type: T }>;
```

---

## `AssistantMessageEvent` Type

`sendAndWait` returns the `assistant.message` event object:

```typescript
// Exported from "@github/copilot-sdk"
type AssistantMessageEvent = Extract<SessionEvent, { type: "assistant.message" }>;
// data.content holds the full text response
// data.toolRequests holds any tool call requests
// data.messageId is the unique message identifier
```

---

## Usage Patterns

```typescript
// Create session with required permission handler
const session = await client.createSession({
  onPermissionRequest: approveAll,  // or custom handler
  model: "claude-sonnet-4.5",
  workingDirectory: process.cwd(),
  streaming: true,
});

// Send and stream events
const unsub = session.on("assistant.message_delta", (e) => {
  process.stdout.write(e.data.deltaContent);
});
await session.send({ prompt: "Refactor this function" });
// Listen for idle to know when done
session.on("session.idle", () => {
  unsub();
});

// Send and wait for complete response
const reply = await session.sendAndWait({ prompt: "List the files in the repo" });
console.log(reply?.data.content);

// Typed event subscription
session.on("tool.execution_start", (e) => {
  console.log("Running tool:", e.data.toolName, e.data.arguments);
});

// Always disconnect when done
await session.disconnect();
```
