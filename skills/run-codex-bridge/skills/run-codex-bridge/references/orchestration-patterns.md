# Orchestration patterns

Use this file when you already know the task shape and need a reliable CLI loop.

## 1. One-shot blocking execution

```bash
codex-worker run task.md
```

Best for:
- narrow implementation tasks
- quick research tasks
- verification tasks with a single output

## 2. Async launch, then wait/read/logs

```bash
START_JSON="$(codex-worker --output json run task.md --async)"
THREAD_ID="$(printf '%s' "$START_JSON" | jq -r '.threadId')"

codex-worker wait --thread-id "$THREAD_ID" --timeout 300000
codex-worker read "$THREAD_ID" --tail 50
codex-worker logs "$THREAD_ID" --tail 100
```

## 3. Continue an existing thread

Friendly continuation:

```bash
codex-worker send "$THREAD_ID" followup.md
```

Protocol-first continuation:

```bash
TURN_ID="$(codex-worker --output json read "$THREAD_ID" | jq -r '.turns[0].id')"
codex-worker turn steer "$THREAD_ID" "$TURN_ID" followup.md
```

## 4. Multi-wave parallel work

```bash
> state/threads.tsv
for file in prompts/wave-1/*.md; do
  start_json="$(codex-worker --output json run "$file" --async)"
  thread_id="$(printf '%s' "$start_json" | jq -r '.threadId')"
  printf '%s\t%s\n' "$file" "$thread_id" >> state/threads.tsv
done
```

Wait on the wave:

```bash
while IFS=$'\t' read -r file thread_id; do
  codex-worker wait --thread-id "$thread_id" --timeout 300000 || true
done < state/threads.tsv
```

Check failures:

```bash
references/scripts/batch-status.sh --status failed --cwd "$PWD"
```

## 5. Blocked request loop

```bash
codex-worker request list --status pending
codex-worker request read <request-id>
codex-worker request respond <request-id> --decision accept
codex-worker wait --thread-id <thread-id> --timeout 300000
```

## 6. Recovery before retry

```bash
codex-worker read <thread-id> --tail 50
codex-worker logs <thread-id> --tail 100
codex-worker doctor
```

Then choose one action:
- answer the pending request
- send a tighter follow-up prompt
- use `turn steer`
- restart cleanly

## Anti-patterns

| Avoid | Why |
|---|---|
| documenting or using `task` / `session` helper commands | they do not exist in the released CLI |
| retrying immediately after failure | you throw away diagnostics |
| parsing human output in scripts | the JSON contract already exists |
