# Serial Merge Queue & Conflict Avoidance Protocol

This guide defines the parent-controlled serial merge architecture, conflict-avoidance rebase queues, and safe worktree retirement lifecycle.

---

## 1. Core Laws of the Merge Engine

### The Zero Data Loss Mandate

> [!CAUTION]
> **NEVER kill a subagent or delete a worktree until its branch has been pushed to remote and cleanly merged.**
> Premature deletion permanently destroys unmerged local commits and working tree state.

### Serial Integration Invariant

Parallel subagents write code in isolated branches (`fix/audit-*`), but integration into `main` must proceed **serially, one PR at a time**. Merging multiple PRs in parallel without rebasing creates silent semantic conflicts and corrupts shared configurations.

---

## 2. The Step-by-Step Serial Merge Lifecycle

```
  [Candidate PR #1352] ──► Merge to main ──► Run Premerge ──► Push origin/main
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
  [Candidate PR #1354] (Overlapping Files?)     [Candidate PR #1351] (Disjoint Paths?)
        │                                               │
  Rebase on origin/main                           Direct Merge Ready
  Resolve any conflicts
  Re-verify scoped tests
```

### Step 1: Establish Integration Order

Sort candidate PRs by architectural layer (foundation/policies first, leaf components last):

1. **Infrastructure & Edge Policies** (e.g. Workloads 41, 52, 56, 66, 67, 70)
2. **Content Layer & Schemas** (e.g. Workloads 31, 35, 63, 64, 65)
3. **Components & Layouts** (e.g. Workloads 01-10, 11-20, 53, 54, 59, 61, 62)
4. **Documentation & Registry** (e.g. Workload 50)

### Step 2: Merge the Leading Candidate

From the primary repository root on `main`:

```bash
git checkout main
git pull origin main

# Option A: Merge via GitHub CLI (recommended for PR tracking)
gh pr merge <PR_NUMBER> --squash --delete-branch=false

# Option B: Fast-forward / squash locally
git merge --squash fix/audit-<ID>
git commit -m "fix(<scope>): <summary> (#<PARENT_ID>)"
```

### Step 3: Run Primary Verification Gates on `main`

```bash
# Verify documentation integrity
pnpm check:doc-integrity

# Run premerge verification gate
pnpm premerge:runner:prepush

# Push updated main to remote
git push origin main
```

### Step 4: Serial Rebase of Remaining Candidates

For each remaining open candidate branch touching overlapping files:

```bash
cd .worktrees/wt-<NEXT_ID>
git fetch origin main
git rebase origin/main

# If conflicts occur: resolve manually, stage, and continue
git rebase --continue

# Re-run scoped tests to verify zero regressions
pnpm exec vitest run tests/int/<slug>.test.ts

# Force-push updated branch to PR
git push --force-with-lease origin fix/audit-<NEXT_ID>
```

### Step 5: Safe Worktree Retirement

Once a PR is merged into `main` and verified:

```bash
# Remove the isolated worktree
git worktree remove .worktrees/wt-<ID> --force

# Prune stale tracking references
git worktree prune

# Verify zero orphaned worktrees remain
git worktree list
```
