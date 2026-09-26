# Serial Merge & Conflict Resolution Pipeline

This reference details the serial integration pipeline for landing candidate changes onto the mission-authorized target branch, including the self-contained 5-step conflict resolution engine, safe rebase aborts, and branch protection safeguards.

---

## 1. Why Serial Integration?

When multiple agents develop features or fixes across parallel worktrees, merging them simultaneously produces silent semantic regressions or merge races.

**The Golden Rule**: Every candidate must be verified on the exact integrated HEAD before landing.
Candidates are merged **serially in sequence** ($Candidate_1 \to Candidate_2 \to \dots \to Candidate_N$).

```
[ Approved Candidate Queue ]
   Candidate #1 ───────►  Merge to target branch
                                    │
                                    ▼ (target branch advances)
   Candidate #2 ───────►  Rebase onto target ───► Run Tests ───► Merge to target
                                    ▲                      │
                                    │ (conflict)           ▼ (target branch advances)
                                Resolve Conflict  Candidate #3 ──► Rebase ...
```

---

## 2. Step-by-Step Serial Integration Pipeline

For each approved candidate in the queue:

### Step 1: Rebase Candidate onto Authorized Target Branch Baseline
Target the branch authorized by the mission brief (e.g. `main`, `release/v2`, `docs/unify-herdr`). Never assume `main` without authorization:
```bash
git fetch origin "$TARGET_BRANCH"
git rebase "origin/$TARGET_BRANCH"
```

### Step 2: Validate Rebased Candidate
Run repository typechecks, linters, and behavioral test suites on the rebased code:
```bash
npm run typecheck --if-present
npm test --if-present
```

### Step 3: Push Verified Rebased HEAD
Push rebased commits using lease (never unconditional force):
```bash
git push --force-with-lease -u origin "$BRANCH_NAME"
```

### Step 4: Execute Authorized Delivery Action
- **If merging via PR**:
  ```bash
  gh pr merge "$PR_URL" --squash --delete-branch
  ```
  *(Note: Git will delete the remote tracking branch, but will refuse to delete the local branch while it remains checked out in an active worktree. Local branch cleanup occurs during post-worktree teardown).*
- **If merging locally**:
  ```bash
  git checkout "$TARGET_BRANCH"
  git merge --ff-only "$BRANCH_NAME"
  ```

---

## 3. Self-Contained Merge Conflict Resolution Engine

If `git rebase` encounters conflict markers, resolve them directly in the worktree:

### Step 1: Observe Exact Merge State
```bash
# Check rebase status and extract conflicting files (UU):
git status --porcelain | grep "^UU " | awk '{print $2}'

# Check conflict markers and boundaries:
git diff --check

# Compare commit histories:
git log --oneline -n 5 "origin/$TARGET_BRANCH"
git log --oneline -n 5 HEAD
```

### Step 2: Understand Original Intent of Both Sides
- Read commit messages and diffs for both upstream and candidate commits (`git log -p -1 <upstream_sha>` and `git log -p -1 <candidate_sha>`).
- Check tickets or architecture notes for both changes.
- **Never guess**: Every conflict hunk represents two intentional decisions that collided.

### Step 3: Reconcile Hunks with Semantic Integrity
- Open each conflicted file and locate markers (`<<<<<<< HEAD`, `=======`, `>>>>>>> <commit>`).
- **Preserve Upstream Invariants**: Keep error-handling guards, security allowlists, type definitions, and configuration keys introduced by earlier merged changes.
- Layer the candidate branch's new functionality, tests, and fixes cleanly on top of those invariants.
- **Strict Invariants**:
  - **Never blindly choose `--ours` or `--theirs`**.
  - **Never invent new, unrelated behavior** or opportunistic refactors during conflict resolution.

### Step 4: Run Automated Repository Checks
Verify syntax, types, and test suites on the resolved code:
```bash
npm run typecheck --if-present
npm test --if-present
```

### Step 5: Complete Rebase Non-Interactively
In automated or agent environments, `git rebase --continue` can launch interactive editors (`nano`, `vi`), hanging the pane. Always use `GIT_EDITOR=true`:
```bash
git add <resolved_files>
GIT_EDITOR=true git rebase --continue
```
Repeat Steps 1–5 if multiple commits are in the rebase sequence.

---

## 4. Safe Rebase Abort (Authorized Rollback)

Unlike rigid rules that prohibit aborting rebases under any circumstances:

- **When to Abort**: If conflict analysis reveals that the target branch baseline is structurally invalid, the candidate was rebased onto the wrong branch, or the conflict scope exceeds the author's mandate, executing `git rebase --abort` is **fully authorized**.
- **Preserve Evidence**: Before aborting, record the conflicting hunks and error log. Restore clean state and report the blocker to the supervisor.
