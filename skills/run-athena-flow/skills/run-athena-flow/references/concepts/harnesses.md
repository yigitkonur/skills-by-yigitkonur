# Harnesses

A harness is the agent runtime Athena wraps. The harness abstraction isolates Athena's workflow, plugin, and UI systems from the specifics of any one agent.

## Supported Harnesses

| Harness | Status | Integration |
|---------|--------|-------------|
| `claude-code` | Production | Hook-forwarding over Unix Domain Socket |
| `openai-codex` | Production | JSON-RPC via app-server protocol |
| `opencode` | Coming soon | TBD |

## Architecture

**Claude Code:**

```
Claude Code → athena-hook-forwarder (stdin) → UDS NDJSON → Athena runtime
```

**OpenAI Codex:**

```
Codex → codex-app-server (JSON-RPC) → Athena runtime
```

Both produce normalized `RuntimeEvent` objects. Workflows, plugins, and the UI work identically regardless of harness.

## Harness Capabilities

| Feature | Claude Code | Codex |
|---------|-------------|-------|
| Session persistence | Yes | Yes |
| MCP servers | Yes | Yes |
| Workflows + loops | Yes | Yes |
| Isolation presets | Yes | Yes |
| Ephemeral sessions | Yes | Yes |
| Skills / commands | Yes | Yes |
| Hook events | 19 event types | Event translation layer |

## How Claude Code Integration Works

1. **Hook registration** — Athena generates a temporary settings file registering `athena-hook-forwarder` for all Claude Code hook events. Tool events use a `"*"` matcher to receive all tool calls.
2. **Event forwarding** — Claude Code calls the forwarder synchronously at each lifecycle point. The forwarder reads stdin, writes NDJSON to the UDS, and exits in single-digit milliseconds.
3. **Socket transport** — Per-instance socket at `<projectDir>/.claude/run/ink-<PID>.sock`. Local-only, no port management.

### Claude Code Hook Event Types

SessionStart, SessionEnd, UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, Stop, SubagentStart, SubagentStop, Notification, PreCompact, Setup, TeammateIdle, TaskCompleted, ConfigChange, InstructionsLoaded, WorktreeCreate, WorktreeRemove

### Claude Code Conversation Model

`fresh_per_turn` — spawns a new `claude -p` process per turn. Each turn is a fresh invocation with the prompt passed via `-p` flag.

## How Codex Integration Works

1. **App-server protocol** — Athena communicates with Codex via a JSON-RPC 2.0 protocol through `codex-app-server`.
2. **Event translation** — Codex events (notifications and server requests) are mapped to Athena's `RuntimeEvent` schema via a comprehensive translation layer.
3. **Decision mapping** — `RuntimeDecision` objects are converted back to Codex-compatible JSON-RPC responses.
4. **Turn management** — Codex uses a persistent thread conversation model with turn-based session management.

### Codex Conversation Model

`persistent_thread` — maintains a thread across turns. Methods: `initialize`, `thread/start`, `thread/resume`, `turn/start`, `turn/interrupt`, `plugin/install`.

### Codex Server Requests (require response)

- `item/commandExecution/requestApproval`
- `item/fileChange/requestApproval`
- `item/permissions/requestApproval`
- `item/tool/requestUserInput`

## The RuntimeConnector Interface

Each harness implements:

```typescript
type Runtime = {
  start(): Promise<void>;
  stop(): void;
  getStatus(): 'stopped' | 'running';
  getLastError(): RuntimeStartupError | null;
  onEvent(handler: RuntimeEventHandler): () => void;
  onDecision(handler: RuntimeDecisionHandler): () => void;
  sendDecision(eventId: string, decision: RuntimeDecision): void;
};
```

Plugin and workflow authors work with normalized `RuntimeEvent` types — they never interact with the harness interface directly.

## The HarnessAdapter Interface

```typescript
type HarnessAdapter = {
  id: AthenaHarness;              // 'claude-code' | 'openai-codex' | 'opencode'
  label: string;
  enabled: boolean;
  capabilities: HarnessCapabilities;
  verify?: () => HarnessVerificationResult;
  createRuntime: (input) => Runtime;
  createSessionController: (input) => SessionController;
  useSessionController: (input) => UseSessionControllerResult;
  resolveConfigProfile: () => HarnessConfigProfile;
};
```

## Configuration

```json
{
  "harness": "claude-code"
}
```

Or for Codex:

```json
{
  "harness": "openai-codex"
}
```

Set via config file or the setup wizard (`athena-flow setup`).
