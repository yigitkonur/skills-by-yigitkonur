# Tracking Waves Without Labels

The old worker CLI had label flags. `codex-worker` does not. Track work explicitly instead of relying on in-band labels.

## Recommended Tracking Primitives

- prompt filenames such as `wave-1-auth.md`, `wave-2-tests.md`
- JSON manifests that store `threadId`, `turnId`, and `job.id`
- `thread list --cwd /abs/project` to scope threads to one workspace

## Minimal Manifest Pattern

```bash
RESULT=$(codex-worker --output json run wave-1-auth.md --async)
printf '%s\n' "$RESULT" > .codex-wave-1-auth.json
```

Later:

```bash
jq '{threadId, turnId, jobId: .job.id}' .codex-wave-1-auth.json
```

## Naming Convention

Use prompt filenames that encode both wave and domain:
- `wave-1-auth.md`
- `wave-1-api.md`
- `wave-2-integration.md`

That makes shell history, manifests, and thread reads easy to correlate.
