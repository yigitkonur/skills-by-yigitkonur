# Session Types Reference — `@github/copilot-sdk`

Complete type reference for session creation, configuration, and lifecycle management.
Used by AI agents building applications with the GitHub Copilot SDK.

---

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
  AssistantMessageEvent,
  SystemMessageConfig,
  SystemMessageAppendConfig,
  SystemMessageReplaceConfig,
  ProviderConfig,
  InfiniteSessionConfig,
  CustomAgentConfig,
  MCPServerConfig,
  MCPLocalServerConfig,
  MCPRemoteServerConfig,
  PermissionHandler,
  PermissionRequest,
  PermissionRequestResult,
  UserInputHandler,
  SessionHooks,
  ReasoningEffort,
} from "@github/copilot-sdk";
```

---

## `SessionConfig`

The primary configuration object passed to `client.createSession()`.
**`onPermissionRequest` is the ONLY required field.**

```typescript
interface SessionConfig {
  sessionId?: string;
  clientName?: string;
  model?: string;
  reasoningEffort?: ReasoningEffort;
  configDir?: string;
  tools?: Tool<any>[];
  systemMessage?: SystemMessageConfig;
  availableTools?: string[];
  excludedTools?: string[];
  provider?: ProviderConfig;
  onPermissionRequest: PermissionHandler;       // REQUIRED
  onUserInputRequest?: UserInputHandler;
  hooks?: SessionHooks;
  workingDirectory?: string;
  streaming?: boolean;
  mcpServers?: Record<string, MCPServerConfig>;
  customAgents?: CustomAgentConfig[];
  agent?: string;
  skillDirectories?: string[];
  disabledSkills?: string[];
  infiniteSessions?: InfiniteSessionConfig;
  onEvent?: SessionEventHandler;
}
```

### Property Details

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `sessionId` | `string` | Auto-generated | Custom session ID. Server generates a UUID if omitted. |
| `clientName` | `string` | — | Client identifier included in the User-Agent header. |
| `model` | `string` | Server default | Model identifier (e.g. `"claude-sonnet-4.5"`). Use `client.listModels()` to enumerate. |
| `reasoningEffort` | `ReasoningEffort` | — | `"low" \| "medium" \| "high" \| "xhigh"`. Only valid when model supports it. |
| `configDir` | `string` | Platform default | Override configuration directory for session state storage. |
| `tools` | `Tool<any>[]` | `[]` | Custom tools exposed to the agent. See tool-types.md. |
| `systemMessage` | `SystemMessageConfig` | Append mode | System prompt configuration. Controls how the system message is built. |
| `availableTools` | `string[]` | All tools | Allowlist of tool names. Takes precedence over `excludedTools`. |
| `excludedTools` | `string[]` | None | Denylist of tool names. Ignored if `availableTools` is set. |
| `provider` | `ProviderConfig` | GitHub AI | BYOK provider configuration. Overrides the default GitHub-hosted model endpoint. |
| `onPermissionRequest` | `PermissionHandler` | — | **REQUIRED.** Handler invoked when the agent requests permission to run a tool. |
| `onUserInputRequest` | `UserInputHandler` | — | Handler for `ask_user` tool invocations. If omitted, `ask_user` is unavailable. |
| `hooks` | `SessionHooks` | — | Lifecycle hook handlers (pre/post tool execution, etc.). See hooks-types.md. |
| `workingDirectory` | `string` | — | Working directory for file-system tool operations. |
| `streaming` | `boolean` | `false` | Enable `assistant.message_delta` and `assistant.reasoning_delta` events. |
| `mcpServers` | `Record<string, MCPServerConfig>` | — | MCP server configurations. Object keys are server names. |
| `customAgents` | `CustomAgentConfig[]` | `[]` | Custom agent definitions available for delegation. |
| `agent` | `string` | — | Pre-selected custom agent name. Must match a name in `customAgents`. |
| `skillDirectories` | `string[]` | `[]` | Directories to search for skill definitions. |
| `disabledSkills` | `string[]` | `[]` | Skill names to disable. |
| `infiniteSessions` | `InfiniteSessionConfig` | Enabled | Infinite session configuration for automatic context compaction. |
| `onEvent` | `SessionEventHandler` | — | Event handler registered before `session.create` RPC. Guarantees early events like `session.start` are captured. |

---

## `ResumeSessionConfig`

Configuration for `client.resumeSession(sessionId, config)`. Identical to `SessionConfig` minus `sessionId`, plus `disableResume`.

```typescript
type ResumeSessionConfig = Pick<SessionConfig,
  | "clientName" | "model" | "reasoningEffort" | "configDir"
  | "tools" | "systemMessage" | "availableTools" | "excludedTools"
  | "provider" | "onPermissionRequest" | "onUserInputRequest"
  | "hooks" | "workingDirectory" | "streaming"
  | "mcpServers" | "customAgents" | "agent"
  | "skillDirectories" | "disabledSkills"
  | "infiniteSessions" | "onEvent"
