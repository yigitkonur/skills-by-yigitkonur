# Serial Merge & Conflict Resolution Pipeline

This reference details the serial integration pipeline for landing candidate changes onto the mission-authorized target branch, including review delta verification after rebase, the self-contained 5-step conflict resolution engine, safe rebase aborts, and branch protection safeguards.

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
   Candidate #2 ───────►  Rebase onto target ───► Verify / Delta Review ───► Merge to target
                                    ▲                                          │
                                    │ (conflict)                               ▼ (target advances)
                                Resolve Conflict                     Candidate #3 ──► Rebase ...
```

---

## 2. Step-by-Step Serial Integration Pipeline

For each approved candidate in the queue:

### Step 1: Rebase Candidate onto Authorized Target Branch Baseline
Target the branch authorized by the mission brief (e.g. `main`, `release/v2`, `docs/unify-herdr`). Never assume `main` without authorization:
```bash
PRE_REBASE_SHA="$(git rev-parse HEAD)"
git fetch origin "$TARGET_BRANCH"
git rebase "origin/$TARGET_BRANCH"
POST_REBASE_SHA="$(git rev-parse HEAD)"
```

### Step 2: Compare Object IDs & Execute Required Delta Review
- Compare `PRE_REBASE_SHA` and `POST_REBASE_SHA`.
- If `PRE_REBASE_SHA == POST_REBASE_SHA`: the rebase was a clean no-op; prior review approval remains valid.
- If `PRE_REBASE_SHA != POST_REBASE_SHA`: Git generated a new commit object ID. **Prior review approval is invalidated**.
  - Execute repository-authorized check and validation commands on the new rebased HEAD:
    ```bash
    <AUTHORIZED_REPO_CHECK_COMMAND>
    ```
  - An independent reviewer must perform a focused delta review on the rebased candidate diff and issue an explicit approval decision before landing.

### Step 3: Push Verified Rebased HEAD (When Remote Delivery Authorized)
*Only execute remote push if the mission brief explicitly authorizes remote publication or PR creation. For local-only tasks, skip Step 3 and proceed to local integration in Step 4.*
- For new candidate branches: use standard `git push -u origin "$BRANCH_NAME"`.
- If an authorized task branch history rewrite occurred during rebase: use lease with verified expected remote state:
  ```bash
  git push --force-with-lease -u origin "$BRANCH_NAME"
  ```
  *Never push unconditional force (`git push -f`); never use force-with-lease unless a branch rewrite was explicitly required.*

### Step 4: Execute Authorized Delivery Action
Verify explicit delivery authority before taking actions:
- **If delivery authority authorizes PR / remote merge**:
  ```bash
  gh pr merge "$PR_URL" --squash
  ```
  *(Do not pass `--delete-branch` here; local branch retirement occurs strictly after the worktree checkout is unlinked during Stage 3 cleanup).*
- **If delivery authority authorizes local integration**:
  Do NOT run `git checkout "$TARGET_BRANCH"` inside secondary worktrees! If `$TARGET_BRANCH` is checked out in the primary repository workspace, Git will abort. Do NOT attempt `git push . "$BRANCH_NAME":"$TARGET_BRANCH"` (Git refuses updates to currently checked-out branches by default via `receive.denyCurrentBranch`).
  Instead:
  1. Inspect primary repository workspace: verify it is on `$TARGET_BRANCH` and its working tree is clean (`git -C "$REPO_ROOT" status --porcelain`). Preserve unrelated uncommitted work.
  2. Perform a fast-forward only merge in the primary workspace:
     ```bash
     git -C "$REPO_ROOT" merge --ff-only "$BRANCH_NAME"
     ```
  3. Verify the resulting integrated HEAD:
     ```bash
     git -C "$REPO_ROOT" rev-parse HEAD
     ```

---

## 3. Self-Contained Merge Conflict Resolution Engine

If `git rebase` encounters conflict markers, resolve them directly in the worktree:

### Step 1: Observe Exact Merge State & Identify Conflicting Files
Path-safe conflict extraction (captures all unmerged states `UU`, `AA`, `DD`, `DU`, `UD`, `AU`, `UA`, handling spaces safely):
```bash
# Check rebase status and list all unmerged files safely:
git diff --name-only --diff-filter=U

# Check conflict markers and boundaries:
git diff --check

# Compare commit histories:
git log --oneline -n 5 "origin/$TARGET_BRANCH"
git log --oneline -n 5 HEAD
```

### Step 2: Understand Original Intent of Both Sides
- Read commit messages and diffs for both upstream and candidate commits (`git log -p -1 origin/$TARGET_BRANCH` and `git log -p -1 HEAD`).
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
Verify syntax, types, and test suites on the resolved code using repository-authorized commands:
```bash
<AUTHORIZED_REPO_CHECK_COMMAND>
```

### Step 5: Complete Rebase Non-Interactively
```bash
# Stage resolved files using NUL-delimited pathspec (safe for spaces, tabs, and newlines):
git diff -z --name-only --diff-filter=U | xargs -0 -I{} git add -- "{}"
# Or explicitly stage individually owned resolved paths:
# git add -- "path/to/resolved file.ts"

# Continue rebase non-interactively:
GIT_EDITOR=true git rebase --continue
```

---

## 4. Safe Rebase Abort Invariant

If conflict investigation reveals that the target branch baseline has shifted fundamentally, or that the candidate's core assumptions conflict irreparably with merged upstream architecture:
```bash
git rebase --abort
```
Safe abort is authorized to return the branch to its clean pre-rebase state. Record the technical conflict details and escalate to the supervisor.
