# Scripts (index)

The mechanical layer of `run-repo-cleanup`. Each script's full reference lives in its own `--help` and module docstring — there is no separate paired `.md` (that duplication was removed). Read the docstring at the top of any `.py` for flags, exit codes, and behavior.

## Index

| Phase | Script | One-liner | Mutates? |
|---|---|---|---|
| 0 / 5 | [`audit-state.py`](audit-state.py) | Inventory: every branch with age + merged-status + classification, worktrees, dirty tree. JSON feeds the report. | No |
| 0 / 2 | [`list-worktrees.py`](list-worktrees.py) | Enumerate worktrees with branch + dirty + ahead-of-base. | No |
| 2 | [`plan-merge-order.py`](plan-merge-order.py) | Order live branches foundation→leaf; split out stale + already-merged. | No |
| 3 | [`merge-branches.py`](merge-branches.py) | Merge branches into base `--no-ff`; predict/abort conflicts. Never resolves them. | Yes (`--execute`) |
| 4 | [`sweep-artifacts.py`](sweep-artifacts.py) | Move non-essential files → `to-delete/`; consolidate docs → `docs/`; manage `.gitignore`. | Yes (`--execute`) |
| 5 | [`retire-merged-branches.py`](retire-merged-branches.py) | Fetch+prune, delete merged local+remote branches + their worktrees. Refuses unmerged. | Yes (`--execute`) |

## Runtime

- Python 3.9+ (stdlib only — no pip, no deps).
- `git` on PATH. `merge-branches.py` dry-run conflict prediction uses `git merge-tree --write-tree` (git ≥ 2.38); on older git it reports `unknown` and you predict by merging in execute mode.

## Conventions

- Every script is executable (`chmod +x`) and Python 3 stdlib only.
- Every mutating script defaults to **dry-run**; `--execute` is required to change state.
- `--json` on the read-only scripts emits machine-readable output for building the end-of-run report.
- No `.env`, no secrets read from the environment.

## Tested on

macOS 14+ and Linux. Windows untested.