> & {
  /**
   * When true, skips emitting the session.resume event on reconnect.
   * @default false
   */
  disableResume?: boolean;
};
```

---

## `MessageOptions`

Passed to `session.send()` and `session.sendAndWait()`.

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
  mode?: "enqueue" | "immediate";
}
```

### `mode` Behavior

| Value | Default | Description |
|-------|---------|-------------|
| `"enqueue"` | ✅ | Queues the message. Waits for current turn to finish before processing. |
| `"immediate"` | — | Interrupts current processing for mid-turn correction. Use sparingly. |

---

## `SystemMessageConfig`

Discriminated union controlling how the system prompt is constructed.

```typescript
type SystemMessageConfig = SystemMessageAppendConfig | SystemMessageReplaceConfig;

// Append mode (default): SDK foundation prompt + your content appended after
interface SystemMessageAppendConfig {
  mode?: "append";
  content?: string;
}

// Replace mode: your content completely replaces the SDK system message
// ⚠️  Removes ALL SDK guardrails including security restrictions
interface SystemMessageReplaceConfig {
  mode: "replace";
  content: string;   // Required when mode is "replace"
}
```

---

## `ProviderConfig` (BYOK)

Bring-your-own-key provider configuration. Credentials are **NOT persisted** — must be re-provided on resume.

```typescript
interface ProviderConfig {
  type?: "openai" | "azure" | "anthropic";   // Default: "openai"
  wireApi?: "completions" | "responses";     // OpenAI/Azure only. Default: "completions"
  baseUrl: string;                            // Required — provider endpoint URL
  apiKey?: string;                            // API key authentication
  bearerToken?: string;                       // Bearer token auth (takes precedence over apiKey)
  azure?: {
    apiVersion?: string;                      // Default: "2024-10-21"
  };
}
```

---

## `InfiniteSessionConfig`

Controls automatic context window compaction for long-running sessions.

```typescript
interface InfiniteSessionConfig {
  enabled?: boolean;                           // Default: true
  backgroundCompactionThreshold?: number;      // 0.0–1.0. Default: 0.80
  bufferExhaustionThreshold?: number;          // 0.0–1.0. Default: 0.95
}
```

- `backgroundCompactionThreshold`: token usage ratio that triggers background compaction.
- `bufferExhaustionThreshold`: token usage ratio that blocks until compaction completes.

---

## `MCPServerConfig` (Union)

```typescript
type MCPServerConfig = MCPLocalServerConfig | MCPRemoteServerConfig;
```

### Base Interface

```typescript
interface MCPServerConfigBase {
  tools: string[];           // Tool names to expose ([] = none)
  type?: string;
  timeout?: number;          // Connection/call timeout in milliseconds
}
```

### Local (stdio) Server

