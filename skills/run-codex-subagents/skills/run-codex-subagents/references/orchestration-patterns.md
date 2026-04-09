# Orchestration Patterns

Patterns for running multiple Codex subagents, from simple parallel dispatch to multi-wave execution plans.

## Pattern 1: Fire-and-forget parallel

Spawn N independent tasks, wait for all. Best when tasks don't depend on each other.

```
# Spawn phase — do NOT wait between spawns
spawn-task: { prompt: "Write auth module", cwd: "/project" } → id-1
spawn-task: { prompt: "Write billing module", cwd: "/project" } → id-2
spawn-task: { prompt: "Write notification module", cwd: "/project" } → id-3

# Monitor phase — read scoreboard
read resource: task:///all
→ tasks -- 3 total (0 done, 3 busy)

# Collect phase — wait for each
wait-task: { task_id: "id-1", timeout_ms: 120000 } → completed
wait-task: { task_id: "id-2", timeout_ms: 120000 } → completed
wait-task: { task_id: "id-3", timeout_ms: 120000 } → completed
```

**When to use:** Independent modules, parallel test suites, multi-file generation.

## Pattern 2: Wave execution

Group tasks into waves. All tasks in a wave run in parallel. The next wave starts only after the previous wave completes.

```
Wave 1: Foundation (no dependencies)
  spawn: types.ts, config.ts, utils.ts
  wait all → completed

Wave 2: Core (depends on Wave 1 outputs)
  spawn: database.ts (reads types.ts), api.ts (reads config.ts)
  wait all → completed

Wave 3: Integration (depends on Waves 1+2)
  spawn: app.ts (reads database.ts + api.ts)
  wait → completed
```

**Planning a wave execution:**

1. List all tasks in the plan
2. Identify dependencies between tasks
3. Group tasks with no unmet dependencies into waves
4. Within each wave, all tasks can run in parallel
5. Between waves, verify completion before spawning the next

**Monitoring between waves:**
```
# After Wave 1 completes
read resource: task:///all
→ tasks -- 3 total (3 done)

# Start Wave 2
spawn-task: ...
spawn-task: ...
```

## Pattern 3: Sequential chain (shared filesystem)

Tasks share a `cwd` and build on each other's output. Each task reads files the previous task created.

```
Task 1: Create database schema
  spawn: { prompt: "Create schema.prisma", cwd: "/project" }
  wait → completed → schema.prisma exists

Task 2: Generate migration
  spawn: { prompt: "Read schema.prisma, generate migration.sql", cwd: "/project" }
  wait → completed → migration.sql exists

Task 3: Generate TypeScript types
  spawn: { prompt: "Read schema.prisma, generate types.ts", cwd: "/project" }
  wait → completed → types.ts exists
```

**Tasks 2 and 3 can run in parallel** since both only read schema.prisma.

## Pattern 4: Approval-aware batch

When running tasks that will need approvals (file writes, command execution), plan for the approval loop.

```
# Spawn tasks that will need approval
spawn: { prompt: "Install dependencies and set up project", cwd: "/project" }
  → wait → input_required (command_approval: "npm install")
  → respond: { type: "command_approval", decision: "accept" }
  → wait → input_required (file_approval: package.json changes)
  → respond: { type: "file_approval", decision: "accept" }
  → wait → completed
```

**Auto-approve pattern:** If you trust the agent's commands within a scope, respond with `accept` to all command_approval and file_approval requests until the task completes.

**Selective approve pattern:** Read the pending_question details before deciding:
- `command_approval` → check the `command` field
- `file_approval` → check the `fileChanges` array (paths and patches)

## Pattern 5: Retry on failure

When a task fails, read the error, adjust the prompt, and retry.

```
spawn: { prompt: "original task" } → wait → failed

# Read error
read resource: task:///{id}
→ Error: "Cannot find module 'express'"

# Retry with corrected prompt
spawn: { prompt: "First run 'npm install express', then [original task]", cwd: "/project" }
→ wait → completed
```

## Pattern 6: Long-running with checkpoints

For tasks that may take a long time, use short wait-task timeouts and check progress.

```
spawn: { prompt: "Refactor the entire src/ directory", timeout_ms: 600000 }

# Check every 30 seconds
wait: { task_id, timeout_ms: 30000 } → working (not done yet)
read resource: task:///all → [busy] refactoring...

wait: { task_id, timeout_ms: 30000 } → working (still going)
read resource: task:///{id}/log → see output progress

wait: { task_id, timeout_ms: 30000 } → completed
```

## Anti-patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Waiting between parallel spawns | Tasks run sequentially instead of parallel | Spawn ALL first, then wait |
| Spawning too many tasks at once | API rate limits, resource exhaustion | Limit to 5-8 parallel tasks per wave |
| No scoreboard checks between waves | Blind to failures until the end | Read `task:///all` after each wave |
| Hardcoded task IDs | Task IDs are random per session | Always capture from spawn response |
| Ignoring `poll_frequency` | Polling too fast or too slow | Use the returned value |
| No cleanup after failures | Orphaned running tasks | Batch cancel remaining tasks |
