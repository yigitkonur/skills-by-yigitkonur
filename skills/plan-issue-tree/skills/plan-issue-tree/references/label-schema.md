# Label Schema

Standard label taxonomy for wave-based planning. Every issue gets at least three labels: one wave, one type, one priority.

## Categories

### Wave labels

| Label | Color | Purpose |
|---|---|---|
| `wave:0-foundation` | `#0052CC` | Setup and shared dependencies — completes first |
| `wave:1` | `#1D76DB` | First feature wave |
| `wave:2` | `#5319E7` | Second feature wave |
| `wave:3` | `#B60205` | Third wave |
| `wave:4` | `#D93F0B` | Fourth wave |
| `wave:5` | `#E4E669` | Fifth wave |

Every issue gets exactly one wave label. Wave N+1 cannot start until wave N is complete. Baseline setup creates `wave:0-foundation` through `wave:5`. If the approved plan needs Wave 6 or higher, rerun label setup with `MAX_WAVE=<highest wave>`.

### Type labels

| Label | Color | Purpose |
|---|---|---|
| `type:epic` | `#3E4B9E` | Top-level grouping — contains features |
| `type:feature` | `#0E8A16` | User-facing capability — contains tasks |
| `type:task` | `#C2E0C6` | Implementation unit — contains subtasks |
| `type:subtask` | `#BFD4F2` | Atomic work — single agent session |
| `type:tracking` | `#7057FF` | Traceability or dependency-matrix issue used to track large plans |

### Priority labels

| Label | Color | Purpose |
|---|---|---|
| `priority:critical` | `#B60205` | Blocks other work |
| `priority:high` | `#D93F0B` | Should complete this wave |
| `priority:medium` | `#FBCA04` | Important, not blocking |
| `priority:low` | `#0E8A16` | Can defer |

### Status labels (applied during execution)

| Label | Color | Purpose |
|---|---|---|
| `status:blocked` | `#B60205` | Waiting on dependency |
| `status:ready` | `#0E8A16` | All dependencies met |
| `status:in-progress` | `#FBCA04` | Currently being worked |
| `status:needs-review` | `#D876E3` | Needs human review |
| `status:failed` | `#D73A4A` | Attempt failed; issue stays out of the ready queue until user chooses recovery |

## Filtering

```bash
gh issue list --repo "$REPO" -l "wave:1"                                # all wave 1 issues
gh issue list --repo "$REPO" -l "status:ready" -l "type:task"           # ready tasks
gh issue list --repo "$REPO" -l "priority:critical" -l "status:blocked" # critical blockers
gh issue list --repo "$REPO" -l "wave:2" -l "type:feature" -s open      # open wave 2 features
gh issue list --repo "$REPO" -l "status:failed"                         # failed issues awaiting a recovery decision
```

## Setup

Assumes `SKILL_DIR` is the absolute path to this skill directory:

```bash
bash "$SKILL_DIR/scripts/setup-labels.sh" "$REPO"          # creates wave:0-foundation and wave:1..wave:5
MAX_WAVE=7 bash "$SKILL_DIR/scripts/setup-labels.sh" "$REPO"  # if your plan uses wave:6 or higher
```
