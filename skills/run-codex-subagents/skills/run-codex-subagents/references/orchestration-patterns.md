# Orchestration Patterns

8 execution patterns from simple to complex, each with spawn/wait/monitor code.

## Pattern 1: Single task

The simplest flow. Spawn one task, monitor it, wait for completion.

```
id = spawn-task({ prompt: "Create src/utils/slugify.ts ...", cwd: "/project", reasoning: "gpt-5.4(low)" })

Monitor({ command: "tail -f ~/.mcp-codex-worker/tasks/{id}/timeline.log", timeout_ms: 120000 })

result = wait-task({ task_id: id, timeout_ms: 120000 })
→ status: "completed", output: [...]
```

## Pattern 2: Parallel wave

Spawn N independent tasks in a single message. They run concurrently on the shared Codex process.

```
# Spawn all in ONE message — do NOT wait between spawns
id1 = spawn-task({ prompt: "Write auth module", cwd: "/project", labels: ["wave-1"] })
id2 = spawn-task({ prompt: "Write billing module", cwd: "/project", labels: ["wave-1"] })
id3 = spawn-task({ prompt: "Write notification module", cwd: "/project", labels: ["wave-1"] })

# Merged monitor — all three timelines interleaved
Monitor({
  command: "for id in {id1} {id2} {id3}; do tail -f ~/.mcp-codex-worker/tasks/$id/timeline.log | sed --unbuffered \"s/^/[$id] /\" & done; wait",
  description: "Wave 1 parallel tasks",
  timeout_ms: 300000
})

# Collect — wait for each
r1 = wait-task({ task_id: id1, timeout_ms: 120000 })
r2 = wait-task({ task_id: id2, timeout_ms: 120000 })
r3 = wait-task({ task_id: id3, timeout_ms: 120000 })
```

**Risk:** All parallel tasks share one Codex process. If one triggers an exit, all siblings die at the same millisecond. Design for this:
- Don't batch your most critical task with experimental ones
- Completed tasks survive (results captured before exit)
- Check scoreboard for same-timestamp EXIT events

## Pattern 3: Sequential chain with depends_on

Tasks execute in dependency order. Each waits for its predecessors.

```
id1 = spawn-task({ prompt: "Create database schema in schema.prisma", cwd: "/project" })
id2 = spawn-task({ prompt: "Read schema.prisma, generate migration.sql", cwd: "/project", depends_on: [id1] })
id3 = spawn-task({ prompt: "Read schema.prisma, generate types.ts", cwd: "/project", depends_on: [id1] })

# id2 and id3 both depend on id1, so they run in parallel after id1 completes
# Monitor all three
Monitor({ command: "tail -f ~/.mcp-codex-worker/tasks/{id1}/timeline.log", timeout_ms: 60000 })

wait-task({ task_id: id1, timeout_ms: 60000 })
# id2 and id3 start automatically

Monitor({
  command: "for id in {id2} {id3}; do tail -f ~/.mcp-codex-worker/tasks/$id/timeline.log | sed --unbuffered \"s/^/[$id] /\" & done; wait",
  timeout_ms: 120000
})

wait-task({ task_id: id2, timeout_ms: 120000 })
wait-task({ task_id: id3, timeout_ms: 120000 })
```

## Pattern 4: Continuation after completion

When a completed task needs follow-up work, spawn a new task in the same `cwd`. The new task sees all files the previous task created.

```
id1 = spawn-task({ prompt: "Create the auth module", cwd: "/project" })
wait-task({ task_id: id1, timeout_ms: 120000 }) → completed

# Continuation — new task, same cwd, sees auth module files
id2 = spawn-task({ prompt: "Read auth module created in previous step. Add rate limiting middleware.", cwd: "/project" })
wait-task({ task_id: id2, timeout_ms: 120000 }) → completed
```

Note: `message-task` also sends follow-ups on the same session, but only works on active tasks. For terminal tasks, use this continuation pattern.

## Pattern 5: Mid-flight steer via message-task

Redirect a running task without cancelling it.

```
id = spawn-task({ prompt: "Refactor the auth module to use JWT", cwd: "/project", reasoning: "gpt-5.4(medium)" })

Monitor({ command: "tail -f ~/.mcp-codex-worker/tasks/{id}/timeline.log", timeout_ms: 300000 })

# After seeing timeline output, realize we need a different approach
message-task({ task_id: id, message: "Change: use session tokens instead of JWT. Keep the same file structure." })

# Continue monitoring — the agent receives the message and adjusts
wait-task({ task_id: id, timeout_ms: 120000 }) → completed
```

