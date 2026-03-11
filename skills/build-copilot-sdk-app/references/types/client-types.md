# Client Types Reference — `@github/copilot-sdk`

Complete type reference for `CopilotClient`, its configuration, and all related types used to manage connections, authentication, models, and session lifecycles.

---

## Import Patterns

```typescript
import { CopilotClient } from "@github/copilot-sdk";
import type {
  CopilotClientOptions,
  ConnectionState,
  GetAuthStatusResponse,
  GetStatusResponse,
  ModelInfo,
  ModelCapabilities,
  ModelPolicy,
  ModelBilling,
  ReasoningEffort,
  SessionMetadata,
  SessionContext,
  SessionListFilter,
  SessionLifecycleEvent,
  SessionLifecycleEventType,
  SessionLifecycleHandler,
  TypedSessionLifecycleHandler,
  ForegroundSessionInfo,
  SessionConfig,
  ResumeSessionConfig,
} from "@github/copilot-sdk";
```

---

## `CopilotClientOptions`

Configuration passed to the `CopilotClient` constructor. All properties are optional.

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

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `cliPath` | `string` | Bundled CLI | Custom path to CLI executable or JS entry point. Omit to use the bundled CLI. |
| `cliArgs` | `string[]` | `[]` | Extra arguments inserted before SDK-managed args when spawning the CLI. |
| `cwd` | `string` | `process.cwd()` | Working directory for the CLI process. |
| `port` | `number` | `0` | TCP port (TCP mode only). `0` picks a random available port. |
| `useStdio` | `boolean` | `true` | Use stdio transport (stdin/stdout) instead of TCP. |
| `isChildProcess` | `boolean` | `false` | SDK is a child process of the Copilot CLI server. **Requires `useStdio: true`.** |
| `cliUrl` | `string` | — | Connect to an existing CLI server. Formats: `"host:port"`, `"http://host:port"`, or `"port"`. |
| `logLevel` | `string` | `"none"` | Log verbosity for the CLI server process. |
| `autoStart` | `boolean` | `true` | Automatically start the CLI server on the first `createSession()` call. |
| `autoRestart` | `boolean` | `true` | Automatically restart the CLI server if it crashes. |
| `env` | `Record<string, string \| undefined>` | `process.env` | Environment variables for the CLI process. Merges with `process.env`. |
| `githubToken` | `string` | — | Explicit GitHub token. Takes priority over `useLoggedInUser`. |
| `useLoggedInUser` | `boolean` | `true` | Use stored OAuth tokens or `gh` CLI auth. Automatically `false` when `githubToken` is set. |
| `onListModels` | `() => Promise<ModelInfo[]> \| ModelInfo[]` | — | Custom BYOK model provider. Replaces the default CLI model query entirely. |

### Mutually Exclusive Options

The constructor throws if incompatible options are combined:

| Option A | ⊗ | Option B | Reason |
|----------|---|----------|--------|
| `cliUrl` | ⊗ | `cliPath` | Cannot spawn a local CLI and connect to a remote server simultaneously. |
| `cliUrl` | ⊗ | `useStdio: true` | Remote connections require TCP, not stdio. |
| `cliUrl` | ⊗ | `githubToken` / `useLoggedInUser` | The external server manages its own authentication. |
| `isChildProcess: true` | requires | `useStdio: true` | Child process mode communicates exclusively via stdio. |

---

## `ConnectionState`

Represents the current state of the client-to-server connection. Returned by `client.getState()`.

```typescript
type ConnectionState = "disconnected" | "connecting" | "connected" | "error";
```

- `"disconnected"` — No active connection. Initial state or after `stop()`.
- `"connecting"` — Connection handshake in progress.
- `"connected"` — Ready to create/resume sessions.
- `"error"` — Connection failed. Check logs. Will auto-recover if `autoRestart: true`.

---

## `GetAuthStatusResponse`

Returned by `client.getAuthStatus()`. Indicates how (or if) the client is authenticated.

```typescript
interface GetAuthStatusResponse {
  isAuthenticated: boolean;
  authType?: "user" | "env" | "gh-cli" | "hmac" | "api-key" | "token";
  host?: string;
  login?: string;
  statusMessage?: string;
}
```

