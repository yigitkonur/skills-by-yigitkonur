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

## 3. Self-Contained Merge Conflict Resolution Engine

If `git rebase origin/main` encounters conflict markers, resolve it directly within the isolated worktree. Do not invoke external skills; follow this comprehensive, self-contained 5-step conflict resolution engine:

### Step 1: Observe Exact Merge State & Identify Conflicting Files
Never attempt to resolve conflicts before seeing the full state across Git history:
```bash
# Check rebase status and exact conflicting files:
git status

# Extract list of unmerged files (UU):
git status --porcelain | grep "^UU " | awk '{print $2}'

# Check diff markers and conflict boundaries:
git diff --check

# Compare commit histories of upstream main vs candidate branch:
git log --oneline -n 5 origin/main
git log --oneline -n 5 HEAD
```

### Step 2: Find Primary Sources & Understand Original Intent
Before touching a single line of code, understand *why* both changes were made:
- Read commit messages and diffs for both sides (`git log -p -1 <upstream_sha>` and `git log -p -1 <candidate_sha>`).
- Check PR descriptions, original tickets, or architecture records for both the upstream change and candidate PR.
- **Never guess**: Every conflict hunk reflects two intentional engineering decisions that collided.

### Step 3: Reconcile Each Hunk with Semantic Integrity
- Open each conflicted file and locate markers (`<<<<<<< HEAD`, `=======`, `>>>>>>> <commit>`).
- **Preserve Both Intents**:
  - Combine non-conflicting imports, exports, configuration keys, or schema fields.
  - **Preserve Upstream Invariants**: If earlier merged PRs added error-handling guards, security allowlists, cancellation checks, type definitions, or fast-syntax protections, **keep them intact**.
  - Layer the candidate branch's new functionality, tests, and fixes cleanly on top of those invariants.
- **When Mutually Exclusive**: Choose the implementation matching the project's documented architectural invariants, ADRs, and stated milestone goals. Document the trade-off in the commit message.
- **Strict Invariants**:
  - **Never blindly choose `--ours` or `--theirs`**.
  - **Never invent new, unrelated behavior** or opportunistic refactors during conflict resolution.
  - **Never abort (`git rebase --abort`)** unless the candidate branch is formally abandoned. Always resolve through to green.

### Step 4: Discover & Run Automated Repository Checks
Once hunks are reconciled and markers removed, verify the codebase against the project's automated quality gates:
```bash
# Fast Syntax Gate (if JavaScript/Node):
node --check <resolved_files>

# Typecheck:
npm run typecheck --if-present

# Behavioral Test Suites (must be green):
npm test --if-present

# Lint / Format:
npm run lint --if-present
```
Fix any syntax errors, type regressions, or broken assertions introduced by the reconciliation before proceeding.

### Step 5: Complete Rebase Non-Interactively & Push with Lease
In automated or agent environments, `git rebase --continue` can launch interactive editors (`nano`, `vi`), hanging the pane or process. Always use `GIT_EDITOR=true`:
```bash
# Stage resolved files:
git add <resolved_files>

# Continue rebase non-interactively:
GIT_EDITOR=true git rebase --continue
```
*Note*: If the rebase sequence has multiple commits, repeat Steps 1–5 until rebase finishes (`git status` reports `working tree clean`).

Once rebase is complete:
```bash
# Re-run full test suite on exact rebased HEAD:
npm test

# Push rebased branch using lease (NEVER blind force):
git push --force-with-lease -u origin "$BRANCH_NAME"
```

### Step 6: GitHub Self-Review & Squash Merge
If using the same GitHub auth token as PR author, `gh pr review --approve` returns `Can not approve your own pull request`. Submit a structured review comment instead:
```bash
gh pr review "$PR_URL" --comment -b "LGTM: verified candidate commit $(git rev-parse HEAD) after serial rebase onto main. All automated checks and tests pass."
```
Then perform the squash merge:
```bash
gh pr merge "$PR_URL" --squash --delete-branch
```

---

## 4. Worktree Lifecycle, Herdr Defaults & Clean Teardown

### Understanding Herdr's Default Worktree Behavior
Herdr couples Git worktree directories with Herdr workspaces, but enforces distinct semantics that must be understood to prevent orphaned checkouts or data loss:

