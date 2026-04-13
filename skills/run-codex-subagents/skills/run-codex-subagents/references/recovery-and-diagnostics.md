# Recovery and diagnostics

Use this file when a task fails, is interrupted, or behaves unexpectedly.

## First response

Do this before retrying:

```bash
cli-codex-subagent task read <taskId> --tail 40 --json
cli-codex-subagent task events <taskId> --tail 100 --json
cli-codex-subagent doctor --json
```

The task may already contain:

- a good rendered prompt
- useful partial file edits
- a clear stderr failure reason
- a recoverable handoff bundle

## What `task read` gives you

`task read` is the main recovery surface. It returns:

- task status and metadata
- related session and requests
- `artifacts.*` paths
- `artifacts.timelineTail`
- `artifacts.summaryTail`
- `artifacts.stderrTail`
- suggested `actions`

Use `--field` when you only need one value:

```bash
cli-codex-subagent task read tsk_123 --field artifacts.stderrPath --json
cli-codex-subagent task read tsk_123 --field actions.steer --json
```

## Artifact files to inspect

These are the most useful recovery artifacts:

- `prompt.rendered.md`
  - exact task body plus resolved context
- `context.manifest.json`
  - which prompt and context files were loaded
- `timeline.log`
  - compact one-line event stream
- `events.jsonl`
  - normalized event log
- `summary.log`
  - short task-level status trail
- `stderr.log`
  - runtime stderr, often the best source of auth or transport failures
- `handoff.manifest.json`
  - portable re-run or delegation bundle

## Event tags

The normalized event stream uses compact tags:

- `TURN`
- `PLAN`
- `THINK`
- `MSG`
- `CMD`
- `FILE`
- `REQ`
- `TOKENS`
- `DONE`
- `FAIL`

Common readings:

- repeated `REQ` means the task is blocked, not dead
- `FAIL` plus stderr usually explains the terminal reason
- `PLAN` and `THINK` help you see where the worker changed direction
- `CMD` and `FILE` show what the worker actually touched

## Raw vs normalized events

Use normalized events first:

```bash
cli-codex-subagent task events tsk_123 --tail 80 --json
```

Use raw events only when the normalized log hides a runtime detail you need:

```bash
cli-codex-subagent task events tsk_123 --raw --tail 80 --json
```

## Recovery playbook

### Failed

1. Read `task read --tail 40 --json`
2. Inspect `stderrTail`, `summaryTail`, and `timelineTail`
3. Open `prompt.rendered.md` and `context.manifest.json`
4. Decide whether the fix is:
   - a prompt correction
   - a request answer
   - an environment/runtime issue
   - a follow-up `task steer`
   - a clean retry with better context

### Interrupted

1. Read the artifacts
2. Check whether the worker already produced useful files
3. Decide whether to:
   - resume via a fresh task from the same handoff bundle
   - `task steer` with a tighter follow-up file
   - discard and restart cleanly

### Waiting request

Switch to the request loop immediately. Do not misclassify it as a failure.

## When `doctor` matters

Use `doctor` when the failure looks environmental:

- authentication issues
- rate limits
- transport problems
- daemon readiness questions
- runtime profile/config problems

`doctor --json` is especially useful after repeated auth or websocket failures because it surfaces recent failure hints from local state.