```typescript
interface MCPLocalServerConfig extends MCPServerConfigBase {
  type?: "local" | "stdio";
  command: string;            // Command to execute
  args: string[];             // Command arguments
  env?: Record<string, string>;
  cwd?: string;               // Working directory for the process
}
```

### Remote (HTTP/SSE) Server

```typescript
interface MCPRemoteServerConfig extends MCPServerConfigBase {
  type: "http" | "sse";
  url: string;                // Remote server URL
  headers?: Record<string, string>;
}
```

---

## `CustomAgentConfig`

Defines a custom agent for task delegation.

```typescript
interface CustomAgentConfig {
  name: string;                                  // Unique agent identifier (required)
  displayName?: string;                          // Human-readable name for UI
  description?: string;                          // CRITICAL for delegation quality
  tools?: string[] | null;                       // Tool whitelist. null/undefined = all tools
  prompt: string;                                // Agent system prompt (required)
  mcpServers?: Record<string, MCPServerConfig>;  // Agent-private MCP servers
  infer?: boolean;                               // Allow automatic selection. Default: true
}
```

> **Tip:** A clear `description` is critical — the model uses it to decide when to delegate to this agent.

---

## `AssistantMessageEvent`

The return type of `sendAndWait()`.

```typescript
type AssistantMessageEvent = Extract<SessionEvent, { type: "assistant.message" }>;

// Key data fields:
// event.data.content      — full text response
// event.data.toolRequests — any tool call requests
// event.data.messageId    — unique message identifier
```

---

## Event Handler Types

```typescript
// Subscribe to all events
type SessionEventHandler = (event: SessionEvent) => void;

// Subscribe to a specific event type (event is narrowed automatically)
type TypedSessionEventHandler<T extends SessionEventType> = (
  event: SessionEventPayload<T>
) => void;

// Utility types
type SessionEventType = SessionEvent["type"];
type SessionEventPayload<T extends SessionEventType> = Extract<SessionEvent, { type: T }>;
```

---

## `CopilotSession` Class

Returned by `client.createSession()` and `client.resumeSession()`. **Do not instantiate directly.**

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `sessionId` | `string` (readonly) | Unique session identifier. |
| `workspacePath` | `string \| undefined` (getter) | Workspace path for infinite sessions. |
| `rpc` | See RPC section below | Typed RPC proxy for session-scoped calls. |

### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `send` | `(options: MessageOptions)` | `Promise<string>` | Sends a message. Returns message ID. |
| `sendAndWait` | `(options: MessageOptions, timeout?: number)` | `Promise<AssistantMessageEvent \| undefined>` | Sends and waits for `session.idle`. Default timeout: 60000ms. Returns `undefined` if no assistant message produced. |
| `on` (typed) | `<K extends SessionEventType>(type: K, handler: TypedSessionEventHandler<K>)` | `() => void` | Subscribe to a specific event type. Returns unsubscribe function. |
| `on` (wildcard) | `(handler: SessionEventHandler)` | `() => void` | Subscribe to all events. Returns unsubscribe function. |
| `getMessages` | `()` | `Promise<SessionEvent[]>` | Retrieves full conversation history as events. |
| `disconnect` | `()` | `Promise<void>` | Releases in-memory resources. Preserves session data on disk. |
| `destroy` | `()` | `Promise<void>` | **DEPRECATED** — use `disconnect()`. |
| `[Symbol.asyncDispose]` | `()` | `Promise<void>` | Enables `await using session = ...` pattern for automatic cleanup. |
| `abort` | `()` | `Promise<void>` | Aborts current processing. Session remains valid for further messages. |
| `setModel` | `(model: string)` | `Promise<void>` | Switches the model for subsequent messages. |
| `log` | `(message: string, options?: { level?: "info" \| "warning" \| "error"; ephemeral?: boolean })` | `Promise<void>` | Emits a log entry into the session event stream. |

---

