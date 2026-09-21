# Serial Merge & Conflict Resolution Pipeline

This reference details the serial integration and delivery mechanics for landing multiple parallel candidate PRs onto `main`, including automated conflict resolution in isolated worktrees, headless rebase safeguards, and clean resource teardown.

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

> [!NOTE]
> **Worktree Branch Deletion Notice**: When `gh pr merge --delete-branch` runs, Git attempts to delete the local branch as well. If the branch is currently checked out in an active worktree, Git will report:
> `failed to delete local branch <branch>: failed to run git: error: cannot delete branch '<branch>' used by worktree at '<path>'`
> This is normal and non-fatal. The local branch will be safely retired during Stage 5 Cleanup after the worktree is unlinked.

### Step 2: Primary Repository Sync
Keep the primary repo checkout synchronized with the remote HEAD:
```bash
git -C "$REPO_ROOT" pull origin main
```

### Step 3: Next Candidate Rebases onto Moving Baseline
Switch to Candidate 2's isolated worktree:
```bash
cd "$WORKTREE_2_PATH"
git fetch origin main
git rebase origin/main
```

- **If Rebase is Clean**:
  1. Run workspace validation suites:
     ```bash
     npm --workspace="$WORKSPACE" run typecheck
     npm --workspace="$WORKSPACE" run test
     ```
  2. Push the verified rebased HEAD using force-with-lease:
     ```bash
     git push --force-with-lease -u origin "$BRANCH_NAME"
     ```
  3. Merge to main:
     ```bash
     gh pr merge "$PR_2_URL" --squash --delete-branch
     ```
  4. Pull main again in root:
     ```bash
     git -C "$REPO_ROOT" pull origin main
     ```

---

## 3. Merge Conflict Resolution Protocol

If `git rebase origin/main` encounters conflict markers, handle it directly within the isolated worktree following semantic integrity principles:

### A. Identify Conflicting Files
```bash
git status --porcelain | grep "^UU "
```

### B. Resolve with Semantic Integrity
- Open each conflicted file.
- Inspect the conflict markers (`<<<<<<< HEAD`, `=======`, `>>>>>>> <commit>`).
- **Never blindly choose `--ours` or `--theirs`**.
- **Preserve Critical HEAD Invariants**: If earlier merged PRs added error-trapping logic, allowlisted environment keys, cancellation guards, or barrel export shims, **preserve them** while layering in the candidate's changes.
- Reconcile both intents cleanly: ensure imports, types, schemas, and behavior from both the integrated baseline and the current PR are satisfied.

### C. Non-Interactive Rebase Continuation
In automated, headless agent environments, `git rebase --continue` can trigger interactive commit message editors (`nano`, `vi`, `vim`), causing the agent or pane to hang.

Always invoke rebase continuation with `GIT_EDITOR=true`:
```bash
git add <resolved_files>
GIT_EDITOR=true git rebase --continue
```

### D. Re-Verify Candidate
Execute the full behavioral test suite and typecheck on the exact rebased HEAD:
```bash
npm --workspace="$WORKSPACE" run typecheck
npm --workspace="$WORKSPACE" run test
```

### E. Push with Lease
Never use blind `--force`. Always use lease to ensure no concurrent pushes are overwritten:
```bash
git push --force-with-lease -u origin "$BRANCH_NAME"
```

### F. GitHub Self-Review Handling
If the reviewer uses the same GitHub authentication token as the PR author, running `gh pr review --approve` returns:
`Review Can not approve your own pull request`

In this case, submit a structured review comment instead:
```bash
gh pr review "$PR_URL" --comment -b "LGTM: verified candidate commit $(git rev-parse HEAD). Behavioral tests and typechecks pass on latest rebased main."
```
Then proceed directly with the squash merge:
```bash
gh pr merge "$PR_URL" --squash --delete-branch
```

---

## 4. Post-Merge Teardown & Resource Cleanup

Once all candidate PRs have merged into `main`, execute the clean 5-stage teardown:

### Stage 1: Cleanliness Check
Ensure no uncommitted changes or untracked scratch files remain:
```bash
test -z "$(git -C "$WORKTREE_PATH" status --porcelain)"
```

### Stage 2: Close Herdr Reviewer Tabs & Worktree Workspaces
Close reviewer tabs and dedicated worktree workspaces over the Herdr socket API (note the positional `<workspace_id>` syntax):
```bash
herdr tab close "$REV_TAB_ID"
herdr workspace close "$WORKSPACE_ID"
```

### Stage 3: Remove Git Worktrees
Unlink and remove the worktrees:
```bash
git worktree remove "$WORKTREE_PATH"
```
> [!NOTE]
> For large monorepos with nested build caches or dependencies, `git worktree remove` performs intensive recursive filesystem deletions and may take 10–30 seconds. Await command completion before proceeding. Never use `--force` on a dirty worktree without explicit human consent.

### Stage 4: Clean Merged Local Branches & Prune Remotes
Delete the local branches that were preserved while checked out:
```bash
git branch -D "$BRANCH_NAME"
git remote prune origin
```

### Stage 5: Close Parent Meta/Tracking Issue
If the batch of PRs was tracked under an umbrella issue or parent meta-ticket, close it with a comprehensive completion summary:
```bash
gh issue close "$META_ISSUE_ID" --comment "All remediation tickets (#181-#185) and PRs (#187-#191) verified, rebased serially onto main, and merged."
```

### Stage 6: Notify Human User
```bash
herdr notification show "Integration Complete" \
  --body "All candidate PRs merged to main. Worktrees and workspaces cleanly retired." \
  --sound done
```
