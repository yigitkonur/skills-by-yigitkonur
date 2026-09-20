# Serial Merge & Conflict Resolution Pipeline

This reference details the serial integration and delivery mechanics for landing multiple parallel candidate PRs onto `main`, including automated conflict resolution in isolated worktrees.

---

## 1. Why Serial Integration?

When multiple agents develop features or fixes across parallel worktrees, merging them simultaneously produces silent semantic regressions or merge races.

**The Golden Rule**: Every candidate must be verified on the exact integrated HEAD before landing.
PRs are merged **serially in sequence** ($PR_1 \to PR_2 \to \dots \to PR_N$).

```
[ Approved PR Queue ]
   PR #1 (Approved)  ───────►  Merge to main
                                   │
                                   ▼ (main advances)
   PR #2 (Approved)  ───────►  Rebase onto main ───► Run Tests ───► Merge to main
                                   ▲                      │
                                   │ (conflict)           ▼ (main advances)
                               Resolve Conflict  PR #3 (Approved) ──► Rebase ...
```

---

## 2. Step-by-Step Serial Landing Pipeline

For each approved PR in the queue:

### Step 1: Candidate 1 Merges Cleanly
```bash
gh pr merge "$PR_1_URL" --squash --delete-branch
```

### Step 2: Next Candidate Rebases onto Moving Baseline
Switch to Candidate 2's isolated worktree:
```bash
cd "$WORKTREE_2_PATH"
git fetch origin main
git rebase origin/main
```

- **If Rebase is Clean**:
  1. Run repository validation suites:
     ```bash
     npm run typecheck
     npm run test
     ```
  2. Push the verified rebased HEAD using force-with-lease:
     ```bash
     git push --force-with-lease
     ```
  3. Merge to main:
     ```bash
     gh pr merge "$PR_2_URL" --squash --delete-branch
     ```

---

## 3. Merge Conflict Resolution Protocol

If `git rebase origin/main` encounters conflict markers, handle it directly within the isolated worktree following the `resolving-merge-conflicts` skill principles:

### A. Identify Conflicting Files
```bash
git status --porcelain | grep "^UU "
```

### B. Resolve with Semantic Integrity
- Open each conflicted file.
- Inspect the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
- **Do not blindly choose `--ours` or `--theirs`**.
- Reconcile both intents: ensure imports, type definitions, and logic from both the freshly merged PR and the current candidate are preserved.

### C. Re-Verify Candidate
After resolving conflict markers:
```bash
git add <resolved_files>
git rebase --continue
```

Execute the full behavioral test suite and typecheck on the exact rebased HEAD:
```bash
npm run typecheck
npm run test
```

### D. Push with Lease
Never use blind `--force`. Always use lease to ensure no concurrent pushes are overwritten:
```bash
git push --force-with-lease
```

Wait for CI to pass on the new SHA, then land the PR:
```bash
gh pr merge "$PR_2_URL" --squash --delete-branch
```

---

## 4. Post-Merge Workspace & Worktree Cleanup

Once a candidate's PR is merged and deleted from remote:

1. **Close Herdr Workspace**:
   ```bash
   herdr workspace close --workspace "$WORKSPACE_ID"
   ```
2. **Worktree Removal Gate**:
   Verify worktree status is clean before deleting:
   ```bash
   test -z "$(git -C "$WORKTREE_PATH" status --porcelain)" && git worktree remove "$WORKTREE_PATH"
   ```
3. **Notify User**:
   ```bash
   herdr notification show "Integration Complete" \
     --body "PR #${PR_NUM} merged to main. Worktree retired." \
     --sound done
   ```
