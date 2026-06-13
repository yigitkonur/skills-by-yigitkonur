# Merge Rules

How to decide **what** to merge, **in what order**, and **what to do when it conflicts**. The scripts mechanize the parts that are mechanical; this file is the judgment layer.

## 1. Recency decides intent

A branch's age (time since its last commit) is the strongest signal of whether it's live work or abandoned debris.

| Age since last commit | Default treatment | Reasoning |
|---|---|---|
| **≤ 7 days** (`active`) | **Merge** (after review) | recent commits mean code you wrote on purpose and intend to use. |
| **> 7 days** (`stale`) | **Skip + report** | might be an abandoned spike, a superseded approach, or work that no longer fits the current code. Don't auto-merge it into a finished codebase. |
| already merged into base | **Retire** (Phase 5) | nothing to merge; the branch is just a dangling pointer to delete. |

`stale` does **not** mean delete. It means *the human decides*. Three sub-cases for a stale branch:

- **Still relevant** ("I started this last month, it's real, I want it") → confirm, then merge it like an active branch.
- **Superseded / philosophically disconnected** from the current state of the code → leave it, name it in the report, don't merge and don't delete.
- **Genuinely abandoned** → still don't auto-delete; report it so the human can delete deliberately.

The `--stale-days` flag (default 7) tunes the cutoff. Bump it for a long-running project; lower it for a fast one.

## 2. Order: foundation → leaf

When several branches are live (the parallel-worktree case), **order matters**. Merge the foundation first so later branches land on a more-complete base; merge independent leaves last.

`plan-merge-order.py` scores each branch by **file overlap**: for every file a branch touches, how many *other* branches also touch it. High overlap ⇒ foundational ⇒ merge early. Zero overlap ⇒ independent leaf ⇒ merge late. Recency breaks ties (newer foundational work first).

The script **suggests**; you **decide**. Override when semantics beat the heuristic:
- Tests for feature X must merge *after* X, regardless of overlap.
- A refactor that everything else builds on merges *first*, even if it touches few files.
- A pure-docs branch usually merges *last* (it rarely conflicts and isn't load-bearing).

### Worked example — 25 worktrees of fixes

You ran 25 parallel agents, each in its own worktree, each fixing something, then run cleanup. Don't merge in finish-order. Instead:

1. `audit-state.py --base main --json` → classify all 25 by age. Say 22 are `active`, 3 are `stale` (started early, never finished).
2. `plan-merge-order.py --base main` → the 22 active branches ordered by overlap. The 3 stale ones are listed separately.
3. Read the plan. The branches touching `src/core/*` (which many others also touch) sort to the front — merge those first so the 18 leaf fixes merge onto a base that already has the core changes. Pure-leaf fixes (one isolated file each) merge last and almost never conflict.
4. Decide the 3 stale branches one by one: two are superseded by the active fixes → skip + report; one is real but old → confirm and merge it early (it's foundational).
5. `merge-branches.py --base main --branches <ordered list> --execute`.
6. Any conflict → resolve by hand (§3) or skip. Report every disposition.

The point: **think about the merge logic before merging**, especially at scale. 25 arbitrary-order merges produce 25 chances for avoidable conflicts; a planned order collapses most of them.

## 3. Conflicts: understand or skip — never guess

`merge-branches.py` attempts each merge with `--no-ff --no-commit`. A clean merge it commits. A conflicted merge it **aborts** (`git merge --abort`) and records as `skipped-conflict`. It does **not** resolve anything — resolution is a human-judgment act.

When a branch is reported as conflicting, resolve it by hand **only if you understand both sides**:

1. `git merge --no-ff <branch>` to re-enter the conflict.
2. `git log --oneline main..<branch>` and `git log --oneline <branch>..main` — read *why* each side changed the conflicting region. The commit messages are the intent.
3. For each conflict hunk, ask: *do these two changes serve the same goal or different goals?*
   - Same goal, compatible → combine them.
   - One supersedes the other → keep the newer/correct one, with reasoning you can state.
   - Genuinely incompatible → **abort and skip.** `git merge --abort`. Report it. The human resolves it with full context.
4. After resolving: `git diff --cached` to confirm the result is what you intended, then commit.

A `skipped-conflict` branch is a **clean, honest outcome**. A wrongly-merged conflict is silent data loss that surfaces as a bug weeks later. Prefer the skip.

## 4. Review before merge — when to dispatch a subagent

Read every branch's diff and commit log before merging (Phase 3.1). For a **significant** branch — **>300 changed lines or >10 files** — dispatch a review subagent:

> Read the diff `git diff main...<branch>` and the commits `git log main..<branch>`. Report: (1) one-sentence summary of what the branch does; (2) anything risky — deletions, config/secret changes, behavior changes without tests; (3) merge-safe or needs-attention. Return findings only; do not merge.

Treat the subagent's report as a **claim**, not verification — spot-check the risky parts it names before merging. For small branches (a few lines, one file), read them yourself; a subagent is overhead.

## 5. Why `--no-ff`

Always merge with `--no-ff` (no fast-forward). It creates a merge commit even when a fast-forward was possible, so:
- Each branch's work stays grouped as one revertable unit (`git revert -m 1 <merge>` undoes the whole branch).
- The history shows *which* branch each change came from — useful when the report says "merged-now" and you later want to find it.
- It's the closest local equivalent to "this branch was merged as a unit," which is what the human mental-model expects.
