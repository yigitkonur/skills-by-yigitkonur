# suggest-merge-order.py

Proposes a foundation-first merge order for N branches relative to a base. **Heuristic-only** — the agent still decides the final order; this script is a starting point.

## Usage

```bash
python3 scripts/suggest-merge-order.py --base main
python3 scripts/suggest-merge-order.py --base main --branches feat/a feat/b docs/c
python3 scripts/suggest-merge-order.py --base main --json
```

## Heuristic

A branch that modifies files also modified by other branches is **more foundational** — other branches will want to rebase on top of it once it merges.

1. For each branch, compute files modified vs `<base>`: `git diff --name-only <base>...<branch>`.
2. Count, for each branch, how many (branch, file) overlaps it has with sibling branches.
3. Sort: higher overlap score first (foundation), ties broken by fewer commits last (smaller / leaf PRs go later).

The overlap score is a proxy for dependency, not a proof of dependency. Semantic dependencies (e.g. "tests for X must merge after X") are invisible to this heuristic.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--base <ref>` | `main` | Base to diff each branch against. |
| `--branches <...>` | all non-base local branches | Explicit branch list (whitelist). |
| `--json` | off | Emit JSON array instead of text report. |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Ordering printed. |
| 1 | Fewer than 2 branches passed the filter — no ordering needed. |
| 2 | Not a git repo / git error. |

## When to run

- **Phase 2**, after `list-worktrees.py` confirms multi-worktree scenario.
- **Before opening the first PR of a stack**, to decide the base-branch layout.

## The agent's decision step

After reading the suggestion:

1. Write down the proposed order with your own one-line rationale per branch.
2. Consider semantic dependencies the heuristic missed (tests, docs, migrations).
3. Override if needed. The script is a starting point, not a verdict.
4. Execute in the final order: first branch → Phase 1 → Phase 3 → Phase 4; then second branch; …

## Safety

Read-only across all branches. Never mutates. Pure `git diff --name-only` + `git rev-list --count`.

## Sample output

```
suggested merge order (3 branches):

  1. feat/refactor-auth
     position 1: touches 5 file-overlaps with siblings; 4 commits.
     files modified: 12 · overlap score: 5

  2. feat/new-login-ui
     position 2: touches 2 file-overlaps with siblings; 3 commits.
     files modified: 5 · overlap score: 2

  3. docs/auth-guide
     position 3: leaf/independent with fewest cross-branch conflicts.
     files modified: 1 · overlap score: 0

NOTE: this is a heuristic (foundation = more file overlap with other branches).
The agent decides the final order. Override when the heuristic misses semantic
ordering (e.g. 'tests for X must merge after X').
```

## Extending

- Add semantic-hint flags (`--before`, `--after`) to let the user pin ordering constraints.
- Add commit-author diff to flag when two branches touch the same lines, not just same files (more specific conflict signal).
