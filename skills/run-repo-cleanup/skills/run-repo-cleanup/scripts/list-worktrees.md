# list-worktrees.py

Enumerates every git worktree with its branch, HEAD, dirty-file count, and unpushed-commit count. Used in Phase 0 and Phase 2 to detect and plan the multi-worktree scenario.

## Usage

```bash
python3 scripts/list-worktrees.py           # human report
python3 scripts/list-worktrees.py --json    # machine-readable
```

## What it reports (per worktree)

- `path` — filesystem path of the worktree.
- `branch` — current branch (or `(detached)` / `(bare)`).
- `head` — 8-char commit SHA at HEAD.
- `upstream` — tracking remote+branch (if set).
- `dirty_count` — number of dirty files (output of `git status --porcelain`).
- `unpushed` — commits ahead of the tracking upstream.
- `commits_ahead_of_origin_main` — commits ahead of `origin/main` (useful for merge-order heuristics).
- Flags: `locked`, `prunable`, `bare`, `detached` when applicable.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--json` | off | Emit JSON (array of objects) instead of the text report. |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Enumerated successfully (even if only 1 worktree). |
| 2 | Not inside a git repository. |

## When to run

- **Phase 0** — after `audit-state.py` flags multi-worktree scenario.
- **Phase 2** — before running `suggest-merge-order.py` to sanity-check the branch list.
- **Phase 5** — before `git worktree remove` to confirm the worktree's state (no unpushed / dirty work about to be lost).

## Safety

Read-only across all worktrees. Never mutates. Enters each worktree directory via `subprocess.run(cwd=…)` but does not modify anything.

## Sample output

```
3 worktree(s):

  • /Users/you/dev/myrepo
    branch: main  (HEAD abc12345)
    tracks: origin/main
    state:  0 dirty · 0 unpushed · 0 ahead of origin/main

  • /Users/you/dev/myrepo-worktree-feat
    branch: feat/foo  (HEAD def67890)
    tracks: origin/feat/foo
    state:  3 dirty · 2 unpushed · 5 ahead of origin/main

  • /Users/you/dev/myrepo-worktree-docs
    branch: docs/bar  (HEAD ghi45678)
    state:  0 dirty · 1 unpushed · 3 ahead of origin/main

→ multi-worktree scenario. Use suggest-merge-order.py for ordering.
```

## Extending

To add per-worktree information (e.g., last commit author, time since last commit), extend `enrich()`. Keep it pure-read.
