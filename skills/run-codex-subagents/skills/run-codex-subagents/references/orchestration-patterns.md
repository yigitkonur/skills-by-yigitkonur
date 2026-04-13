# Orchestration Patterns For `codex-worker`

These patterns assume the current thread/turn/request model. Replace `codex-worker` with `npx -y codex-worker` if you are not installed globally.

## Pattern 1: Single foreground run

Use this when one prompt file should run to completion before you decide anything else.

```bash
codex-worker run task.md
```

If the turn completes, inspect the result with:

```bash
codex-worker read <thread-id>
```

If it blocks, answer the request and then:

```bash
codex-worker wait --thread-id <thread-id>
```

## Pattern 2: Background wave of independent tasks

Spawn multiple threads in parallel and keep the returned ids in shell variables.

```bash
AUTH_JSON=$(codex-worker --output json run auth.md --async)
API_JSON=$(codex-worker --output json run api.md --async)
TEST_JSON=$(codex-worker --output json run tests.md --async)

AUTH_THREAD=$(printf '%s' "$AUTH_JSON" | jq -r '.threadId')
API_THREAD=$(printf '%s' "$API_JSON" | jq -r '.threadId')
TEST_THREAD=$(printf '%s' "$TEST_JSON" | jq -r '.threadId')

AUTH_JOB=$(printf '%s' "$AUTH_JSON" | jq -r '.job.id')
API_JOB=$(printf '%s' "$API_JSON" | jq -r '.job.id')
TEST_JOB=$(printf '%s' "$TEST_JSON" | jq -r '.job.id')

codex-worker wait --job-id "$AUTH_JOB"
codex-worker wait --job-id "$API_JOB"
codex-worker wait --job-id "$TEST_JOB"
```

Follow-up inspection:

```bash
codex-worker read "$AUTH_THREAD"
codex-worker read "$API_THREAD"
codex-worker read "$TEST_THREAD"
```

## Pattern 3: Explicit thread bootstrapping

Use `thread start` when you want to inject thread-level instructions before the first turn.

```bash
THREAD_JSON=$(codex-worker --output json thread start \
  --cwd "$PWD" \
  --developer-instructions "Prefer rg over grep. Keep output concise.")

THREAD_ID=$(printf '%s' "$THREAD_JSON" | jq -r '.thread.id')

TURN_JSON=$(codex-worker --output json turn start "$THREAD_ID" plan.md --async)
TURN_ID=$(printf '%s' "$TURN_JSON" | jq -r '.turnId')

codex-worker wait --turn-id "$TURN_ID"
codex-worker send "$THREAD_ID" implement.md
```

## Pattern 4: Continue from a known turn

Steer a thread after reviewing the prior result.

```bash
FIRST_JSON=$(codex-worker --output json run step1.md --async)
THREAD_ID=$(printf '%s' "$FIRST_JSON" | jq -r '.threadId')
TURN_ID=$(printf '%s' "$FIRST_JSON" | jq -r '.turnId')

codex-worker wait --turn-id "$TURN_ID"
codex-worker turn steer "$THREAD_ID" "$TURN_ID" step2.md
```

Use `turn steer` when the next prompt depends on the specific turn boundary you just reviewed. Use `send` when you only need to continue the thread.

## Pattern 5: Failure, inspect, salvage, continue

```bash
RUN_JSON=$(codex-worker --output json run repair.md --async)
THREAD_ID=$(printf '%s' "$RUN_JSON" | jq -r '.threadId')
JOB_ID=$(printf '%s' "$RUN_JSON" | jq -r '.job.id')

codex-worker wait --job-id "$JOB_ID" || true
codex-worker read "$THREAD_ID"
codex-worker logs "$THREAD_ID"

git status
npm run build
npm test
```

If the agent wrote useful partial work, keep the thread and send a narrowly scoped follow-up:

```bash
codex-worker send "$THREAD_ID" fix-only.md
```

## Pattern 6: Blocked request in the middle of a wave

```bash
THREAD_JSON=$(codex-worker --output json run feature.md --async)
THREAD_ID=$(printf '%s' "$THREAD_JSON" | jq -r '.threadId')

codex-worker request list
codex-worker request read <request-id>
codex-worker request respond <request-id> --decision accept-session
codex-worker wait --thread-id "$THREAD_ID"
```

## Pattern 7: Tracking waves without label flags

The current CLI has no `--label`. Track waves with:
- prompt filenames such as `wave-1-auth.md`, `wave-1-api.md`
- shell variables or a local TSV/JSON manifest of `threadId` and `job.id`
- `thread list --cwd /abs/project` to scope to one workspace

That keeps batch orchestration explicit and scriptable without depending on removed task-label features.
