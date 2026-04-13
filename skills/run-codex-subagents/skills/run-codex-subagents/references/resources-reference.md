# CLI Inspection Reference

How to inspect tasks, sessions, requests, and artifacts using `cli-codex-subagent` commands. Replaces the old `task:///` URI resource model.

## Task list — Scoreboard

```bash
cli-codex-subagent task list
cli-codex-subagent task list --status failed
cli-codex-subagent task list --label "wave-1"
cli-codex-subagent task list --json
cli-codex-subagent task list --quiet    # IDs only
```

**When to use:** Between waves to check overall status. After a failure to find which tasks need recovery.

**Example output:**
```
tsk_abc123  [done]    completed   23s    109K tokens   wave-1
tsk_def456  [done]    completed   45s    85K tokens    wave-1
tsk_ghi789  [busy]    working     62s    running       wave-1
tsk_jkl012  [fail]    failed      8s     —             wave-1

Total: 4 tasks
```

---

## Task read — Task detail

```bash
cli-codex-subagent task read <taskId>
cli-codex-subagent task read <taskId> --json
cli-codex-subagent task read <taskId> --field status
cli-codex-subagent task read <taskId> --field artifacts.timelineLogPath
```

**When to use:** Inspect one task's full metadata after completion or failure.

**Output includes:**
- `status`, `effort`, `model`, `cwd`, `labels`
- `sessionId` — for continuing with `--session` or `task steer`
- Timestamps: `createdAt`, `startedAt`, `completedAt`
- Error message if failed
- Artifact paths (timeline, events, summary, stderr)
- Last output tail

**Scripting — get session id:**
```bash
SESSION=$(cli-codex-subagent task read tsk_abc123 --field sessionId)
cli-codex-subagent run followup.md --session "$SESSION" --follow
```

---

## Task events — Full event trace

```bash
cli-codex-subagent task events <taskId>
cli-codex-subagent task events <taskId> --tail 20
cli-codex-subagent task events <taskId> --raw           # raw app-server events
cli-codex-subagent task events <taskId> --follow        # stream as task runs
```

**When to use:** Debug trace — every notification including reasoning, commands, file changes, token usage. Use `--raw` for the lowest-level JSON.

**Output format (default — normalized):**
```
TURN    019d786c-...
THINK   Inspecting the repository
CMD     find src -name "*.ts" → exit=0 (0.3s)
FILE    src/auth.ts (modified)
TOKENS  18629 / 996147 (1.9%)
MSG     I've updated the auth module.
DONE    completed
```

**Raw output:** One JSON object per line (full `events.jsonl` format). Includes delta events, hooks, and all streaming data. See `event-types.md`.

**Disk path** (direct access):
```bash
cat ~/.cli-codex-subagent/tasks/<taskId>/events.jsonl
```

---

## Task follow — Live event stream

```bash
cli-codex-subagent task follow <taskId>
cli-codex-subagent task follow <taskId> --stream-json
```

The primary monitoring tool for running tasks. Streams normalized events until the task reaches a terminal state.

**Also available as a flag on `run`:**
```bash
cli-codex-subagent run task.md --follow
```

**Disk path** (for direct tail):
```bash
tail -f ~/.cli-codex-subagent/tasks/<taskId>/timeline.log
```

See `timeline-format.md` for all 16 line types.

---

## Summary log — Artifact tails

The summary log (last ~20 human-readable lines) is shown automatically by `task read`.

**Disk path:**
```bash
cat ~/.cli-codex-subagent/tasks/<taskId>/summary.log
```

Format: `[HH:MM:SS] {type}: {detail}`. Types: `cmd`, `agent`, `turn completed`, `turn failed`, `ERROR`.

---

## Verbose log — Full command output

Not exposed as a CLI command; access directly from disk:

```bash
cat ~/.cli-codex-subagent/tasks/<taskId>/verbose.log
```

Contains full stdout/stderr from every command, not just the one-liner summary.

---

## Request list — Pending approvals

```bash
cli-codex-subagent request list
cli-codex-subagent request list --task <taskId>
cli-codex-subagent request list --json
```

**When to use:** When a task exits with code `2` (blocked). Lists all pending requests across all tasks.

---

## Request read — Inspect what's needed

```bash
cli-codex-subagent request read <reqId>
```

Shows the request type, full payload (command being approved, question text, available choices), and the task that created it.

---

## Session read — Session metadata

```bash
cli-codex-subagent session read <sesId>
cli-codex-subagent session list
```

Shows session status, the tasks that ran within it, and context window usage. Use to find the right `sesId` for `task steer` or `--session`.

---

## Disk layout

All artifacts are under `~/.cli-codex-subagent/tasks/<taskId>/`:

| File | CLI command |
|------|------------|
| `timeline.log` | `task follow <id>` (or `task events <id>`) |
| `events.jsonl` | `task events <id> --raw` |
| `summary.log` | Shown by `task read <id>` |
| `verbose.log` | Direct disk access only |
| `stderr.log` | Direct disk access only |
| `prompt.md` | The original prompt file (preserved) |
| `context.manifest.json` | Context files used |

The state root can be overridden with `CLI_CODEX_SUBAGENT_STATE_DIR`.
