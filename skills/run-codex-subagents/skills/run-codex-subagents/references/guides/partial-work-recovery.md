# Partial Work Recovery

A failed thread may still have written useful files. Recover that work before retrying from scratch.

## Recovery Sequence

```bash
codex-worker read <thread-id>

# How far did the failed turn get before dying? The raw log's mtime is the
# last activity timestamp; the line count is a proxy for progress.
RAW=$(codex-worker --output json read <thread-id> | jq -r '.artifacts.rawLogPath')
stat -f %Sm "$RAW"
wc -l "$RAW"

# Find the cause of death (see guides/failure-diagnosis.md):
jq -c 'select(.dir=="daemon" or .dir=="exit" or .method=="error")' "$RAW"

git status
npm run build
npm test
```

## Decision Rules

### Files are correct or nearly correct

Keep the same thread and narrow the next prompt:

```bash
codex-worker send <thread-id> fix-only.md
```

### Files are wrong but the analysis was useful

Create a fresh prompt that points to the partially written files as context, but decide whether to continue the same thread or start a new one based on how much bad context accumulated.

### Nothing useful was written

Start over with a sharper prompt file.

## Good Recovery Prompt Shape

```markdown
## Context

The previous turn created `src/auth.ts` and `src/session.ts` but `npm test`
still fails in `AuthGuard`.

## Mission

Fix only the failing import and type mismatch.

## Constraints

- Do not touch billing or routing files.
- Modify only `src/auth.ts` and `src/session.ts`.
```