You can also override reasoning for the follow-up turn:
```
message-task({ task_id: id, message: "Complex follow-up...", reasoning: "gpt-5.4(high)" })
```

## Pattern 6: Diagnostic then fix (branch point)

Run a diagnostic task first, then decide what to do based on its output.

```
# Phase 1: Diagnose
diag = spawn-task({
  prompt: "Run 'swift build 2>&1' and report: (1) exit code, (2) error count, (3) first 5 errors with file:line",
  cwd: "/project",
  reasoning: "gpt-5.4(low)",
  task_type: "tester"
})
wait-task({ task_id: diag, timeout_ms: 60000 })

# Phase 2: Branch based on output
if diag.output shows 0 errors:
  → done, no fix needed

if diag.output shows < 5 errors:
  fix = spawn-task({ prompt: "Fix these specific errors: {paste errors from diag.output}", cwd: "/project", reasoning: "gpt-5.4(low)" })
  wait-task({ task_id: fix, timeout_ms: 120000 })

if diag.output shows 5+ errors:
  fix = spawn-task({ prompt: "Fix build errors. Start with {first error}. Run 'swift build' after each fix.", cwd: "/project", reasoning: "gpt-5.4(medium)" })
  wait-task({ task_id: fix, timeout_ms: 300000 })
```

## Pattern 7: Retry with lower reasoning

When a task fails due to process exit (reasoning burned too many tokens), retry at a lower level with a better prompt.

```
# First attempt at medium
id1 = spawn-task({ prompt: "Refactor ContentView.swift", cwd: "/project", reasoning: "gpt-5.4(medium)" })
wait-task({ task_id: id1, timeout_ms: 120000 }) → failed (process exit)

# Check what was done
# git status, ls the cwd — the agent may have partially completed

# Retry at low with more specific prompt
id2 = spawn-task({
  prompt: "In ContentView.swift, extract lines 200-350 (the gesture handling block) into NotchGestureRouter.swift. Import it back. Do not change any other code.",
  cwd: "/project",
  reasoning: "gpt-5.4(low)"
})
wait-task({ task_id: id2, timeout_ms: 120000 }) → completed
```

Key insight: the retry prompt is more specific (exact line range, exact file names), which is why `low` succeeds where `medium` failed.

## Pattern 8: Partial work recovery

When a task fails but left work on disk, salvage it instead of retrying from scratch.

```
id = spawn-task({ prompt: "Create 5 new controller files from ContentView.swift", cwd: "/project", reasoning: "gpt-5.4(medium)" })
wait-task({ task_id: id, timeout_ms: 120000 }) → failed

# Step 1: Check what exists
# Run: git status, ls, swift build
# Found: 3 of 5 controllers created, 2 compile

# Step 2: Fix what's broken
fix = spawn-task({
  prompt: "TimerPopupController.swift exists but has a missing import. Add 'import Combine'. Do not modify anything else.",
  cwd: "/project",
  reasoning: "gpt-5.4(low)"
})
wait-task({ task_id: fix, timeout_ms: 60000 }) → completed

# Step 3: Create what's missing
remaining = spawn-task({
  prompt: "Create the remaining 2 controllers: NotchGestureRouter.swift and NotchWindowCoordinator.swift. Follow the same pattern as the existing 3.",
  cwd: "/project",
  reasoning: "gpt-5.4(low)"
})
wait-task({ task_id: remaining, timeout_ms: 120000 }) → completed
```

## Anti-patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Waiting between parallel spawns | Tasks run sequentially | Spawn ALL in one message, then wait |
| Spawning > 8 tasks in one wave | Resource exhaustion, shared-process risk | Cap at 5-8 per wave |
| No scoreboard checks between waves | Blind to failures | Read `task:///all` after each wave |
| Hardcoded task IDs | IDs are random | Always capture from spawn response |
| Ignoring `poll_frequency` | Polling too fast or too slow | Use the returned value |
| No cleanup after failures | Orphaned running tasks | Batch cancel remaining tasks |
| Using message-task on terminal tasks | Rejected with error | Spawn a new task in same cwd |
| Raising reasoning after failure | Makes it worse (burns more tokens) | Lower reasoning + better prompt |
