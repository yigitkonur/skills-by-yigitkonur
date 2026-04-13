# Labels and Tracking

Labels are string arrays attached to tasks at spawn time. They appear throughout the lifecycle and are the primary mechanism for organizing parallel work.

## Setting Labels

Set labels with the `--label` flag at spawn time:

```bash
cli-codex-subagent run task.md --label wave-1 --label notch --label extraction
```

Or in the task.md frontmatter:

```yaml
---
labels: ["wave-1", "notch", "extraction"]
---
```

Labels are immutable after spawn. You cannot add or remove labels from a running task.

## Where Labels Appear

### Scoreboard

The scoreboard is the primary tracking view. Labels appear in brackets after the task ID:

```
tasks -- 6 total (3 done, 2 busy, 1 fail)

[done]    tsk_abc123   [wave-1,notch]      -- "Extract NotchHoverStateMachine..."
[done]    tsk_def456    [wave-1,music]      -- "Extract MusicHoverController..."
[done]    tsk_ghi789     [wave-1,gesture]    -- "Extract NotchGestureRouter..."
[busy]    tsk_jkl012     [wave-2,notch]      -- "Wire NotchHoverStateMachine into..."
[busy]    tsk_mno345     [wave-2,music]      -- "Wire MusicHoverController into..."
[fail]    tsk_pqr678     [wave-2,gesture]    -- "Wire NotchGestureRouter into..."
```

### task read output

Labels appear in `task read` output:

```
taskId:     tsk_abc123
status:     done
labels:     wave-1, notch, extraction
completedAt: 2025-01-15T10:32:45Z
```

### Task detail

`cli-codex-subagent task read tsk_abc123` includes labels alongside other metadata.

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

```bash
cli-codex-subagent run task.md --label wave-2 --label auth --label critical
```

Scoreboard shows: `tsk_jkl012  [done]  23s  wave-2, auth, critical`

## Batch Operations Using Labels

### Visual filtering on scoreboard

Use `cli-codex-subagent task list --label wave-N` to filter by label.

```
# Read scoreboard
cli-codex-subagent task list

# Mentally or textually filter for "wave-1"
# Count: 3 done, 0 busy, 0 fail → Wave 1 complete, proceed to Wave 2
```

### Batch cancel by inspection

To cancel all tasks in a wave:

1. `cli-codex-subagent task list --label wave-N` to find IDs
2. Cancel each:

```bash
cli-codex-subagent task cancel tsk_jkl012
cli-codex-subagent task cancel tsk_mno345
cli-codex-subagent task cancel tsk_pqr678
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
