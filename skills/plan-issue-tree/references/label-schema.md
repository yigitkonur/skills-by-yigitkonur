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

Every issue gets exactly one wave label. Wave N+1 cannot start until wave N is complete.

### Type labels

| Label | Color | Purpose |
|---|---|---|
| `type:epic` | `#3E4B9E` | Top-level grouping — contains features |
| `type:feature` | `#0E8A16` | User-facing capability — contains tasks |
| `type:task` | `#C2E0C6` | Implementation unit — contains subtasks |
| `type:subtask` | `#BFD4F2` | Atomic work — single agent session |

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

## Filtering

```bash
gh issue list -l "wave:1"                              # all wave 1 issues
gh issue list -l "status:ready" -l "type:task"         # ready tasks
gh issue list -l "priority:critical" -l "status:blocked" # critical blockers
gh issue list -l "wave:2" -l "type:feature" -s open    # open wave 2 features
```

## Setup

```bash
bash {baseDir}/scripts/setup-labels.sh OWNER/REPO
```
