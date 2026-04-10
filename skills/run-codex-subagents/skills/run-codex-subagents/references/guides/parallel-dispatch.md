# Parallel Dispatch: Wave Execution and Shared-Process Risks

Spawning multiple Codex agents in parallel is the primary throughput lever. It's also the primary failure mode. Understand the shared-process model before dispatching anything.

## The Shared-Process Model

All tasks spawned from one MCP session share a SINGLE Codex process. This is not one process per task — it is one process for all tasks. Consequences:

1. If the process exits, ALL running tasks die at the same millisecond
2. Task isolation is logical, not physical
3. A crash in task A kills task B, C, D even if they were healthy
4. Completed tasks survive — only running tasks are affected

This was confirmed empirically: two tasks spawned in parallel both showed EXIT at timestamp `2026-04-10T17:05:25.846Z`. Same millisecond. Not coincidence — shared process death.

## Evidence of Shared-Process Death

When you see this pattern in your monitoring, it's shared-process death:

```
[task-abc] EXIT code=0 signal=null  @ 2026-04-10T17:05:25.846Z
[task-def] EXIT code=0 signal=null  @ 2026-04-10T17:05:25.846Z
[task-ghi] EXIT code=0 signal=null  @ 2026-04-10T17:05:25.846Z
```

Key indicators:
- Multiple tasks EXIT at the exact same timestamp (same second, often same millisecond)
- Exit code is 0 with null signal (clean shutdown, not a crash from the OS perspective)
- All tasks were still in RUNNING state before the exit

If tasks exit at different times, that's individual task completion or individual failures — not shared-process death.

## Wave Pattern

The safe way to do parallel work:

```
Wave 1: Spawn tasks A, B, C in one message
         ├─ Monitor all three
         ├─ Wait for all three to complete or die
         └─ Gate: check results, recover partial work
         
Wave 2: Spawn tasks D, E, F in one message
         ├─ Monitor all three
         ├─ Wait for all three
         └─ Gate: check results
         
Wave 3: ...
```

### Wave Design Rules

1. **All tasks in a wave are spawned in a single message** — This triggers parallel execution. Separate messages are sequential.

2. **Gate between waves** — Never spawn Wave 2 until Wave 1 is fully resolved (completed, recovered, or abandoned). Wave 2 may depend on Wave 1 outputs.

3. **Group by risk, not by topic** — Put reliable tasks together. Don't mix a simple rename (will complete in 20s) with a complex refactor (might trigger an approval question and kill the process).

4. **Size waves at 3-5 tasks** — More than 5 increases the chance that at least one task causes process death. Fewer than 3 underutilizes the parallelism.

5. **Keep wave tasks at the same reasoning level** — Mix of `low` and `high` means the `high` task's extended thinking time increases exposure for all tasks.

## Dispatch Mechanics

Spawn all tasks in a single tool-call batch:

```
# In one message, call spawn-task three times:
spawn-task(prompt="Extract MusicHoverController...", reasoning="low")
spawn-task(prompt="Extract TimerPopupController...", reasoning="low")  
spawn-task(prompt="Extract NotchGestureRouter...", reasoning="low")
```

Immediately after spawning, start monitoring:

```
# Merged monitor for all three
Monitor: tail -f /path/to/timeline-abc.log | sed 's/^/[music] /' &
         tail -f /path/to/timeline-def.log | sed 's/^/[timer] /' &
         tail -f /path/to/timeline-ghi.log | sed 's/^/[gesture] /'
```

Then wait:

```
wait-task(id="abc")
wait-task(id="def")
wait-task(id="ghi")
```

## What Happens When One Task Kills the Process

Scenario: You spawned tasks A, B, C. Task B triggers an approval question, the 4s timeout hits, and the process exits.

- Task A: Was mid-execution. Files on disk may be partial. Check git status.
- Task B: Was at the approval gate. Files on disk are likely complete up to that point.
- Task C: Was mid-execution. Same as A.

Recovery:
1. Check partial work for all three (see partial-work-recovery.md)
2. Recover what you can
3. Re-spawn only the tasks that need it in a new wave

## Don't Batch Critical With Experimental

Bad wave:
```
Wave 1:
  - Task A: Simple file move (will definitely complete)
  - Task B: Complex refactor with uncertain scope (might ask questions)
  - Task C: Task using unfamiliar API (might error out)
```

Task B or C dying kills Task A's easy work. Better:

```
Wave 1: Task A (simple), Task D (simple), Task E (simple)
Wave 2: Task B (complex), Task C (experimental)
```

## Merged Monitoring Command

For watching multiple parallel tasks with labeled output:

```bash
# Three-task merged monitor
tail -f /path/timeline-a.log | sed 's/^/[task-a] /' &
tail -f /path/timeline-b.log | sed 's/^/[task-b] /' &
tail -f /path/timeline-c.log | sed 's/^/[task-c] /'
```

Output looks like:
```
[task-a] STARTED
[task-b] STARTED  
[task-c] STARTED
[task-a] CMD: read ContentView.swift
[task-b] CMD: read ContentView.swift
[task-c] CMD: read ContentView.swift
[task-a] CMD: create MusicHoverController.swift
[task-b] CMD: create TimerPopupController.swift
[task-a] CMD: edit ContentView.swift
...
```

## Wave Sizing by Task Type

| Task Type               | Tasks per Wave | Reasoning |
|--------------------------|---------------|-----------|
| File moves/renames       | 5-7           | Fast, no questions, low risk |
| Pattern extractions      | 3-5           | Moderate time, predictable |
| Multi-file refactors     | 2-3           | Longer, higher risk |
| Architecture tasks       | 1-2           | High risk, long think time |
| Unknown/experimental     | 1             | Don't risk other tasks |

## Post-Wave Checklist

After every wave completes:

1. Check completion status of each task
2. For failed tasks: check partial work on disk
3. Recover what you can (usually 1-3 minute fix)
4. Commit all completed + recovered work
5. Update any tracking (status report, wave plan)
6. Design next wave based on what's left

## Real Wave Execution Example

Wave 4 of a ContentView decomposition:

```
Wave 4a: 3 tasks at low reasoning
  - Extract ClosedChinPresentation helpers → COMPLETED
  - Extract OverlayTransition helpers → COMPLETED  
  - Extract NotchWindowCoordinator → COMPLETED

Wave 4b: 2 tasks at low reasoning  
  - Extract MusicHoverController → COMPLETED
  - Extract TimerPopupController → DIED (approval timeout)
    → Partial recovery: file was complete, 1 build error, fixed in 1 edit

Wave 4c: 2 tasks at low reasoning
  - Extract NotchGestureRouter → COMPLETED
  - Extract NotchHoverStateMachine → COMPLETED
```

Total: 7 extractions in 3 waves. 1 partial recovery. Zero re-spawns from scratch. Wall-clock time: ~12 minutes for work that would take 2-3 hours manually.