| Property | Description |
|----------|-------------|
| `isAuthenticated` | `true` if credentials are valid and accepted by the server. |
| `authType` | Authentication method used. `"user"` = interactive OAuth; `"env"` = environment variable; `"gh-cli"` = GitHub CLI stored token; `"hmac"` = HMAC signature; `"api-key"` = API key; `"token"` = explicit token. |
| `host` | GitHub host URL, e.g. `"https://github.com"` or a GHES instance. |
| `login` | Authenticated GitHub username. |
| `statusMessage` | Human-readable auth status or error message. |

---

## `GetStatusResponse`

Returned by `client.getStatus()`. Reports server version info for compatibility checks.

```typescript
interface GetStatusResponse {
  version: string;
  protocolVersion: number;
}
```

| Property | Description |
|----------|-------------|
| `version` | Package version string, e.g. `"1.0.0"`. |
| `protocolVersion` | Wire protocol version number. Used for SDK-to-CLI compatibility validation. |

---

## Model Types

### `ModelInfo`

Describes a single model available through the client. Returned in arrays by `client.listModels()`.

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
```

| Property | Description |
|----------|-------------|
| `id` | Unique model identifier, e.g. `"claude-sonnet-4.5"`, `"gpt-4o"`. Used in `SessionConfig.model`. |
| `name` | Human-readable display name. |
| `capabilities` | Vision support, token limits, and feature flags. |
| `policy` | Organization-level enablement state and terms. |
| `billing` | Billing multiplier for quota consumption. |
| `supportedReasoningEfforts` | Present only if the model supports reasoning effort. Array of allowed levels. |
| `defaultReasoningEffort` | The default reasoning effort when none is specified. |

### `ModelCapabilities`

```typescript
interface ModelCapabilities {
  supports: {
    vision: boolean;
    reasoningEffort: boolean;
  };
  limits: {
    max_prompt_tokens?: number;
    max_context_window_tokens: number;
    vision?: {
      supported_media_types: string[];
      max_prompt_images: number;
      max_prompt_image_size: number;
    };
  };
}
```

| Property | Description |
|----------|-------------|
| `supports.vision` | Whether the model accepts image inputs. |
| `supports.reasoningEffort` | Whether the model supports adjustable reasoning effort. |
| `limits.max_prompt_tokens` | Maximum tokens allowed in the prompt. Optional; omitted when unlimited. |
| `limits.max_context_window_tokens` | Total context window size in tokens. |
| `limits.vision` | Vision-specific constraints. Only present when `supports.vision` is `true`. |
| `limits.vision.supported_media_types` | Accepted MIME types, e.g. `["image/png", "image/jpeg"]`. |
| `limits.vision.max_prompt_images` | Maximum number of images per prompt. |
| `limits.vision.max_prompt_image_size` | Maximum size in bytes for a single image. |

### `ModelPolicy`

```typescript
interface ModelPolicy {
  state: "enabled" | "disabled" | "unconfigured";
  terms: string;
}
```

| Property | Description |
|----------|-------------|
| `state` | `"enabled"` = usable; `"disabled"` = blocked by org policy; `"unconfigured"` = no policy set. |
| `terms` | Policy terms text or URL. May require display/acceptance before use. |

### `ModelBilling`

```typescript
interface ModelBilling {
  multiplier: number;
}
```

| Property | Description |
|----------|-------------|
| `multiplier` | Cost multiplier relative to baseline. `1.0` = standard rate; `2.0` = double consumption. |

### `ReasoningEffort`

```typescript
type ReasoningEffort = "low" | "medium" | "high" | "xhigh";
```

Controls how much "thinking" a model performs. Higher values increase quality at the cost of latency and tokens. Used in `SessionConfig.reasoningEffort`.

---

## Session Metadata Types

### `SessionMetadata`

Returned by `client.listSessions()`. Describes a persisted session.

```typescript
interface SessionMetadata {
  sessionId: string;
  startTime: Date;
  modifiedTime: Date;
  summary?: string;
  isRemote: boolean;
  context?: SessionContext;
}
```

| Property | Description |
|----------|-------------|
| `sessionId` | Unique session identifier. Use with `resumeSession()` or `deleteSession()`. |
| `startTime` | When the session was created. |
| `modifiedTime` | When the session was last active. |
| `summary` | AI-generated session summary (set after first few turns). |
| `isRemote` | `true` if the session is running on a remote server. |
| `context` | Workspace context captured at session creation time. |

### `SessionContext`

```typescript
interface SessionContext {
  cwd: string;
  gitRoot?: string;
  repository?: string;
  branch?: string;
}
```

| Property | Description |
|----------|-------------|
| `cwd` | Working directory at session creation. |
| `gitRoot` | Root of the git repository, if inside one. |
| `repository` | Repository in `"owner/repo"` format. |
| `branch` | Active git branch name. |

### `SessionListFilter`

Optional filter passed to `client.listSessions()`. All fields are optional; multiple fields are AND-combined.

```typescript
interface SessionListFilter {
  cwd?: string;
  gitRoot?: string;
  repository?: string;
  branch?: string;
}
```

| Property | Description |
|----------|-------------|
| `cwd` | Exact match on the session's working directory. |
| `gitRoot` | Exact match on git root path. |
| `repository` | Filter by `"owner/repo"` string. |
| `branch` | Filter by branch name. |

---

## Session Lifecycle Events

### `SessionLifecycleEventType`

```typescript
type SessionLifecycleEventType =
  | "session.created"
  | "session.deleted"
  | "session.updated"
  | "session.foreground"
  | "session.background";
