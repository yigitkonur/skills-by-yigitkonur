# Complete Type Reference

## Package exports

```typescript
// Runtime values
import {
  CopilotClient,
  CopilotSession,
  defineTool,
  approveAll,
} from "@github/copilot-sdk";

// Extension entry point
import { joinSession } from "@github/copilot-sdk/extension";
```

## Client types

### CopilotClientOptions

```typescript
interface CopilotClientOptions {
  cliPath?: string;
  cliArgs?: string[];
  cwd?: string;
  port?: number;
  useStdio?: boolean;
  isChildProcess?: boolean;
  cliUrl?: string;
  logLevel?: "none" | "error" | "warning" | "info" | "debug" | "all";
  autoStart?: boolean;
  autoRestart?: boolean;
  env?: Record<string, string | undefined>;
  githubToken?: string;
  useLoggedInUser?: boolean;
  onListModels?: () => Promise<ModelInfo[]> | ModelInfo[];
}
```

### ConnectionState

```typescript
type ConnectionState = "disconnected" | "connecting" | "connected" | "error";
```

## Session types

### SessionConfig

```typescript
interface SessionConfig {
  onPermissionRequest: PermissionHandler;
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

### ResumeSessionConfig

Same as SessionConfig minus `sessionId`, plus:

```typescript
interface ResumeSessionConfig {
  disableResume?: boolean; // skip session.resume event (default false)
  // ... all other SessionConfig fields
}
```

### InfiniteSessionConfig

```typescript
interface InfiniteSessionConfig {
  enabled?: boolean;                        // default true
  backgroundCompactionThreshold?: number;   // default 0.80
  bufferExhaustionThreshold?: number;       // default 0.95
}
```

### SystemMessageConfig

```typescript
type SystemMessageConfig =
  | SystemMessageAppendConfig
  | SystemMessageReplaceConfig;

interface SystemMessageAppendConfig {
  mode?: "append";
  content?: string;
}

interface SystemMessageReplaceConfig {
  mode: "replace";
  content: string;
}
```

### MessageOptions

```typescript
interface MessageOptions {
  prompt: string;
  attachments?: Array<
    | { type: "file"; path: string; displayName?: string }
    | { type: "directory"; path: string; displayName?: string }
    | { type: "selection"; filePath: string; displayName: string;
        selection?: { start: { line: number; character: number };
                      end: { line: number; character: number } };
        text?: string }
  >;
  mode?: "enqueue" | "immediate";
}
```

## Tool types

### Tool

```typescript
interface Tool<TArgs = unknown> {
  name: string;
  description?: string;
  parameters?: ZodSchema<TArgs> | Record<string, unknown>;
  handler: ToolHandler<TArgs>;
  overridesBuiltInTool?: boolean;
}
```

### ToolHandler

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
  data: string;        // base64
  mimeType: string;
  type: string;
  description?: string;
};

type ToolResult = string | ToolResultObject;
```

### ZodSchema

```typescript
interface ZodSchema<T = unknown> {
  _output: T;
  toJSONSchema(): Record<string, unknown>;
}
```

## Permission types

### PermissionHandler

```typescript
type PermissionHandler = (
  request: PermissionRequest,
  invocation: { sessionId: string },
) => Promise<PermissionRequestResult> | PermissionRequestResult;
```

### PermissionRequest

```typescript
interface PermissionRequest {
  kind: "shell" | "write" | "read" | "mcp" | "url" | "memory" | "custom-tool";
  toolCallId?: string;
  [key: string]: unknown;
}
```

### PermissionRequestResult

```typescript
type PermissionRequestResult =
  | { kind: "approved" }
  | { kind: "denied-by-rules"; rules: unknown[] }
  | { kind: "denied-no-approval-rule-and-could-not-request-from-user" }
  | { kind: "denied-interactively-by-user"; feedback?: string }
  | { kind: "denied-by-content-exclusion-policy"; path: string; message: string };
```

## User input types

### UserInputHandler

```typescript
type UserInputHandler = (
  request: UserInputRequest,
  invocation: { sessionId: string },
) => Promise<UserInputResponse> | UserInputResponse;
```

### UserInputRequest / Response

