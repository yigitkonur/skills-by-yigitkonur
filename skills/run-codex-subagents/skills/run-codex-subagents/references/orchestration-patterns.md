# Orchestration patterns

Use this file when you already know the task shape and need a reliable CLI execution loop.

Assume `jq` is available when examples capture ids from JSON. If it is not, use any equivalent JSON parser.

## 1. One-shot blocking execution

Use this when you want one command that starts the task and waits for the final result:

```bash
codex-worker run task.md
```

With live streaming:

```bash
codex-worker run task.md --follow --compact
```

Best for:

- narrow implementation tasks
- verification tasks
- quick research tasks with a single output

## 2. Async start, then follow

Use this when you want ids immediately and will monitor later:

```bash
START_JSON="$(codex-worker --output json run task.md --async)"
THREAD_ID="$(printf '%s' "$START_JSON" | jq -r '.threadId')"

codex-worker task follow "$THREAD_ID" --compact
```

If you only want the final state later:

```bash
codex-worker task wait "$THREAD_ID"
```

## 3. Session continuity

Use a session when multiple turns should share the same runtime thread, cwd, and evolving context:

```bash
# Start first task
START_JSON="$(codex-worker --output json run prompts/step-1.md --async)"
THREAD_ID="$(printf '%s' "$START_JSON" | jq -r '.threadId')"

codex-worker task wait "$THREAD_ID"

# Continue in same session
codex-worker task steer "$THREAD_ID" prompts/step-2.md --follow --compact
```

Or use `--session` on `run` or `task start`:

```bash
codex-worker task start prompts/step-2.md --session "$THREAD_ID" --follow --compact
```

Do not reuse a session casually across unrelated tasks.

## 4. Multi-wave parallel work

Parallel tasks should not share one active session. Start them independently.

Wave launch:

```bash
IDS=()
for file in prompts/wave-1/*.md; do
  START_JSON="$(codex-worker --output json run "$file" --async --label wave-1)"
  IDS+=("$(printf '%s' "$START_JSON" | jq -r '.threadId')")
done
```

Wave monitor:

```bash
for id in "${IDS[@]}"; do
  codex-worker task wait "$id" || true
done

codex-worker --output json task list --status failed
```

Only start the next wave after checking for failures.

## 5. Blocked-request loop

When a task stops in `waiting_request`:

```bash
codex-worker request list --status pending
codex-worker request read req_123
codex-worker request answer req_123 --decision accept
codex-worker task follow thr_abc123 --compact
```

Treat this as normal control flow, not an exceptional state.

## 6. Recovery before retry

If a task fails:

```bash
codex-worker task read thr_abc123 --tail 40
codex-worker task events thr_abc123 --tail 100
codex-worker doctor
```

Decide whether to:

- answer a request
- tighten the prompt and rerun
- use `task steer` with a focused follow-up
- restart cleanly

## Anti-patterns

| Avoid | Why |
|---|---|
| sharing one active session across parallel tasks | the CLI protects active sessions and you lose clean isolation |
| retrying immediately after failure | you throw away diagnostics |
| using `task steer` on a still-running task | it is rejected by design |
| parsing text output in scripts | `--output json`, `--field`, and `--quiet` are the stable contract |
