# Multi-Worktree Merge Ordering (Phase 2)

When multiple subagents (or the same agent across multiple parallel tasks) have produced **N separate worktrees**, each on its own branch, Phase 2 decides the order they become PRs. Wrong order → pointless rebases, confused reviewers, or worse, conflicting merges.

## When this phase applies

Skip Phase 2 if `git worktree list` shows only one worktree (the main one). Otherwise, every additional worktree is an independent branch whose commits need to ship. Typical scenarios:

- User dispatched 3 Explore agents → 3 worktrees with research findings.
- User had coding + doc subagents in parallel → 1 feature worktree, 1 docs worktree.
- You started work, switched to a parallel task in a worktree, never closed out.

## The decomposition

**Think first: what does each worktree *produce*?**

For each worktree, answer in one phrase:
- Feature code (`feat(…)` in commit subjects)
- Documentation (`docs(…)`)
- Tests (`test(…)`)
- Infrastructure / CI (`build(…)`, `ci(…)`)
- Tooling / scripts (`chore(…)`)
- Refactor of something shared (`refactor(…)`)

The classification drives the ordering.

## Ordering rules — foundation → leaves

1. **Foundation branches go first.** If branch A modifies a file that branch B also modifies, A is more foundational (B will need to re-examine its changes against A). Merge A first.
2. **Shared-refactor branches go before features that depend on them.** A refactor that renames a function should ship before a feature that uses the renamed function.
3. **Tests and docs can go last.** They usually only reference existing code; they don't block anything else.
4. **Independent branches (no file overlap) can ship in any order.** Prefer shortest/simplest first to keep reviewer momentum.

## Computing the order

Use `python3 scripts/suggest-merge-order.py --base main` for the heuristic:

- Compute the set of files each branch modifies (`git diff --name-only <base>..<branch>`).
- Build an overlap graph: branches that share files are "adjacent".
- Branches with more overlaps (touch files others touch) are more foundational.
- Topological sort with ties broken by commit count (smaller branches go later).

The script **proposes** ordering; the agent **decides**. The heuristic misses semantic ordering (e.g. "tests for X must merge after X" is a semantic constraint, not a file-overlap one).

## The agent's decision step

After reading the suggestion, write down:

```
merge order:
  1. <branch-A>  (foundation: renames of shared helpers)
  2. <branch-B>  (feature: uses the renamed helpers)
  3. <branch-C>  (docs for the feature)
  4. <branch-D>  (tests for the feature)
```

If two branches are truly independent, note it:

```
  1-OR-2. <branch-E>  (independent: touches scripts/ only)
  1-OR-2. <branch-F>  (independent: touches docs/guides/ only)
```

Start with the foundation. Finish before starting the next.

## Execute in order

For each branch in merge order:

1. **Enter the worktree** or check out the branch.
2. **Run Phase 1** (diff-walk → conventional commits). Most of the work may be done; you're just cleaning up the last commits.
3. **Run Phase 3** (push + open PR). Push, open the PR on the fork with `--repo` explicit.
4. **Run Phase 4** (self-review body). Stay under 50k chars.
5. **Do NOT start the next branch until the previous is pushed.** This keeps reviewer context ordered.
6. If stacking: the N+1 PR's base is the N PR's branch, not `main`. Note "stacked on #N" in the body.

## After the foundation PR merges

If upstream branches need rebasing onto the newly-merged base:

```bash
git fetch origin main
cd <path-to-next-worktree>
git rebase origin/main
# resolve any conflicts
git push --force-with-lease origin <branch>   # only if no review in progress
```

If the next branch already has an open PR and reviewers have commented inline, **do not rebase**. Merge `main` into the branch instead (regular merge commit), or wait for the review to finish.

## Worked example (adapted from the Wope cleanup)

Starting state: 3 branches on the private fork.
- `feat/wope-branding-lockdown` — 2 commits touching `src/`, `locales/`, `index.html`.
- `docs/wope-agent-optimization` — 2 commits touching `src/**/AGENTS.md` (9 nested files).
- `docs/scratch-handoff` — 1 commit that shouldn't exist (session artifact). Move to `to-delete/` or abandon.

File-overlap graph:
- `feat/wope-branding-lockdown` touches `src/features/ChatInput/ActionBar/Model/index.tsx` (among others).
- `docs/wope-agent-optimization` touches `src/features/ChatInput/AGENTS.md` — same folder.

→ `feat/wope-branding-lockdown` is foundation (code change).
→ `docs/wope-agent-optimization` is leaf (documents the code change).
→ `docs/scratch-handoff` is noise → abandon.

Executed order: PR #1 on `feat/wope-branding-lockdown` (fork, base `main`), PR #2 stacked on #1 (base `feat/wope-branding-lockdown`). Session-artifact branch abandoned (branch deleted locally, worktree removed).

## Retirement after merge

Each merged branch + its worktree must be retired in Phase 5:

```bash
# After PR #1 merges to main
git fetch --all --prune
git worktree remove <path-to-old-worktree>
python3 scripts/retire-merged-branches.py --base main --execute
```

See `scripts/retire-merged-branches.md`.

## Common Phase 2 mistakes

| Mistake | Consequence | Fix |
|---|---|---|
| Merge in arbitrary order | Cascading rebases on sibling branches | Foundation first |
| Start all PRs simultaneously | Reviewer can't follow | Push + PR in merge order |
| Ignore script's suggestion without reason | Might be right | Override with a reason, write it down |
| Let `suggest-merge-order.py` be the decider | Script is heuristic only | Agent decides |
| Leave abandoned worktrees | Debris | `git worktree remove` after Phase 5 |
| Force-push a stacked child after parent merge | Invalidates review comments | Merge `main` in instead if review is in progress |

## The mindset

Multi-worktree is a dependency graph problem, not a git-command problem. Name the relationships first (foundation / leaf / independent), *then* run the commands. If you can't name why A comes before B, you don't yet understand the work — ask, or read more of the diffs.
