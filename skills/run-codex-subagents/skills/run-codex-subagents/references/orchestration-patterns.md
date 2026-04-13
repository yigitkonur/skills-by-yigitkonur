# Orchestration patterns

Use this file when you already know the task shape and need a reliable CLI execution loop.

Assume `jq` is available when examples capture ids from JSON. If it is not, use any equivalent JSON parser.

## 1. One-shot blocking execution

Use this when you want one command that starts the task and waits for the final result:

```bash
cli-codex-subagent run task.md --wait --json
```

Best for:

- narrow implementation tasks
- verification tasks
- quick research tasks with a single output

## 2. Async start, then follow

Use this when you want ids immediately and will monitor later:

```bash
START_JSON="$(cli-codex-subagent task start task.md --json)"
TASK_ID="$(printf '%s' "$START_JSON" | jq -r '.task_id')"

cli-codex-subagent task follow "$TASK_ID"
```

If you only want the final state later:

```bash
cli-codex-subagent task wait "$TASK_ID" --json
```

## 3. Pre-create a session for continuity

Use a session when multiple turns should share the same runtime thread, cwd, and evolving context:

```bash
SESSION_JSON="$(cli-codex-subagent session create --cwd /repo --model gpt-5.4 --json)"
SESSION_ID="$(printf '%s' "$SESSION_JSON" | jq -r '.session_id')"

STEP1_JSON="$(cli-codex-subagent task start prompts/step-1.md --session "$SESSION_ID" --wait --json)"
TASK1_ID="$(printf '%s' "$STEP1_JSON" | jq -r '.task_id')"

cli-codex-subagent task steer "$TASK1_ID" prompts/step-2.md --follow
```

Do not reuse a session casually across unrelated tasks.

## 4. Multi-wave parallel work

Parallel tasks should not share one active session. Start them without `--session`, or pre-create separate sessions.

Wave launch:

```bash
IDS=()
for file in prompts/wave-1/*.md; do
  START_JSON="$(cli-codex-subagent task start "$file" --label wave-1 --json)"
  IDS+=("$(printf '%s' "$START_JSON" | jq -r '.task_id')")
done
```

Wave monitor:

```bash
for id in "${IDS[@]}"; do
  cli-codex-subagent task wait "$id" --json || true
done

cli-codex-subagent task list --label wave-1 --json
cli-codex-subagent task list --label wave-1 --status failed --json
```

Only start the next wave after checking for failures.

## 5. Blocked-request loop

When a task stops in `waiting_request`:

```bash
cli-codex-subagent request list --status pending --json
cli-codex-subagent request read req_123 --json
cli-codex-subagent request answer req_123 --choice 1
cli-codex-subagent task follow tsk_123
```

Treat this as normal control flow, not an exceptional state.

## 6. Portable handoff to another agent

Before execution:

```bash
cli-codex-subagent prompt inspect task.md --write-bundle ./handoff/task --json
```

After execution:

```bash
cli-codex-subagent task read tsk_123 --field artifacts.handoffManifestPath --json
```

Use the bundle when another agent should continue from the exact resolved prompt and context.

## 7. Recovery before retry

If a task fails:

```bash
cli-codex-subagent task read tsk_123 --tail 40 --json
cli-codex-subagent task events tsk_123 --tail 100 --json
cli-codex-subagent doctor --json
```

Decide whether to:

- answer a request
- tighten the prompt and rerun
- use `task steer` with a focused follow-up
- hand the work to another agent with the bundle artifacts

## Anti-patterns

| Avoid | Why |
|---|---|
| sharing one active session across parallel tasks | the CLI protects active sessions and you lose clean isolation |
| retrying immediately after failure | you throw away the rendered prompt and diagnostics |
| using `task steer` on a still-running task | it is rejected by design |
| scraping human text output in scripts | `--json`, `--stream-json`, `--field`, and `--quiet` are the stable contract |