```typescript
interface UserInputRequest {
  question: string;
  choices?: string[];
  allowFreeform?: boolean;
}

interface UserInputResponse {
  answer: string;
  wasFreeform: boolean;
}
```

## Hook types

### SessionHooks

```typescript
interface SessionHooks {
  onPreToolUse?: (input: PreToolUseHookInput, inv: { sessionId: string }) => Promise<PreToolUseHookOutput | void> | PreToolUseHookOutput | void;
  onPostToolUse?: (input: PostToolUseHookInput, inv: { sessionId: string }) => Promise<PostToolUseHookOutput | void> | PostToolUseHookOutput | void;
  onUserPromptSubmitted?: (input: UserPromptSubmittedHookInput, inv: { sessionId: string }) => Promise<UserPromptSubmittedHookOutput | void> | UserPromptSubmittedHookOutput | void;
  onSessionStart?: (input: SessionStartHookInput, inv: { sessionId: string }) => Promise<SessionStartHookOutput | void> | SessionStartHookOutput | void;
  onSessionEnd?: (input: SessionEndHookInput, inv: { sessionId: string }) => Promise<SessionEndHookOutput | void> | SessionEndHookOutput | void;
  onErrorOccurred?: (input: ErrorOccurredHookInput, inv: { sessionId: string }) => Promise<ErrorOccurredHookOutput | void> | ErrorOccurredHookOutput | void;
}
```

### Hook input types

```typescript
interface BaseHookInput { timestamp: number; cwd: string; }

interface PreToolUseHookInput extends BaseHookInput { toolName: string; toolArgs: unknown; }
interface PostToolUseHookInput extends BaseHookInput { toolName: string; toolArgs: unknown; toolResult: ToolResultObject; }
interface UserPromptSubmittedHookInput extends BaseHookInput { prompt: string; }
interface SessionStartHookInput extends BaseHookInput { source: "startup" | "resume" | "new"; initialPrompt?: string; }
interface SessionEndHookInput extends BaseHookInput { reason: "complete" | "error" | "abort" | "timeout" | "user_exit"; finalMessage?: string; error?: string; }
interface ErrorOccurredHookInput extends BaseHookInput { error: string; errorContext: "model_call" | "tool_execution" | "system" | "user_input"; recoverable: boolean; }
```

### Hook output types

```typescript
interface PreToolUseHookOutput { permissionDecision?: "allow" | "deny" | "ask"; permissionDecisionReason?: string; modifiedArgs?: unknown; additionalContext?: string; suppressOutput?: boolean; }
interface PostToolUseHookOutput { modifiedResult?: ToolResultObject; additionalContext?: string; suppressOutput?: boolean; }
interface UserPromptSubmittedHookOutput { modifiedPrompt?: string; additionalContext?: string; suppressOutput?: boolean; }
interface SessionStartHookOutput { additionalContext?: string; modifiedConfig?: Record<string, unknown>; }
interface SessionEndHookOutput { suppressOutput?: boolean; cleanupActions?: string[]; sessionSummary?: string; }
interface ErrorOccurredHookOutput { suppressOutput?: boolean; errorHandling?: "retry" | "skip" | "abort"; retryCount?: number; userNotification?: string; }
```

## Agent types

### CustomAgentConfig

```typescript
interface CustomAgentConfig {
  name: string;
  displayName?: string;
  description?: string;
  tools?: string[] | null;
  prompt: string;
  mcpServers?: Record<string, MCPServerConfig>;
  infer?: boolean;
}
```

## MCP types

```typescript
type MCPServerConfig = MCPLocalServerConfig | MCPRemoteServerConfig;

interface MCPLocalServerConfig {
  type?: "local" | "stdio";
  command: string;
  args: string[];
  env?: Record<string, string>;
  cwd?: string;
  tools: string[];
  timeout?: number;
}

interface MCPRemoteServerConfig {
  type: "http" | "sse";
  url: string;
  headers?: Record<string, string>;
  tools: string[];
  timeout?: number;
}
```

## Provider types

```typescript
interface ProviderConfig {
  type?: "openai" | "azure" | "anthropic";
  wireApi?: "completions" | "responses";
  baseUrl: string;
  apiKey?: string;
  bearerToken?: string;
  azure?: { apiVersion?: string };
}
```

## Model types

