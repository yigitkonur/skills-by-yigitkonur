# Scripts (index)

Every script in this directory is paired with a `<name>.md` doc that holds its full reference. This `README.md` is just the index — read the per-script `.md` for flags, exit codes, and when-to-run details.

## Index

| Phase | Script | Paired doc | One-liner |
|---|---|---|---|
| 0 | [`audit-state.py`](audit-state.py) | [`audit-state.md`](audit-state.md) | Read-only repo state dump (dirty files, worktrees, remotes, open PRs). |
| 0 | [`init-to-delete.py`](init-to-delete.py) | [`init-to-delete.md`](init-to-delete.md) | Idempotent setup of `to-delete/` folder + recommended `.gitignore` patterns. |
| 0 / 2 | [`list-worktrees.py`](list-worktrees.py) | [`list-worktrees.md`](list-worktrees.md) | Enumerate worktrees with branch + dirty + unpushed. |
| 2 | [`suggest-merge-order.py`](suggest-merge-order.py) | [`suggest-merge-order.md`](suggest-merge-order.md) | Foundation→leaf merge-order heuristic for N branches. |
| 4 | [`draft-pr-body.py`](draft-pr-body.py) | [`draft-pr-body.md`](draft-pr-body.md) | PR body skeleton from a commit range. |
| 5 | [`retire-merged-branches.py`](retire-merged-branches.py) | [`retire-merged-branches.md`](retire-merged-branches.md) | Delete merged local + remote branches (dry-run default). |

## Runtime

- Python 3.9+ (stdlib only — no pip, no deps).
- `git` on PATH.
- `gh` CLI on PATH for scripts that query GitHub (optional; those scripts gracefully omit GitHub sections if `gh` is missing).

## Conventions

- Every script is executable (`chmod +x`).
- Every script has a paired `.md` with the same base name.
- Every script's `--help` and its paired `.md` agree on flags, defaults, and exit codes.
- Every mutating script defaults to dry-run; `--execute` is required to change state.
- No `.env`, no secrets read from environment. If a script ever needs a credential, hardcode it in the script and document it at the top of the paired `.md` — the private-skills-pack policy accepts hardcoded values because the repo is private.

## When you add a new script

1. Give it a comprehensive kebab-case name (`verb-object` pattern).
2. Create the `.py` AND the paired `.md` in the same commit.
3. Add a row to the Index table above.
4. Reference the script from `../SKILL.md` (the skill's top-level) in the "Scripts" section.
5. Run `python3 <repo-root>/scripts/validate-skills.py` — must pass.

## Tested on

macOS 14+ and Linux. Windows has not been tested.
