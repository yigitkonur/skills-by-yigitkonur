# Batch Wave Template

Template for dispatching parallel waves of tasks with monitoring, inter-wave checks, and scoreboard tracking.

## Template: Single Wave

### Spawn phase — all tasks in one message

```
spawn-task: {
  prompt: "{task 1 mission}",
  cwd: "{project_root}",
  task_type: "coder",
  reasoning: "gpt-5.4(low)",
  labels: ["wave-1", "{domain-1}"],
  timeout_ms: 120000
}
→ task-id-1

spawn-task: {
  prompt: "{task 2 mission}",
  cwd: "{project_root}",
  task_type: "coder",
  reasoning: "gpt-5.4(low)",
  labels: ["wave-1", "{domain-2}"],
  timeout_ms: 120000
}
→ task-id-2

spawn-task: {
  prompt: "{task 3 mission}",
  cwd: "{project_root}",
  task_type: "coder",
  reasoning: "gpt-5.4(low)",
  labels: ["wave-1", "{domain-3}"],
  timeout_ms: 120000
}
→ task-id-3
```

### Monitor phase — merged timeline stream

```
Monitor({
  command: "for id in {task-id-1} {task-id-2} {task-id-3}; do tail -f ~/.mcp-codex-worker/tasks/$id/timeline.log | sed --unbuffered 's/^/['$id'] /' & done; wait",
  description: "Wave 1 parallel tasks",
  timeout_ms: 180000,
  persistent: false
})
```

### Collect phase — wait for each

```
wait-task: { task_id: "task-id-1", timeout_ms: 120000 }
wait-task: { task_id: "task-id-2", timeout_ms: 120000 }
wait-task: { task_id: "task-id-3", timeout_ms: 120000 }
```

### Verify phase — check scoreboard

```
read resource: task:///all

Expected output:
[done] task-id-1 [wave-1,domain-1] -- "task 1 mission..."
[done] task-id-2 [wave-1,domain-2] -- "task 2 mission..."
[done] task-id-3 [wave-1,domain-3] -- "task 3 mission..."
```

## Template: Multi-Wave Execution

### Wave 1: Foundation (no dependencies)

```
# Spawn all Wave 1 tasks
spawn-task: { ..., labels: ["wave-1", "types"] }     → w1-a
spawn-task: { ..., labels: ["wave-1", "config"] }    → w1-b
spawn-task: { ..., labels: ["wave-1", "utils"] }     → w1-c

# Monitor
Monitor({ command: "merged tail for w1-a, w1-b, w1-c", ... })

# Wait
wait-task: w1-a → completed
wait-task: w1-b → completed
wait-task: w1-c → completed

# Scoreboard check
read resource: task:///all
→ All wave-1 tasks [done]? Yes → proceed to Wave 2
```

### Subsequent waves

Repeat the spawn/monitor/wait/scoreboard pattern for each wave. Between waves, optionally spawn a quick verification task (e.g., "check files exist") before proceeding. Read `task:///all` after each wave to confirm all tasks show `[done]`.

## Handling Failures Mid-Wave

```
# Wave 1 results:
wait-task: w1-a → completed
wait-task: w1-b → failed       ← failure
wait-task: w1-c → completed

# Recovery:
# 1. Check partial work from w1-b
git status / ls in cwd → files partially created?

# 2. If partial work exists and is usable:
#    Fix manually or spawn a targeted fix task

# 3. If no usable work:
#    Retry with adjusted prompt
spawn-task: { prompt: "{adjusted mission}", labels: ["wave-1", "retry"] }
wait-task → completed

# 4. Verify all Wave 1 work is now complete before proceeding
read resource: task:///all
→ All wave-1 [done]? Yes → proceed to Wave 2
```

## Rules

1. **Spawn all tasks in a wave in one message.** Don't wait between spawns.
2. **Always label by wave.** `["wave-N", ...]` on every task.
3. **Always set up a merged Monitor** after spawning a wave.
4. **Check scoreboard between waves.** Don't start Wave N+1 until Wave N is all [done].
5. **Limit parallel tasks to 5-8 per wave.** More risks API limits and shared-process instability.
6. **Handle failures before proceeding.** One failed task in Wave 1 can cascade to Wave 2.
7. **Inter-wave verification is optional but recommended** for multi-wave plans where later waves depend on earlier outputs.
