# Batch Wave Launcher

Use this shell pattern to launch several Markdown prompts in parallel and keep a manifest for each thread.

```bash
#!/usr/bin/env bash
set -euo pipefail

mkdir -p .codex-wave

for prompt in wave-1-auth.md wave-1-api.md wave-1-tests.md; do
  name=$(basename "$prompt" .md)
  codex-worker --output json run "$prompt" --async > ".codex-wave/$name.json"
done

for manifest in .codex-wave/*.json; do
  job_id=$(jq -r '.job.id' "$manifest")
  codex-worker wait --job-id "$job_id" || true
done

for manifest in .codex-wave/*.json; do
  thread_id=$(jq -r '.threadId' "$manifest")
  codex-worker read "$thread_id"
done
```

## Manifest Fields To Keep

- `.threadId`
- `.turnId`
- `.job.id`
- `.status`

## When To Use

- one wave of independent prompts
- same repo, separate domains
- no dependency between the prompts until after all waits finish
