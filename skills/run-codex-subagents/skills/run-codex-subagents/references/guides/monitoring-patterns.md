# Monitoring Patterns

Use the current primitives together:
- foreground streaming from blocking commands
- `wait` for background turns
- `read` for structured state
- `logs` for readable output

## Foreground Monitoring

```bash
codex-worker run task.md
```

If stdout is a TTY, you will see `[event] payload` lines until the turn completes, fails, or blocks.

## Background Monitoring

```bash
RUN_JSON=$(codex-worker --output json run task.md --async)
THREAD_ID=$(printf '%s' "$RUN_JSON" | jq -r '.threadId')
JOB_ID=$(printf '%s' "$RUN_JSON" | jq -r '.job.id')

codex-worker wait --job-id "$JOB_ID"
codex-worker read "$THREAD_ID"
codex-worker logs "$THREAD_ID"
```

## Tail The Stored Artifacts

```bash
LOG_PATH=$(codex-worker --output json read <thread-id> | jq -r '.artifacts.logPath')
TRANSCRIPT_PATH=$(codex-worker --output json read <thread-id> | jq -r '.artifacts.transcriptPath')

tail -f "$LOG_PATH"
tail -f "$TRANSCRIPT_PATH"
```

## Triage Checklist

- `wait` if you want to block until the current turn stops changing
- `read` if you need turns, requests, and artifact paths
- `logs` if you only need the readable tail
- direct file tails if the CLI summary is not enough
