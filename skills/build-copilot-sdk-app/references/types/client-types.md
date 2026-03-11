# Client Types Reference

## Import Patterns

```typescript
import { CopilotClient, defineTool, approveAll } from "@github/copilot-sdk";
import type {
  CopilotClientOptions,
  ConnectionState,
  GetAuthStatusResponse,
  GetStatusResponse,
  ModelInfo,
  ModelCapabilities,
  ModelPolicy,
  ModelBilling,
  SessionMetadata,
  SessionListFilter,
  SessionLifecycleEvent,
  SessionLifecycleEventType,
  SessionLifecycleHandler,
  TypedSessionLifecycleHandler,
  ForegroundSessionInfo,
  ResumeSessionConfig,
  SessionConfig,
} from "@github/copilot-sdk";
```

---

## `CopilotClientOptions` Interface

```typescript
interface CopilotClientOptions {
  // Path to CLI executable or JS entry point. Omit to use bundled CLI.
  cliPath?: string;

  // Extra arguments inserted before SDK-managed args.
  cliArgs?: string[];

  // Working directory for the CLI process. Inherits process.cwd() if unset.
  cwd?: string;

  // TCP port (TCP mode only). 0 = random available port. Default: 0.
  port?: number;

  // Use stdio transport (stdin/stdout) instead of TCP. Default: true.
  useStdio?: boolean;

  // When true, SDK is a child process of the Copilot CLI server and uses
  // its own stdio. Requires useStdio: true.
  isChildProcess?: boolean;

  // Connect to an existing CLI server over TCP. Format: "host:port" |
  // "http://host:port" | "port". Mutually exclusive with cliPath, useStdio.
  cliUrl?: string;

  // CLI server log level.
  logLevel?: "none" | "error" | "warning" | "info" | "debug" | "all";

  // Auto-start the CLI server on first use. Default: true.
  autoStart?: boolean;

  // Auto-restart the CLI server after a crash. Default: true.
  autoRestart?: boolean;

  // Environment variables for the CLI process. Inherits process.env if unset.
  env?: Record<string, string | undefined>;

  // GitHub token for authentication. Takes priority over other auth methods.
  githubToken?: string;

  // Use stored OAuth tokens or gh CLI auth. Default: true (false when
  // githubToken is provided).
  useLoggedInUser?: boolean;

  // Custom handler for listing models. Replaces the CLI query entirely.
  // Use in BYOK mode to return models from your custom provider.
  onListModels?: () => Promise<ModelInfo[]> | ModelInfo[];
}
```

---

## `ConnectionState` Type

```typescript
type ConnectionState = "disconnected" | "connecting" | "connected" | "error";
```

---

## `GetAuthStatusResponse` Interface

```typescript
interface GetAuthStatusResponse {
  isAuthenticated: boolean;
  authType?: "user" | "env" | "gh-cli" | "hmac" | "api-key" | "token";
  host?: string;       // GitHub host URL
  login?: string;      // GitHub username
  statusMessage?: string;
}
```

---

## `GetStatusResponse` Interface

```typescript
interface GetStatusResponse {
  version: string;          // Package version, e.g. "1.0.0"
  protocolVersion: number;  // Protocol version for SDK compatibility checks
}
```

---

## `ModelInfo` Interface

```typescript
interface ModelInfo {
  id: string;    // e.g. "claude-sonnet-4.5"
  name: string;  // Display name
  capabilities: ModelCapabilities;
  policy?: ModelPolicy;
  billing?: ModelBilling;
  // Only present if model supports reasoning effort:
  supportedReasoningEfforts?: ReasoningEffort[];
  defaultReasoningEffort?: ReasoningEffort;
}

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

interface ModelPolicy {
  state: "enabled" | "disabled" | "unconfigured";
  terms: string;
}

interface ModelBilling {
  multiplier: number;
}

type ReasoningEffort = "low" | "medium" | "high" | "xhigh";
```

---

## `CopilotClient` Public API

`CopilotClient` is the entry-point class. Instantiate with `new CopilotClient(options)`.

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `start` | `(): Promise<void>` | Starts the CLI server. Called automatically on first use if `autoStart: true`. |
| `stop` | `(): Promise<void>` | Stops the CLI server and releases resources. |
| `getAuthStatus` | `(): Promise<GetAuthStatusResponse>` | Returns authentication state. |
| `getStatus` | `(): Promise<GetStatusResponse>` | Returns server version and protocol version. |
| `listModels` | `(): Promise<ModelInfo[]>` | Returns available models. Uses `onListModels` if provided. |
| `createSession` | `(config: SessionConfig): Promise<CopilotSession>` | Creates and returns a new session. |
| `resumeSession` | `(sessionId: string, config: ResumeSessionConfig): Promise<CopilotSession>` | Resumes an existing session by ID. |
| `listSessions` | `(filter?: SessionListFilter): Promise<SessionMetadata[]>` | Lists available sessions with optional filters. |
| `deleteSession` | `(sessionId: string): Promise<void>` | Deletes a session permanently. |
| `on` | `(handler: SessionLifecycleHandler): () => void` | Subscribes to all session lifecycle events. Returns unsubscribe function. |
| `on<K>` | `(type: K, handler: TypedSessionLifecycleHandler<K>): () => void` | Subscribes to a specific lifecycle event type. |
| `getForegroundSession` | `(): Promise<ForegroundSessionInfo>` | Returns the foreground session in TUI+server mode. |

---

## `SessionMetadata` Interface

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
  repository?: string;  // "owner/repo" format
  branch?: string;
}
```

---

## `SessionListFilter` Interface

```typescript
interface SessionListFilter {
  cwd?: string;         // Exact match on working directory
  gitRoot?: string;
  repository?: string;  // "owner/repo" format
  branch?: string;
}
```

---

## `SessionLifecycleEvent` Interface

```typescript
type SessionLifecycleEventType =
  | "session.created"
  | "session.deleted"
  | "session.updated"
  | "session.foreground"
  | "session.background";

interface SessionLifecycleEvent {
  type: SessionLifecycleEventType;
  sessionId: string;
  metadata?: {
    startTime: string;
    modifiedTime: string;
    summary?: string;
  };
}

type SessionLifecycleHandler = (event: SessionLifecycleEvent) => void;

type TypedSessionLifecycleHandler<K extends SessionLifecycleEventType> = (
  event: SessionLifecycleEvent & { type: K }
) => void;
```

---

## `ForegroundSessionInfo` Interface

```typescript
interface ForegroundSessionInfo {
  sessionId?: string;
  workspacePath?: string;
}
```

---

## Usage Patterns

```typescript
// Basic client setup with GitHub token
const client = new CopilotClient({ githubToken: process.env.GITHUB_TOKEN });

// Connect to existing server
const client = new CopilotClient({ cliUrl: "localhost:8080" });

// Child process mode (SDK is a subprocess of the CLI server)
const client = new CopilotClient({ useStdio: true, isChildProcess: true });

// BYOK with custom models
const client = new CopilotClient({
  onListModels: () => [{ id: "gpt-4o", name: "GPT-4o", capabilities: { ... } }],
});

// Subscribe to typed lifecycle events
const unsubscribe = client.on("session.created", (event) => {
  console.log("New session:", event.sessionId);
});
unsubscribe(); // stop listening

// Check auth before creating sessions
const auth = await client.getAuthStatus();
if (!auth.isAuthenticated) throw new Error("Not authenticated");
```
