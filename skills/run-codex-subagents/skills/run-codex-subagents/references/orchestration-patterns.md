# Orchestration Patterns

8 execution patterns from simple to complex, using `cli-codex-subagent` CLI commands.

## Pattern 1: Single task (one-shot)

The simplest flow. Spawn one task, stream events, wait for completion.

```bash
cli-codex-subagent run task.md --effort low --follow --auto-approve
# → streams events in real time
# → exits 0 on success, 1 on failure, 2 if blocked
```

For fully unattended runs:
```bash
cli-codex-subagent run task.md --effort low --wait --auto-approve
echo "Exit: $?"
```

## Pattern 2: Parallel wave

Spawn N independent tasks, then wait for all of them.

```bash
# Spawn all — returns task IDs immediately
TASK_A=$(cli-codex-subagent run auth.md    --effort low --label wave-1 --json | python3 -c "import sys,json; print(json.load(sys.stdin)['taskId'])")
TASK_B=$(cli-codex-subagent run billing.md --effort low --label wave-1 --json | python3 -c "import sys,json; print(json.load(sys.stdin)['taskId'])")
TASK_C=$(cli-codex-subagent run notify.md  --effort low --label wave-1 --json | python3 -c "import sys,json; print(json.load(sys.stdin)['taskId'])")

# Monitor all three simultaneously in separate terminal panes, or serially:
cli-codex-subagent task wait "$TASK_A"
cli-codex-subagent task wait "$TASK_B"
cli-codex-subagent task wait "$TASK_C"

# Check results
cli-codex-subagent task list --label wave-1
```

**Risk:** All parallel tasks share one Codex process. If one triggers a crash, all siblings die at the same millisecond. Design for this:
- Don't batch your most critical task with experimental ones
- Completed tasks survive (results captured before exit)
- Check `task list --status failed` for casualties

## Pattern 3: Sequential chain

Wave N must complete before Wave N+1 starts.

```bash
# Wave 1: schema
cli-codex-subagent run schema.md --effort low --wait --label wave-1

# Wave 2: depends on schema (two tasks in parallel)
TASK_MIG=$(cli-codex-subagent run migration.md --effort low --label wave-2 --json | python3 -c "import sys,json; print(json.load(sys.stdin)['taskId'])")
TASK_TYP=$(cli-codex-subagent run types.md     --effort low --label wave-2 --json | python3 -c "import sys,json; print(json.load(sys.stdin)['taskId'])")
cli-codex-subagent task wait "$TASK_MIG"
cli-codex-subagent task wait "$TASK_TYP"

# Wave 3: validation
cli-codex-subagent run validate.md --effort low --wait --label wave-3
```

## Pattern 4: Continuation (steer after completion)

When a completed task needs follow-up work, use `task steer` to continue in the same session. The agent retains all prior context.

```bash
# Step 1: initial task
cli-codex-subagent run auth.md --effort medium --wait
# → tsk_abc123 completed

# Step 2: follow-up in same session (agent remembers the auth module)
cli-codex-subagent task steer tsk_abc123 rate-limiting.md --follow --effort low
```

Note: `task steer` requires the prior task to be in a terminal state. To span multiple follow-ups:

```bash
TASK1=$(cli-codex-subagent run step1.md --json | python3 -c "import sys,json; print(json.load(sys.stdin)['taskId'])")
cli-codex-subagent task wait "$TASK1"

TASK2=$(cli-codex-subagent task steer "$TASK1" step2.md --json | python3 -c "import sys,json; print(json.load(sys.stdin)['taskId'])")
cli-codex-subagent task wait "$TASK2"

cli-codex-subagent task steer "$TASK2" step3.md --follow
```

## Pattern 5: Continuation without session (new task in same cwd)

When you don't need to preserve session context, simply spawn a new task in the same working directory. The new task sees all files the previous task created.

```bash
# Task 1 creates the auth module
cli-codex-subagent run create-auth.md --effort medium --wait

# Task 2 reads the auth module and adds rate limiting
# Uses the same cwd, sees auth module files
cli-codex-subagent run add-rate-limiting.md --effort low --follow
```

## Pattern 6: Diagnostic then fix (branch point)

Run a diagnostic task first, then decide what to do based on output.

```bash
# Phase 1: diagnose
cli-codex-subagent run diagnose.md --effort low --wait
# diagnose.md: "Run 'npm run build 2>&1' and report: exit code, error count, first 5 errors with file:line"

# Read diagnostic output
cli-codex-subagent task read tsk_diag123 | tail -20

# Phase 2: branch based on output
# If 0 errors: done
# If < 5 errors: targeted fix
cli-codex-subagent run fix-specific.md --effort low --follow
# If 5+ errors: broad fix
cli-codex-subagent run fix-broad.md --effort medium --follow
```

`fix-specific.md` should paste the exact errors from the diagnostic output.

## Pattern 7: Retry with lower effort

When a task fails due to process exit (reasoning burned too many tokens), retry at lower effort with a more specific prompt.

```bash
# First attempt at medium
cli-codex-subagent run refactor.md --effort medium --wait   # → exit 1 (process exit)

# Check what was done
git status   # agent may have partially completed

# Retry at low with narrower scope
cli-codex-subagent run refactor-narrow.md --effort low --follow
# refactor-narrow.md: exact file names, exact line ranges, minimal scope
```

Key insight: the retry prompt is more specific (exact file, exact line range). That's why `low` succeeds where `medium` failed.

## Pattern 8: Partial work recovery

When a task fails but left work on disk, salvage it instead of retrying from scratch.

```bash
# Original task failed
cli-codex-subagent run create-controllers.md --effort medium --wait   # → exit 1

# Step 1: check what exists
git status

# Found: 3 of 5 controllers created, 2 compile cleanly

# Step 2: fix what's broken (targeted)
cli-codex-subagent run fix-import.md --effort low --follow
# fix-import.md: "TimerPopupController.swift has a missing import 'Combine'. Add it. Don't modify anything else."

# Step 3: create what's missing
cli-codex-subagent run create-remaining.md --effort low --follow
# create-remaining.md: "Create 2 remaining controllers: NotchGestureRouter.swift and NotchWindowCoordinator.swift. Follow the same pattern as the 3 existing ones."
```

## Anti-patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Waiting between parallel spawns | Tasks run sequentially | Spawn ALL before waiting |
| Spawning > 8 tasks in one wave | Resource exhaustion, shared-process risk | Cap at 5-8 per wave |
| No `task list` checks between waves | Blind to failures | Check after each wave |
| Using `task steer` on a running task | Returns error | Wait for completion first |
| High effort on simple tasks | Reasoning burns budget; execution never starts | Use `low` unless explicitly needed |
| Not using `--auto-approve` for batch work | Manual approvals break unattended runs | Add `--auto-approve` for autonomous tasks |
| Re-running from scratch on every failure | Discards 80%+ completed work | Always check `git status` first |
| Higher effort on retry | Burns more tokens → worse outcome | Lower effort + narrower prompt |