1. **`herdr worktree remove --workspace <WORKSPACE_ID>`**:
   - Runs `git worktree remove` under the hood on the worktree directory and destroys the Herdr workspace registration.
   - **Crucial Invariant 1: Never Deletes the Branch**: Neither Herdr nor Git deletes the local branch when removing a worktree checkout.
   - **Crucial Invariant 2: Refuses Dirty Trees**: If uncommitted changes or untracked files exist, removal fails unless `--force` is provided. Never force-remove without verifying untracked changes are disposable.
2. **`herdr workspace close <WORKSPACE_ID>` vs `herdr worktree remove`**:
   - `workspace close` closes **ONLY Herdr's UI tabs and session processes**. It leaves the physical Git worktree directory on disk and Git's worktree registration completely orphaned!
   - Always use `herdr worktree remove --workspace <WORKSPACE_ID>` (or manually execute `git worktree remove <PATH>`) to delete the filesystem checkout.
3. **`gh pr merge --delete-branch` Limitation**:
   - Git refuses to delete a local branch while it is currently checked out in an active worktree (`cannot delete branch '<branch>' used by worktree at '<path>'`).
   - Therefore, local branch cleanup must occur **after** the worktree checkout is unlinked.

### The Zero-Bloat Teardown Protocol

Execute these stages in strict order:

### Stage 1: Mandatory Merge Integrity Gate
> [!CAUTION]
> **NEVER remove a worktree until the PR is confirmed submitted and merged into `main`** (or explicitly abandoned). Removing a worktree with unmerged, unpushed commits permanently destroys work.
```bash
# Confirm PR status is MERGED on remote:
gh pr view "$PR_URL" --json state -q .state | grep -iq "MERGED"
```

### Stage 2: Cleanliness Verification
Confirm zero uncommitted or untracked work remains in the checkout:
```bash
test -z "$(git -C "$WORKTREE_PATH" status --porcelain)"
```

### Stage 3: Remove Worktree & Workspace
Safely delete the checkout and unregister from Herdr:
```bash
# Preferred (Herdr socket API):
herdr worktree remove --workspace "$WORKSPACE_ID"

# Fallback (Manual Git + Herdr):
git worktree remove "$WORKTREE_PATH"
herdr workspace close "$WORKSPACE_ID"
```

### Stage 4: Delete Local Branch & Prune Tracking
Now that the branch is no longer checked out anywhere, delete it locally:
```bash
git -C "$REPO_ROOT" branch -d "$BRANCH_NAME" 2>/dev/null || git -C "$REPO_ROOT" branch -D "$BRANCH_NAME"
git -C "$REPO_ROOT" remote prune origin
```

### Stage 5: Verify Zero Lingering Worktrees
```bash
git -C "$REPO_ROOT" worktree list
# Must only output the primary repo root!
```

### Stage 6: Close Parent Meta/Tracking Issues
Close the tracking or umbrella issue with evidence:
```bash
gh issue close "$ISSUE_ID" --comment "Issue resolved by $PR_URL, rebased and merged into main."
```

### Stage 7: Post-Milestone Pane & Agent Retirement (CTO Obligation)
> [!IMPORTANT]
> **Zero Idle Agent Policy**: When a wave or entire milestone is complete (all tickets closed, all PRs merged), **immediately close all unrelated panes, tabs, and agents**.
> - **Engineering Manager Retirement**: If no further waves or dispatch tasks remain for the Engineering Manager, the CTO must cleanly close the EM agent pane:
>   ```bash
>   herdr pane close "$EM_PANE_ID"
>   ```
> - **Worker & Reviewer Pane Cleanup**: Close any lingering worker, reviewer, or temporary execution panes/tabs (`herdr pane close <PANE_ID>` or `herdr tab close <TAB_ID>`).
> - Never leave idle, orphaned AI agents running in the background consuming memory, API context, and cluttering `herdr pane list`.

### Stage 8: Notify Human User
```bash
herdr notification show "Integration & Teardown Complete" \
  --body "All candidate PRs merged to main. Worktrees, branches, and finished agent panes cleanly retired." \
  --sound done
```
