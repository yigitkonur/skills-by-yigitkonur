# CLI Command Reference

Complete parameter and flag reference for all `cli-codex-subagent` commands.

## run / task start — Spawn a task

Create and start a task from a prompt file. Returns immediately (async) or blocks until done.

```bash
cli-codex-subagent run <task.md> [options]
# shorthand for:
cli-codex-subagent task start <task.md> [options]
```

### Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--effort <level>` | enum | `medium` | Reasoning depth: `none\|minimal\|low\|medium\|high\|xhigh` |
| `--auto-approve` | flag | off | Auto-accept all shell-command and file approvals |
| `--approval-policy <p>` | enum | `on-request` | `never\|on-failure\|on-request\|untrusted` |
| `--follow` | flag | off | Stream events; block until terminal state |
| `--wait` | flag | off | Block until terminal state, no streaming |
| `--session <sesId>` | string | — | Attach to an existing session (preserves context) |
| `--context-file <f>` | string | — | Prepend a file as context (repeatable) |
| `--output-schema <f>` | string | — | JSON Schema file for structured output |
| `--label <label>` | string | — | Tag for filtering in `task list` |
| `--model <model>` | string | — | Override the model |
| `--json` | flag | off | Print `{taskId, sessionId}` JSON and exit immediately |

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Task completed successfully |
| `1` | Task failed |
| `2` | Task blocked — needs `request answer` |
| `3` | Reconnect / network error |
| `5` | Task file not found |

### Response (default async)

Prints `taskId` and `sessionId`, then exits. Task runs in the daemon.

```
Started task tsk_abc123 in session ses_xyz789
```

### Response (--json)

```json
{ "taskId": "tsk_abc123", "sessionId": "ses_xyz789" }
```

### Frontmatter alternative

Options can be embedded in the task file YAML frontmatter:

```markdown
---
label: "wave-1:auth"
effort: low
session: ses_abc123
context_files:
  - ./notes.md
  - ./schema.ts
output_schema: ./response-schema.json
base_instructions_file: ./AGENTS.md
cwd: /project
model: gpt-4o
---

Your task prompt here...
```

Frontmatter keys: `label`, `effort`, `session`, `context_files` (array), `output_schema` (path or inline JSON), `base_instructions_file`, `cwd`, `model`.

---

## task wait — Block until done

Block until a task reaches a terminal state. No streaming output.

```bash
cli-codex-subagent task wait <taskId> [--timeout-ms N]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--timeout-ms <N>` | daemon default | Max wait in ms before returning current status |

Returns exit code 0/1/2 matching task outcome.

---

## task follow — Stream events

Attach to a running task and stream normalized events until terminal state.

```bash
cli-codex-subagent task follow <taskId> [--stream-json]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--stream-json` | off | Emit raw JSON events instead of human-readable lines |

Output format (human-readable):
```
TURN    019d786c-...
THINK   Inspecting the repository structure
CMD     find src -name "*.ts" → exit=0 (0.3s)
FILE    src/auth.ts (modified)
TOKENS  18629 / 996147 (1.9%)
MSG     I've updated the auth module...
DONE    completed
```

---

## task steer — Continue in same session

Run a follow-up prompt in the same session as a completed task. The agent retains full prior context.

```bash
cli-codex-subagent task steer <taskId> <followup.md> [--follow] [--effort <level>]
```

**Requires:** the referenced task must be in a terminal state (`completed`, `failed`). Attempting to steer a still-running task returns an error.

---

## task read — Inspect task state

Print task metadata and artifact paths.

```bash
cli-codex-subagent task read <taskId> [--field <key>] [--json]
```

| Flag | Description |
|------|-------------|
| `--field <key>` | Print a single field value (e.g. `status`, `artifacts.timelineLogPath`) |
| `--json` | Emit full task record as JSON |

Output includes: status, session, model, effort, cwd, created/started/completed timestamps, artifact paths (timeline, events, summary, stderr), last output tail.

---

## task events — Full event log

Print or stream the `events.jsonl` for a task.

```bash
cli-codex-subagent task events <taskId> [--raw] [--tail N] [--follow]
```