```

| Event | Trigger |
|-------|---------|
| `session.created` | A new session is created via `createSession()`. |
| `session.deleted` | A session is permanently deleted via `deleteSession()`. |
| `session.updated` | Session metadata changes (e.g., new summary after turns). |
| `session.foreground` | Session moves to foreground (TUI+server mode). |
| `session.background` | Session moves to background (TUI+server mode). |

### `SessionLifecycleEvent`

```typescript
interface SessionLifecycleEvent {
  type: SessionLifecycleEventType;
  sessionId: string;
  metadata?: {
    startTime: string;
    modifiedTime: string;
    summary?: string;
  };
}
```

### Event Handlers

```typescript
// Wildcard handler — receives all lifecycle events
type SessionLifecycleHandler = (event: SessionLifecycleEvent) => void;

// Typed handler — receives only events of type K, with narrowed type field
type TypedSessionLifecycleHandler<K extends SessionLifecycleEventType> = (
  event: SessionLifecycleEvent & { type: K }
) => void;
```

### `ForegroundSessionInfo`

Used internally for TUI+server foreground tracking.

```typescript
interface ForegroundSessionInfo {
  sessionId?: string;
  workspacePath?: string;
}
```

---

## `CopilotClient` Class — Public API

### Constructor

```typescript
const client = new CopilotClient(options?: CopilotClientOptions);
```

Creates a client instance. Throws immediately if mutually exclusive options are provided.

### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `start` | `()` | `Promise<void>` | Starts the CLI server. Auto-called on first `createSession()` if `autoStart: true`. |
| `stop` | `()` | `Promise<Error[]>` | Graceful shutdown with retry logic. Returns an array of errors (empty = success). **Does not throw.** |
| `forceStop` | `()` | `Promise<void>` | Sends SIGKILL to the CLI process. Use only when `stop()` hangs. |
| `createSession` | `(config: SessionConfig)` | `Promise<CopilotSession>` | Creates a new session. `config.onPermissionRequest` is required. |
| `resumeSession` | `(sessionId, config: ResumeSessionConfig)` | `Promise<CopilotSession>` | Resumes a persisted session by ID. Full history is restored. |
| `getState` | `()` | `ConnectionState` | Returns the current connection state. Synchronous. |
| `ping` | `(message?: string)` | `Promise<{message, timestamp, protocolVersion?}>` | Verifies server connectivity. Optional echo message. |
| `getStatus` | `()` | `Promise<GetStatusResponse>` | Returns CLI version and protocol version. |
| `getAuthStatus` | `()` | `Promise<GetAuthStatusResponse>` | Returns current authentication status and method. |
| `listModels` | `()` | `Promise<ModelInfo[]>` | Lists available models. Cached after first call; cache clears on disconnect. |
| `getLastSessionId` | `()` | `Promise<string \| undefined>` | Returns the most recently active session ID, or `undefined`. |
| `deleteSession` | `(sessionId: string)` | `Promise<void>` | **Permanently** deletes a session and its history. Irreversible. |
| `listSessions` | `(filter?: SessionListFilter)` | `Promise<SessionMetadata[]>` | Lists sessions, optionally filtered by workspace context. |
| `getForegroundSessionId` | `()` | `Promise<string \| undefined>` | Returns the foreground session ID. **TUI+server mode only.** |
| `setForegroundSessionId` | `(sessionId: string)` | `Promise<void>` | Sets the foreground session. **TUI+server mode only.** |
| `on` (typed) | `<K>(type: K, handler: TypedSessionLifecycleHandler<K>)` | `() => void` | Subscribe to a specific lifecycle event. Returns an unsubscribe function. |
| `on` (wildcard) | `(handler: SessionLifecycleHandler)` | `() => void` | Subscribe to all lifecycle events. Returns an unsubscribe function. |

### `rpc` Getter — Low-Level RPC Access

The `rpc` property exposes raw JSON-RPC methods for advanced use cases. Prefer the high-level methods above for typical usage.

```typescript
get rpc: {
  ping(params: { message?: string }): Promise<{
    message: string;
    timestamp: number;
    protocolVersion: number;
  }>;

  models: {
    list(): Promise<{ models: ModelInfo[] }>;
  };

  tools: {
    list(params?: { model?: string }): Promise<{ tools: ToolInfo[] }>;
  };

  account: {
    getQuota(): Promise<{
      quotaSnapshots: Record<string, QuotaInfo>;
    }>;
  };
}
```

| RPC Method | Description |
|------------|-------------|
| `rpc.ping(params)` | Raw ping with full response including `protocolVersion`. |
| `rpc.models.list()` | Raw model list (returns `{ models: ModelInfo[] }` wrapper). |
| `rpc.tools.list(params?)` | Lists available tools, optionally filtered by model ID. |
| `rpc.account.getQuota()` | Returns quota snapshots keyed by quota category. |

---

## Usage Examples

### 1. Default Client — Create and Clean Up

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient({
  githubToken: process.env.GITHUB_TOKEN,
});

// autoStart: true means start() is called implicitly on first createSession()
const session = await client.createSession({
  model: "gpt-4o",
  onPermissionRequest: async () => ({ granted: true }),
  onTurn: (turn) => console.log(turn.message),
});

// ... use session ...

session.disconnect();
const errors = await client.stop();
if (errors.length > 0) {
  console.error("Shutdown errors:", errors);
}
```

