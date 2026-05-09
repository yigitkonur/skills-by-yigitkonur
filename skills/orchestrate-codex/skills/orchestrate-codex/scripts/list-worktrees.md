# list-worktrees.py

Read-only enumeration of git worktrees with branch / dirty / unpushed / ahead-of-main columns. Ported from `run-repo-cleanup` verbatim.

## Inputs

```bash
python3 list-worktrees.py [--json] [--cwd <dir>]
```

| Arg | Notes |
|---|---|
| `--json` | Emit JSON; default is a human-readable table |
| `--cwd <dir>` | Override cwd for the `git worktree list` invocation |

## Outputs

Human (default):

```
PATH                                BRANCH                    DIRTY  UNPUSHED  AHEAD
/Users/yigit/dev/myrepo             main                      0      0         0
/Users/yigit/dev/myrepo-wt-exec-01  wave1/search-rewrite      3      2         5
/Users/yigit/dev/myrepo-wt-exec-02  wave1/cache-eviction      0      0         3
```

JSON (`--json`):

```json
[
  {"path": "/Users/yigit/dev/myrepo", "branch": "main", "dirty": 0, "unpushed": 0, "ahead": 0},
  {"path": "/Users/yigit/dev/myrepo-wt-exec-01", "branch": "wave1/search-rewrite", "dirty": 3, "unpushed": 2, "ahead": 5},
  ...
]
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Listed cleanly |
| 2 | Not in a git repo |

## Behavior

- Parses `git worktree list --porcelain`.
- For each worktree, runs `git -C <path> status --short` (counts), `git -C <path> log --oneline @{u}..` (unpushed count), `git -C <path> log --oneline origin/main..` (ahead-of-main count).
- Read-only: never modifies state.

## Notes

Useful for forensics during a fleet run. Combined with `audit-fleet-state.py`, surfaces orphan worktrees (worktree exists but no manifest entry) — those are the user's own worktrees, not the skill's; do not touch.