| Flag | Description |
|------|-------------|
| `--raw` | Emit raw app-server events (unprocessed) |
| `--tail <N>` | Show only the last N events |
| `--follow` | Stream new events as they arrive |

---

## task list — List tasks

```bash
cli-codex-subagent task list [--status <s>] [--label <l>] [--quiet] [--json]
```

| Flag | Description |
|------|-------------|
| `--status <s>` | Filter: `completed\|failed\|working\|cancelled` |
| `--label <l>` | Filter by label tag |
| `--quiet` | Print task IDs only (one per line) |
| `--json` | Emit JSON array |

---

## task cancel — Cancel a task

```bash
cli-codex-subagent task cancel <taskId>
```

Cancels an actively running task. No-op on already-terminal tasks.

---

## request list — Find pending requests

```bash
cli-codex-subagent request list [--task <taskId>] [--json]
```

Lists all requests pending a response. Requests are created when a task blocks on a shell-command approval, user-input question, or file-write approval.

---

## request read — Inspect a request

```bash
cli-codex-subagent request read <reqId>
```

Shows request type, payload (question text, command details, choices), and which task it belongs to.

---

## request answer — Unblock a task

```bash
cli-codex-subagent request answer <reqId> [options]
```

| Flag | Description |
|------|-------------|
| `--decision <d>` | `accept-session\|accept-once\|reject` (for command/file approvals) |
| `--choice <N>` | 1-indexed choice for multiple-choice prompts |
| `--text-file <f>` | File containing free-text answer |
| `--custom-file <f>` | File with custom response payload |
| `--json-file <f>` | JSON file with full response payload |

After answering, resume monitoring with:
```bash
cli-codex-subagent task follow <taskId>
```

---

## session list / read / create

```bash
cli-codex-subagent session list [--json]
cli-codex-subagent session read <sesId>
cli-codex-subagent session create
```

Sessions are auto-created when you run a task. Use `--session <sesId>` to reuse a session (and its context) for a new task.

---

## prompt inspect / lint

```bash
cli-codex-subagent prompt inspect <task.md>   # Show resolved prompt with context
cli-codex-subagent prompt lint <task.md>       # Validate frontmatter and context files
```

Use before running to verify the prompt will be loaded correctly.

---

## model list

```bash
cli-codex-subagent model list [--json]
```

Lists available models from the configured Codex runtime.

---

## account

```bash
cli-codex-subagent account
```

Shows rate limits, token quotas, and account info from the Codex runtime.

---

## doctor

```bash
cli-codex-subagent doctor
```

Full readiness check: verifies daemon connectivity, Codex runtime availability, auth configuration, and state directory layout.

---

## daemon status / stop / run

```bash
cli-codex-subagent daemon status   # Is the daemon running?
cli-codex-subagent daemon stop     # Graceful shutdown
cli-codex-subagent daemon run      # Run in foreground (debug mode)
```

The daemon auto-starts on first `run` or `task start`. You only need these commands for diagnostics or forced restarts.

---

## Effort levels

| Level | Reasoning depth | Reliability | Typical tokens | Use for |
|-------|----------------|-------------|----------------|---------|
| `none` | Off | ~100% | ~5K | Trivial output, no reasoning |
| `minimal` | Minimal | ~100% | ~8K | Simple transforms |
| `low` | Low | ~100% | ~15K | 1–3 commands, simple file ops |
| `medium` | Medium | ~50–70% | 30–110K | Multi-step coding, refactoring |
| `high` | High | ~30–50% | 60–110K | Complex multi-file reasoning |
| `xhigh` | Max | Untested | — | Deep research, architecture |

**Default to `low` unless the task genuinely needs planning.** Higher effort = more reasoning tokens = higher chance of process exit before work completes.

---

## Approval policies

| Policy | Behavior |
|--------|---------|
| `never` | Auto-approve everything (equivalent to `--auto-approve`) |
| `on-failure` | Auto-approve unless a command has previously failed |
| `on-request` | Default — block and require explicit `request answer` |
| `untrusted` | Stricter — blocks on more approval types |