### 2. Connect to an External Server

```typescript
const client = new CopilotClient({
  cliUrl: "localhost:3000",
  // No githubToken or useLoggedInUser — the external server handles auth.
  // No cliPath or useStdio — mutually exclusive with cliUrl.
});

await client.start();
const status = await client.getStatus();
console.log(`Connected to server v${status.version}`);
```

### 3. BYOK — Custom Model Provider

```typescript
const client = new CopilotClient({
  onListModels: async () => [
    {
      id: "my-custom-model",
      name: "My Custom Model",
      capabilities: {
        supports: { vision: false, reasoningEffort: false },
        limits: { max_context_window_tokens: 128_000 },
      },
    },
  ],
});

const models = await client.listModels();
// models === [{ id: "my-custom-model", ... }]
```

### 4. Session Lifecycle Event Subscription

```typescript
// Typed — only receives "session.created" events
const unsub1 = client.on("session.created", (event) => {
  // event.type is narrowed to "session.created"
  console.log("New session:", event.sessionId);
});

// Wildcard — receives all lifecycle events
const unsub2 = client.on((event) => {
  console.log(`[${event.type}] ${event.sessionId}`);
});

// Unsubscribe when done
unsub1();
unsub2();
```

---

## Important Caveats

1. **`stop()` returns `Error[]`, does NOT throw.** An empty array means clean shutdown. Always check the returned array for errors.

2. **`forceStop()` uses SIGKILL.** Only call this as a last resort when `stop()` hangs. It does not allow graceful cleanup.

3. **`listModels()` results are cached.** The first call queries the server; subsequent calls return the cached result. The cache is automatically cleared on disconnect.

4. **`deleteSession()` is permanent.** It removes the session and its entire history. This is different from `session.disconnect()`, which preserves data for later `resumeSession()`.

5. **`getForegroundSessionId()` / `setForegroundSessionId()` are TUI+server mode only.** They return `undefined` or silently fail in other modes.

6. **Constructor validates mutual exclusion.** Passing incompatible options (e.g., `cliUrl` + `cliPath`) throws synchronously at construction time.

7. **`autoStart: true` defers `start()`.** The CLI server is not started in the constructor — it is started implicitly on the first `createSession()` or `resumeSession()` call.