# Async Task Execution

Experimental support for long-running MCP operations via mcpc's async task system — covering detection, execution modes, polling, crash resilience, and scripting patterns.

## What async tasks are

Some MCP servers expose long-running operations (data exports, batch processing, model inference jobs) that would exceed a normal request timeout. mcpc detects whether a connected server supports the task protocol by inspecting `capabilities.tasks` in the server's initialize response.

When task support is present, tool calls can be launched asynchronously instead of blocking the CLI until completion. The server manages the task lifecycle; mcpc provides commands to monitor and retrieve results.

```bash
# Check whether the connected server supports tasks
mcpc --json @session | jq '.capabilities.tasks // "not supported"'
```

If the output is not `"not supported"`, the server has declared task capabilities and the flags below are available.

## Three execution modes

### 1. Awaited (`--task`)

```bash
mcpc @session tools-call slow-tool arg:=value --task
```

- Blocks the CLI until the task reaches a terminal state (`completed`, `failed`, or `cancelled`)
- Displays a spinner in the terminal with live progress updates streamed from the server
- On completion, prints the tool result exactly as a normal synchronous tool call would
- Press **ESC** while the spinner is active to detach mid-flight — the task continues running server-side and mcpc prints the task ID so you can poll later
- ESC-to-detach is only available in TTY mode; it has no effect when output is piped or redirected

Use awaited mode when you need the result immediately and can afford to keep the terminal open.

### 2. Detached (`--task --detach`)

```bash
mcpc --json @session tools-call slow-tool arg:=value --task --detach
```

- Returns immediately after the server acknowledges task creation
- JSON output contains the task ID and initial status:

```json
{
  "taskId": "task_abc123",
  "status": "submitted"
}
```

- The task continues running server-side with no CLI process attached
- Use `--json` with this mode — the task ID is the only handle you have for later retrieval

Use detached mode for fire-and-forget workloads, parallel fan-out, or when a task is expected to take longer than your terminal session.

### 3. Manual polling (after detach or crash recovery)

```bash
mcpc --json @session tasks-get <taskId>
```

- Fetches the current state of a previously submitted task
- Returns the full status object including result when the task has completed
- Poll this on a schedule until the status field reaches a terminal state

Use manual polling in scripts, CI pipelines, or after recovering from a bridge crash.

## Task lifecycle

```
submitted → working → completed
                    → failed
                    → cancelled
```

| State | Meaning |
|---|---|
| `submitted` | Server acknowledged creation; not yet executing |
| `working` | Actively executing on the server |
| `completed` | Finished successfully; result is available |
| `failed` | Finished with an error; inspect `error` field |
| `cancelled` | Explicitly cancelled via `tasks-cancel` |

`submitted` and `working` are transient. Scripts should loop until `completed`, `failed`, or `cancelled` is observed.

## Task management commands

```bash
# List all active tasks in the current session
mcpc @session tasks-list

# Same as above, machine-readable
mcpc --json @session tasks-list

# Check status of a specific task (human-readable)
mcpc @session tasks-get <taskId>

# Check status of a specific task (JSON — use in scripts)
mcpc --json @session tasks-get <taskId>

# Cancel a running task
mcpc @session tasks-cancel <taskId>
```

JSON response from `tasks-get` while running:

```json
{
  "taskId": "task_abc123",
  "status": "working",
  "progress": { "percentage": 42, "message": "Processing batch 3 of 7" }
}
```

JSON response from `tasks-get` after completion:

```json
{
  "taskId": "task_abc123",
  "status": "completed",
  "result": {
    "content": [
      { "type": "text", "text": "Export complete: 1,482 records written." }
    ],
    "isError": false
  }
}
```

## Crash resilience

When a task is submitted in awaited or detached mode, the bridge stores the `capturedTaskId` inside the session's `activeTasks` entry in `~/.mcpc/sessions.json`. This entry persists across bridge restarts.

If the bridge process crashes while a task is in flight:

1. `consolidateSessions()` runs at the next CLI invocation and detects the crashed bridge
2. The bridge is restarted automatically
3. Instead of re-invoking the tool (which would duplicate the operation), the bridge resumes by calling `pollTask()` with the stored task ID
4. The task's server-side execution is unaffected — it was running independently the whole time

This prevents duplicate execution of expensive or non-idempotent operations. After recovery, you can poll the task ID normally:

```bash
mcpc --json @session tasks-get <taskId>
```

## Scripting patterns

### Poll-to-completion script

Wait for a detached task to finish and extract its result:

```bash
#!/usr/bin/env bash
set -euo pipefail

SESSION="@my-session"
POLL_INTERVAL=2

# Start detached, capture task ID
TASK_ID=$(mcpc --json "$SESSION" tools-call expensive-tool arg:=value \
  --task --detach | jq -r '.taskId')

echo "Task started: $TASK_ID"

# Poll until terminal state
while true; do
    RESPONSE=$(mcpc --json "$SESSION" tasks-get "$TASK_ID")
    STATUS=$(echo "$RESPONSE" | jq -r '.status')

    case "$STATUS" in
        completed)
            echo "Done!"
            echo "$RESPONSE" | jq '.result'
            break
            ;;
        failed)
            echo "Task failed:"
            echo "$RESPONSE" | jq '.error'
            exit 1
            ;;
        cancelled)
            echo "Task was cancelled"
            exit 1
            ;;
        submitted|working)
            PROGRESS=$(echo "$RESPONSE" | jq -r '.progress.message // "in progress"')
            echo "Status: $STATUS — $PROGRESS"
            sleep "$POLL_INTERVAL"
            ;;
        *)
            echo "Unknown status: $STATUS"
            sleep "$POLL_INTERVAL"
            ;;
    esac
done
```

### Fire multiple tasks in parallel

Submit a batch of tasks concurrently, then collect results:

```bash
#!/usr/bin/env bash
set -euo pipefail

SESSION="@my-session"
QUERIES=("query1" "query2" "query3")
TASK_IDS=()

# Fan out — submit all tasks without waiting
for query in "${QUERIES[@]}"; do
    TID=$(mcpc --json "$SESSION" tools-call search query:="$query" \
        --task --detach | jq -r '.taskId')
    echo "Submitted: $TID (query: $query)"
    TASK_IDS+=("$TID")
done

echo "All tasks submitted. Polling for results..."

# Collect — poll each task until complete
for tid in "${TASK_IDS[@]}"; do
    while true; do
        RESPONSE=$(mcpc --json "$SESSION" tasks-get "$tid")
        STATUS=$(echo "$RESPONSE" | jq -r '.status')

        case "$STATUS" in
            completed)
                echo "$RESPONSE" | jq '{taskId: .taskId, status: .status, result: .result}'
                break
                ;;
            failed|cancelled)
                echo "$RESPONSE" | jq '{taskId: .taskId, status: .status}'
                break
                ;;
            *)
                sleep 2
                ;;
        esac
    done
done
```

## Limitations

- **Experimental** — the task protocol may change between mcpc releases
- **Server must declare support** — servers that do not include `capabilities.tasks` in their initialize response will ignore `--task` and `--detach` flags or return an error
- **Not all tools support tasks** — even on task-capable servers, individual tools may only support synchronous execution
- **ESC-to-detach requires TTY** — the escape key shortcut is unavailable when stdout is a pipe or file redirect
- **Task state is per-session** — task IDs are scoped to the session that created them; a different session cannot retrieve results for tasks it did not start
- **Closing a session may lose task references** — active task IDs stored in `activeTasks` are removed when a session is explicitly closed with `mcpc @session close`; the server-side task may still be running but becomes unqueryable through mcpc