```typescript
interface ModelInfo {
  id: string;
  name: string;
  capabilities: ModelCapabilities;
  policy?: ModelPolicy;
  billing?: ModelBilling;
  supportedReasoningEfforts?: ReasoningEffort[];
  defaultReasoningEffort?: ReasoningEffort;
}

interface ModelCapabilities {
  supports: { vision: boolean; reasoningEffort: boolean };
  limits: {
    max_prompt_tokens?: number;
    max_context_window_tokens: number;
    vision?: { supported_media_types: string[]; max_prompt_images: number; max_prompt_image_size: number };
  };
}

interface ModelPolicy { state: "enabled" | "disabled" | "unconfigured"; terms: string; }
interface ModelBilling { multiplier: number; }
type ReasoningEffort = "low" | "medium" | "high" | "xhigh";
```

## Status types

```typescript
interface GetStatusResponse {
  version: string;
  protocolVersion: number;
}

interface GetAuthStatusResponse {
  isAuthenticated: boolean;
  authType?: "user" | "env" | "gh-cli" | "hmac" | "api-key" | "token";
  host?: string;
  login?: string;
  statusMessage?: string;
}
```

## Session metadata types

```typescript
interface SessionMetadata {
  sessionId: string;
  startTime: Date;
  modifiedTime: Date;
  summary?: string;
  isRemote: boolean;
  context?: SessionContext;
}

interface SessionContext {
  cwd: string;
  gitRoot?: string;
  repository?: string;
  branch?: string;
}

interface SessionListFilter {
  cwd?: string;
  gitRoot?: string;
  repository?: string;
  branch?: string;
}
```

## Lifecycle types

```typescript
type SessionLifecycleEventType =
  | "session.created" | "session.deleted" | "session.updated"
  | "session.foreground" | "session.background";

interface SessionLifecycleEvent {
  type: SessionLifecycleEventType;
  sessionId: string;
  metadata?: { startTime: string; modifiedTime: string; summary?: string };
}

interface ForegroundSessionInfo {
  sessionId?: string;
  workspacePath?: string;
}
```

## Event handler types

```typescript
type SessionEventType = SessionEvent["type"];
type SessionEventPayload<T extends SessionEventType> = Extract<SessionEvent, { type: T }>;
type TypedSessionEventHandler<T extends SessionEventType> = (event: SessionEventPayload<T>) => void;
type SessionEventHandler = (event: SessionEvent) => void;
type SessionLifecycleHandler = (event: SessionLifecycleEvent) => void;
type TypedSessionLifecycleHandler<K extends SessionLifecycleEventType> = (event: SessionLifecycleEvent & { type: K }) => void;
```

## RPC methods summary

### Server-scoped (via `client.rpc`)

| Method | Returns |
|--------|---------|
| `ping({ message? })` | `{ message, timestamp, protocolVersion }` |
| `models.list()` | `ModelInfo[]` |
| `tools.list({ model? })` | `ToolsListResult[]` |
| `account.getQuota()` | `{ quotaSnapshots }` |

### Session-scoped (via `session.rpc`)

| Method | Returns |
|--------|---------|
| `model.getCurrent()` | `{ modelId? }` |
| `model.switchTo({ modelId, reasoningEffort? })` | `{ modelId? }` |
| `mode.get()` | `{ mode }` |
| `mode.set({ mode })` | `{ mode }` |
| `plan.read()` | `{ exists, content, path }` |
| `plan.update({ content })` | `{}` |
| `plan.delete()` | `{}` |
| `workspace.listFiles()` | `{ files: string[] }` |
| `workspace.readFile({ path })` | `{ content }` |
| `workspace.createFile({ path, content })` | `{}` |
| `fleet.start({ prompt? })` | `{ started }` |
| `agent.list()` | `{ agents }` |
| `agent.getCurrent()` | `{ agent }` |
| `agent.select({ name })` | `{ agent }` |
| `agent.deselect()` | `{}` |
| `compaction.compact()` | `{ success, tokensRemoved, messagesRemoved }` |
| `tools.handlePendingToolCall({ requestId, result?, error? })` | `{ success }` |
| `permissions.handlePendingPermissionRequest({ requestId, result })` | `{ success }` |
| `log({ message, level?, ephemeral? })` | `{ eventId }` |