## `session.rpc` — Session RPC Methods

The `rpc` getter exposes typed RPC methods organized by namespace. All methods return Promises.

```typescript
get rpc: {
  model: {
    getCurrent(): Promise<{ modelId?: string }>;
    switchTo(params: {
      modelId: string;
      reasoningEffort?: ReasoningEffort;
    }): Promise<{ modelId?: string }>;
  };

  mode: {
    get(): Promise<{ mode: "interactive" | "plan" | "autopilot" }>;
    set(params: {
      mode: "interactive" | "plan" | "autopilot";
    }): Promise<{ mode: string }>;
  };

  plan: {
    read(): Promise<{
      exists: boolean;
      content: string | null;
      path: string | null;
    }>;
    update(params: { content: string }): Promise<void>;
    delete(): Promise<void>;
  };

  workspace: {
    listFiles(): Promise<{ files: string[] }>;
    readFile(params: { path: string }): Promise<{ content: string }>;
    createFile(params: {
      path: string;
      content: string;
    }): Promise<void>;
  };

  fleet: {
    start(params?: { prompt?: string }): Promise<{ started: boolean }>;
  };

  agent: {
    list(): Promise<{ agents: AgentInfo[] }>;
    getCurrent(): Promise<{ agent: AgentInfo | null }>;
    select(params: { name: string }): Promise<{ agent: AgentInfo }>;
    deselect(): Promise<void>;
  };

  compaction: {
    compact(): Promise<{
      success: boolean;
      tokensRemoved: number;
      messagesRemoved: number;
    }>;
  };

  tools: {
    handlePendingToolCall(params: {
      requestId: string;
      result?: string;
      error?: string;
    }): Promise<{ success: boolean }>;
  };

  permissions: {
    handlePendingPermissionRequest(params: {
      requestId: string;
      result: PermissionRequestResult;
    }): Promise<{ success: boolean }>;
  };

  log(params: {
    message: string;
    level?: "info" | "warning" | "error";
    ephemeral?: boolean;
  }): Promise<{ eventId: string }>;
}
```

### RPC Namespace Summary

| Namespace | Methods | Purpose |
|-----------|---------|---------|
| `model` | `getCurrent`, `switchTo` | Query and change the active model. |
| `mode` | `get`, `set` | Read/set the agent mode (interactive, plan, autopilot). |
| `plan` | `read`, `update`, `delete` | Manage the session plan document. |
| `workspace` | `listFiles`, `readFile`, `createFile` | File operations in the session workspace. |
| `fleet` | `start` | Start fleet (multi-agent) execution. |
| `agent` | `list`, `getCurrent`, `select`, `deselect` | Manage custom agent selection. |
| `compaction` | `compact` | Manually trigger context compaction. |
| `tools` | `handlePendingToolCall` | Resolve a pending tool call with result or error. |
| `permissions` | `handlePendingPermissionRequest` | Resolve a pending permission request. |
| *(root)* | `log` | Emit a log entry to the session timeline. |

---

## Usage Examples

### 1. Basic Session with `sendAndWait`

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient();
const session = await client.createSession({
  onPermissionRequest: async (req) => ({ allowed: true }),
  model: "claude-sonnet-4.5",
  workingDirectory: process.cwd(),
});

const reply = await session.sendAndWait({
  prompt: "List the TypeScript files in this project",
});
console.log(reply?.data.content);

await session.disconnect();
```

### 2. Streaming with Event Handlers

> **Register event handlers BEFORE calling `send()`** to avoid missing early events.

```typescript
const session = await client.createSession({
  onPermissionRequest: async (req) => ({ allowed: true }),
  streaming: true,
});

// Register BEFORE send — prevents race conditions
session.on("assistant.message_delta", (event) => {
  process.stdout.write(event.data.deltaContent);
});

session.on("tool.execution_start", (event) => {
  console.log(`\n[Tool] ${event.data.toolName}`);
});

