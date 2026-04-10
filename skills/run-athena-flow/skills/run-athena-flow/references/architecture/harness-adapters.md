# Harness Adapter Architecture

The harness adapter layer isolates Athena's core from the specifics of each agent runtime.

## HarnessAdapter Interface

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

## Adapter Registry

The registry (`src/harnesses/registry.ts`) lists all adapters and resolves by ID:

- `claude-code` → `claudeHarnessAdapter` (enabled)
- `openai-codex` → `codexHarnessAdapter` (enabled)
- `opencode` → placeholder (disabled, falls through to Claude adapter)

## Claude Code Adapter

**ID:** `claude-code`
**Conversation model:** `fresh_per_turn`
**Integration:** Hook-forwarding over Unix Domain Socket

### Architecture

```
athena-flow
  ├─ spawnClaude()          # Spawns `claude -p "<prompt>"` process
  ├─ UDS Server             # NDJSON listener at .claude/run/ink-<PID>.sock
  └─ Hook Settings          # Temp JSON registering athena-hook-forwarder for all events

claude -p
  └─ athena-hook-forwarder  # Called at each lifecycle point
       └─ Connects to UDS → sends HookEventEnvelope → receives HookResultEnvelope
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `spawn.ts` | Preflight checks, builds CLI args, spawns `claude -p` |
| `generateHookSettings.ts` | Creates temp hook config JSON for all event types |
| `server.ts` | UDS server: NDJSON listener, pending request map |
| `mapper.ts` | HookEventEnvelope → RuntimeEvent conversion |
| `eventTranslator.ts` | Claude hook name → RuntimeEventKind + data |
| `decisionMapper.ts` | RuntimeDecision → HookResultPayload |
| `interactionRules.ts` | Per-event timeout and blocking rules |
| `tokenAccumulator.ts` | Parses token usage from stream-json stdout |
| `isolation.ts` | Three presets: strict, minimal, permissive |
| `flagRegistry.ts` | Declarative IsolationConfig → CLI flag mapping |

### Verification

`verifyHarness.ts` checks:
- `claude` binary exists on PATH (`resolveBinary.ts`)
- Version is parseable (`detectVersion.ts`)
- Binary executes successfully

## OpenAI Codex Adapter

**ID:** `openai-codex`
**Conversation model:** `persistent_thread`
**Integration:** JSON-RPC 2.0 over stdio to `codex app-server`

### Architecture

```
athena-flow
  ├─ AppServerManager       # Spawns `codex app-server`, manages JSON-RPC
  └─ CodexRuntime            # Handles prompts, decisions, events

codex app-server
  ├─ Notifications           # turn/started, turn/completed, item/* events
  └─ Server Requests         # Approval/input requests requiring responses
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `appServerManager.ts` | Spawns `codex app-server`, manages JSON-RPC pipe |
| `server.ts` | CodexRuntime: wraps manager, handles prompts/decisions |
| `mapper.ts` | Codex notification → RuntimeEvent |
| `eventTranslator.ts` | Codex event type translation |
| `decisionMapper.ts` | RuntimeDecision → Codex JSON-RPC response |
| `tokenUsage.ts` | Token usage parsing from Codex events |
| `workflowPluginLifecycle.ts` | Plugin install/uninstall in Codex |
| `agentConfig.ts` | Agent config management |

### JSON-RPC Methods

| Category | Methods |
|----------|---------|
| Lifecycle | `initialize`, `thread/start`, `thread/resume` |
| Turns | `turn/start`, `turn/interrupt` |
| Plugins | `plugin/install`, `plugin/uninstall` |

### JSON-RPC Server Requests

| Request | Description |
|---------|-------------|
| `item/commandExecution/requestApproval` | Approval for command execution |
| `item/fileChange/requestApproval` | Approval for file changes |
| `item/permissions/requestApproval` | General permission approval |
| `item/tool/requestUserInput` | Request for user input |

### Protocol Bindings

Codex protocol types are auto-generated from the codex app-server schema:
- `src/harnesses/codex/protocol/generated/` — 200+ auto-generated type files
- Regenerate with: `npm run protocol:codex`

## Shared Contracts

Both adapters share contracts defined in `src/harnesses/contracts/`:

- `config.ts` — `HarnessConfigProfile`, `BuildHarnessConfigInput`
- `session.ts` — `SessionController`, `UseSessionController` types
