# Hooks and Permissions

Hooks are how Athena observes and controls agent runtimes. Each harness fires events at lifecycle points; Athena receives and processes them. The examples below use Claude Code's hook system, but the same event types are available on Codex via its event translation layer.

## Hook Protocol

```
Claude Code → stdin JSON → athena-hook-forwarder → UDS NDJSON → Athena runtime
```

For events that expect a decision (`interaction.expectsDecision: true`), Athena writes a response back through the socket before the forwarder exits. Exit code `0` = passthrough, exit code `2` = block.

Auto-passthrough timeout: 5 seconds (5 minutes for permission/question events).

## Hook Event Types

### Tool Events (require `"*"` matcher)

| Hook Name | RuntimeEventKind | Can Block | Description |
|-----------|-----------------|-----------|-------------|
| `PreToolUse` | `tool.pre` | Yes | Before Claude invokes a tool |
| `PostToolUse` | `tool.post` | No | After a tool completes and returns its result |
| `PostToolUseFailure` | `tool.failure` | No | After a tool invocation results in an error |
| `PermissionRequest` | `permission.request` | Yes | Claude Code requests explicit permission for a tool |

### Non-Tool Events

| Hook Name | RuntimeEventKind | Description |
|-----------|-----------------|-------------|
| `SessionStart` | `session.start` | New Claude Code session begins |
| `SessionEnd` | `session.end` | Claude Code session ends |
| `UserPromptSubmit` | `user.prompt` | User submits a prompt |
| `Stop` | `stop.request` | Claude Code's stop hook fires |
| `SubagentStart` | `subagent.start` | A subagent session starts |
| `SubagentStop` | `subagent.stop` | A subagent session ends |
| `Notification` | `notification` | Informational notification from Claude Code |
| `PreCompact` | `compact.pre` | Before context compaction occurs |
| `Setup` | `setup` | Session init or maintenance |

## Blocking Decisions

Events marked "Can Block" allow Athena to respond before the agent proceeds:

- **passthrough** — allow the action
- **block** — deny with a reason string (sent to agent via stderr)
- **json** — structured response with semantic intent

### RuntimeDecision Types

```typescript
type RuntimeDecision =
  | { type: 'passthrough' }
  | { type: 'block'; reason: string }
  | { type: 'json'; intent: RuntimeIntent };
```

### RuntimeIntent Values

- `permission_allow` — Allow a permission request
- `permission_deny` — Deny a permission request
- `question_answer` — Answer an AskUserQuestion
- `pre_tool_allow` — Allow a PreToolUse event
- `pre_tool_deny` — Deny a PreToolUse event
- `stop_block` — Block a stop request

## Decision Flow

Athena's `RuntimeController` processes events:

1. Check deny-first rules (tool name pattern matching)
2. Route permission requests to the permission queue
3. Auto-allow non-denied PreToolUse events
4. Route AskUserQuestion to question handler
5. Apply isolation policy automatically for `tool.pre` and `permission.request` events

Decisions with `source: 'rule'` are auto-applied. Decisions requiring user input pause the event feed.

## Isolation Presets

Control what the agent is allowed to do per-session:

| Preset | MCP Servers | Allowed Tools |
|--------|-------------|---------------|
| `strict` | Blocked | `Read`, `Edit`, `Glob`, `Grep`, `Bash`, `Write` |
| `minimal` | Project servers | Above + `WebSearch`, `WebFetch`, `Task`, `Agent`, `Skill`, `mcp__*` |
| `permissive` | Project servers | Above + `NotebookEdit` |

All presets use `--setting-sources ""` to fully isolate from Claude Code's own settings file. Tool enforcement is done via `PreToolUse` hooks.

```bash
athena-flow --isolation=minimal
```

Workflows can declare an isolation preset. If the workflow requires a more permissive level than the user's setting, Athena upgrades it with a warning.
