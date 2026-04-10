# Labels and Tracking

Labels are string arrays attached to tasks at spawn time. They appear throughout the lifecycle and are the primary mechanism for organizing parallel work.

## Setting Labels

Pass `labels` as a string array on `spawn-task`:

```json
{
  "prompt": "Extract NotchHoverStateMachine from ContentView",
  "cwd": "/project",
  "labels": ["wave-1", "notch", "extraction"]
}
```

Labels are immutable after spawn. You cannot add or remove labels from a running task.

## Where Labels Appear

### Scoreboard (task:///all)

The scoreboard is the primary tracking view. Labels appear in brackets after the task ID:

```
tasks -- 6 total (3 done, 2 busy, 1 fail)

[done]    bold-falcon-42   [wave-1,notch]      -- "Extract NotchHoverStateMachine..."
[done]    calm-river-17    [wave-1,music]      -- "Extract MusicHoverController..."
[done]    dark-mesa-09     [wave-1,gesture]    -- "Extract NotchGestureRouter..."
[busy]    easy-wind-33     [wave-2,notch]      -- "Wire NotchHoverStateMachine into..."
[busy]    free-lake-21     [wave-2,music]      -- "Wire MusicHoverController into..."
[fail]    gray-peak-55     [wave-2,gesture]    -- "Wire NotchGestureRouter into..."
```

### wait-task response

Labels are included in the response metadata:

```json
{
  "task_id": "bold-falcon-42",
  "status": "completed",
  "labels": ["wave-1", "notch", "extraction"],
  "output": ["..."]
}
```

### Task detail (task:///{id})

The full task detail includes labels alongside other metadata.

## Label Strategies

### Wave identification

Tag tasks by execution wave for tracking parallel batches:

```
["wave-1"]  ["wave-2"]  ["wave-3"]
```

After each wave, read the scoreboard and visually filter: "Are all wave-1 tasks done?"

### Domain tagging

Tag by functional area when tasks span multiple domains:

```
["auth"]  ["ui"]  ["database"]  ["api"]
```

Useful when reviewing results: "Show me all auth-related tasks."

### Priority marking

Mark tasks by importance for triage when failures occur:

```
["critical"]  ["important"]  ["nice-to-have"]
```

If a wave partially fails, you can quickly identify which failures matter.

### Combined labels

Combine strategies for rich tracking:

```json
{
  "labels": ["wave-2", "auth", "critical"]
}
```

Scoreboard shows: `[busy] easy-wind-33 [wave-2,auth,critical] -- "Implement JWT refresh..."`

## Batch Operations Using Labels

### Visual filtering on scoreboard

Read `task:///all` and scan for your label. No programmatic filtering exists yet — you scan the text output.

```
# Read scoreboard
read resource: task:///all

# Mentally or textually filter for "wave-1"
# Count: 3 done, 0 busy, 0 fail → Wave 1 complete, proceed to Wave 2
```

### Batch cancel by inspection

To cancel all tasks in a wave:

1. Read scoreboard
2. Identify task IDs with the target label
3. Pass them as an array to cancel-task

```json
{
  "task_id": ["easy-wind-33", "free-lake-21", "gray-peak-55"]
}
```

### Wave completion check

After spawning a wave, the pattern is:

```
1. Spawn all tasks with ["wave-N"] label
2. Wait for each task
3. Read scoreboard — filter for wave-N
4. All done? → proceed to wave N+1
5. Any failed? → recover partial work, retry if needed
6. Still busy? → wait again
```

## Conventions and Limits

Keep labels short (under 20 chars), lowercase, hyphen-separated. Common patterns: `wave-N` (order), `auth`/`ui` (domain), `critical`/`p2` (priority), `extract`/`wire` (action).

- Practical limit: 3-5 labels per task
- Strings only — no key=value, no structured data
- Immutable after spawn
- No server-side filtering — visual scan of scoreboard only
- Empty `[]` is valid, equivalent to omitting

**Anti-patterns:** No labels on parallel tasks (can't track waves). Unique-per-task labels (defeats grouping). Labels as data (`["file:auth.ts"]` — use the prompt for metadata).
