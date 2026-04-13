# Parallel Dispatch

Parallelism now means multiple async threads, each with its own `threadId`, `turnId`, and `job.id`.

## Simple Three-Thread Wave

```bash
for prompt in auth api tests; do
  json=$(codex-worker --output json run "wave-1-$prompt.md" --async)
  printf '%s\n' "$json" > ".codex-$prompt.json"
done
```

Wait on each job:

```bash
for f in .codex-*.json; do
  job_id=$(jq -r '.job.id' "$f")
  codex-worker wait --job-id "$job_id"
done
```

Read every thread afterward:

```bash
for f in .codex-*.json; do
  thread_id=$(jq -r '.threadId' "$f")
  codex-worker read "$thread_id"
done
```

## Operational Rules

- Keep one manifest file per spawned thread.
- Use distinct prompt files per unit of work.
- Prefer separate threads for independent domains.
- Use `send` or `turn steer` only after you have inspected the prior result.