session.on("session.idle", () => {
  console.log("\n--- Turn complete ---");
});

await session.send({ prompt: "Refactor the auth module" });
```

### 3. Session Resume with Custom Tools

```typescript
import { Tool } from "@github/copilot-sdk";

const fetchTool = new Tool({
  name: "fetch_url",
  description: "Fetches a URL and returns its content",
  parameters: { url: { type: "string", description: "URL to fetch" } },
  handler: async ({ url }) => {
    const res = await fetch(url);
    return await res.text();
  },
});

// Resume an existing session with tools
const session = await client.resumeSession("session-abc-123", {
  onPermissionRequest: async (req) => ({ allowed: true }),
  tools: [fetchTool],
  disableResume: false,
});

await session.sendAndWait({ prompt: "Fetch the README from GitHub" });
await session.disconnect();
```

### 4. Infinite Session with Workspace Access

```typescript
const session = await client.createSession({
  onPermissionRequest: async (req) => ({ allowed: true }),
  infiniteSessions: {
    enabled: true,
    backgroundCompactionThreshold: 0.80,
    bufferExhaustionThreshold: 0.95,
  },
});

// Access workspace files via RPC
const { files } = await session.rpc.workspace.listFiles();
console.log("Workspace files:", files);

// Manually trigger compaction
const result = await session.rpc.compaction.compact();
console.log(`Removed ${result.tokensRemoved} tokens`);

await session.disconnect();
```

### 5. Automatic Cleanup with `await using`

```typescript
async function runTask(prompt: string) {
  await using session = await client.createSession({
    onPermissionRequest: async (req) => ({ allowed: true }),
    model: "claude-sonnet-4.5",
  });
  // session.disconnect() is called automatically when scope exits

  const reply = await session.sendAndWait({ prompt });
  return reply?.data.content;
}
```

---

## Extension Function: `joinSession`

```typescript
import { joinSession } from "@github/copilot-sdk/extension";

async function joinSession(config: ResumeSessionConfig): Promise<CopilotSession>
```

Joins the current foreground session from a CLI extension running as a child process. Reads `SESSION_ID` from the environment automatically.

- **Throws** if `SESSION_ID` environment variable is not set (i.e., process is not a CLI child)
- Sets `disableResume: true` by default
- `onPermissionRequest` is required in `config`

```typescript
import { approveAll, joinSession } from "@github/copilot-sdk/extension";

const session = await joinSession({
  onPermissionRequest: approveAll,
  tools: [myExtensionTool],
});
await session.send({ prompt: "Extension reporting in" });
```

---

## Important Caveats

1. **`onPermissionRequest` is required.** It is the only mandatory field in `SessionConfig`. Omitting it causes a runtime error.

2. **Register event handlers BEFORE `send()`.** Events fire asynchronously — registering after `send()` creates a race condition where early events (like `session.start`) are lost.

3. **`sendAndWait` timeout does NOT abort work.** When the timeout expires, `sendAndWait` resolves with `undefined` but the agent continues processing. Call `session.abort()` to actually stop it.

4. **`disconnect()` vs `deleteSession()`.** `disconnect()` releases in-memory resources but preserves session data on disk for later resume. `client.deleteSession(id)` permanently destroys all session data.

5. **BYOK credentials are NOT persisted.** When resuming a session that used a custom `provider`, you must re-provide the `ProviderConfig` with credentials in `ResumeSessionConfig`.

6. **`mode: "immediate"` interrupts processing.** Use it only for mid-turn corrections. Default `"enqueue"` waits for the current turn to finish.

7. **`systemMessage.mode: "replace"` removes SDK guardrails.** This disables built-in security restrictions and safety prompts. Use `"append"` (default) unless you have a specific reason to replace the entire system message.

8. **`availableTools` takes precedence over `excludedTools`.** When both are set, only `availableTools` is used and `excludedTools` is ignored.
