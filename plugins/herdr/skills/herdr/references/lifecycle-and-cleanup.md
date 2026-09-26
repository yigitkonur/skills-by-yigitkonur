# Lifecycle, Resource Teardown & Cleanup Gates

Resource cleanup follows three distinct, decoupled engineering stages: pane retirement, worktree checkout removal, and local branch retirement. Decoupling these stages prevents orphaned processes, data loss, and git reference corruption.

```
[ Task Complete & Verified ]
            │
            ▼
[ Stage 1: Pane Retirement ] ──────► Close owned worker / reviewer panes
            │                        (Preserves checkout directory on disk)
            ▼
[ Stage 2: Worktree Removal Gate ] ─► Verify clean tree + delivery completion
            │                        + ignored build artifacts safety
            │                        herdr worktree remove --workspace <WS_ID>
            ▼
[ Stage 3: Safe Branch Retirement ] ─► Delete local branch (safe git branch -d)
                                     Refusal preserves branch reference; NO -D fallback.
```

---

## 1. Stage 1: Terminal & Pane Retirement

- **Worker Pane Retirement**:
  - Once an owned worker's handback report is received and verified durable on disk, ownership is reconciled, and no further operations remain in that pane, close the pane:
    ```bash
    herdr pane close "$PANE_ID"
    ```
  - Terminal release does NOT wait for PR merge or milestone completion. Releasing finished terminals promptly frees memory and PTY allocations.
- **Review & Author Retention Invariant**:
  - When using the side-by-side author/reviewer pattern, the author pane is retained while the reviewer is actively auditing.
  - **Do NOT close an author pane merely because a review verdict was reached**: If a review concludes with findings or a rejection verdict and fixes remain assigned to that author, keep the author pane alive to receive delta review findings and implement fixes.
  - An author pane is retired only when its candidate is accepted or the task is explicitly re-assigned or canceled.
- **Session Retention Rule**:
  - If a session must be retained for follow-up debugging, record an explicit retention reason and release trigger in the manager state. Conversation IDs and artifacts must be safe outside the process before closing.
- **Leadership Retirement**:
  - Leadership panes (EM or supervisor) retire ONLY when no remaining coordination, integration, or delivery responsibilities exist. Never retire leadership prematurely at an arbitrary wave boundary.
  - Never close active user-owned panes.
- **Pre-Closure & Disappearance Verification**:
  - Before closing any pane, tab, or workspace, verify live pane, session, child process, and pending effect ownership. Ensure all pending `.partial` files or unconsumed notices are finalized.
  - When closing a tab or workspace, verify ownership and successful termination of ALL child panes before whole-tab or whole-workspace closure.
  - Verify physical disappearance (`herdr pane list`, `herdr workspace list`) after issuing close commands.

---

## 2. Stage 2: Worktree Removal Gate

> [!CAUTION]
> **Worktree Removal is NOT Terminal Closure**:
> Closing a terminal pane does NOT delete its Git worktree checkout.
> Deleting a worktree checkout permanently removes the working directory from the filesystem.

### Prerequisites Before Worktree Removal:
1. **Delivery / Preservation Verification & Retained Commit Reachability**:
   - Ensure explicit retained commit reachability for ALL paths: a remote PR merged status or GitHub squash merge alone does NOT preserve the author's exact commit object in local git history. Verify the author's candidate commit object ID is preserved in an explicit local ref, branch, or run-root patch before worktree checkout removal.
   - If delivered via PR: verify PR is confirmed merged on remote:
     ```bash
     gh pr view "$PR_URL" --json state -q .state | grep -iq "MERGED"
     ```
     AND ensure candidate commit SHA is reachable locally.
   - If delivered locally: verify candidate commit is merged into target branch:
     ```bash
     git -C "$REPO_ROOT" merge-base --is-ancestor "$CANDIDATE_SHA" "$TARGET_BRANCH"
     ```
   - If read-only mission: verify task was non-mutating (no unmerged branch created).
   - If abandoned: verify decision is explicitly authorized and artifacts/diff are preserved at run root.
2. **Cleanliness Verification**:
   - Verify zero uncommitted or untracked changes remain:
     ```bash
     test -z "$(git -C "$WORKTREE_PATH" status --porcelain)"
     ```
3. **Ignored Artifact Safety**:
   - Verify that required build outputs, logs, or ignored artifacts in `.gitignore` are either safely archived outside the worktree or confirmed disposable.
4. **Open Operations Gate**:
   - Verify no background processes, compilers, or test runners remain running inside the worktree directory.

### Removal Command:
```bash
herdr worktree remove --workspace "$WORKSPACE_ID"
```

### Critical Invariants:
- **Ordinary Cleanup Uses No Force**: Ordinary cleanup uses NO force (`--force` is prohibited on ordinary paths). If uncommitted or untracked changes exist, or if checkout state is ambiguous, retain the worktree with an explicit recorded reason and release trigger rather than forcing removal.
- **Preserve Ambiguous Checkouts**: Dirty or ambiguous worktrees are **retained with a recorded reason and release trigger**; never force-delete.
- **Workspace Close vs. Worktree Remove**: `herdr workspace close` closes the UI session only, leaving Git tracking intact. Retained linked checkouts can be completely intentional.
- **No Global Zero-Worktree Prune**: Never run global worktree prune or seek a "zero worktrees on host" goal. Other branches, features, or teammates may have valid active worktrees. Touch ONLY what this task created.

---

## 3. Stage 3: Safe Local Branch Retirement

Git refuses to delete a local branch while it is checked out in an active worktree. Therefore, local branch cleanup occurs **strictly after Stage 2**:

1. **Safe Local Branch Deletion**:
   ```bash
   git -C "$REPO_ROOT" branch -d "$BRANCH_NAME"
   ```
2. **Refusal Preservation Rule (No `-D` Fallback)**:
   - If `git branch -d` refuses (e.g. branch is not fully merged in upstream tracking or rebase produced different commit object IDs), **DO NOT fall back to `git branch -D`**.
   - Force-deleting (`-D`) destroys the protective named Git reference, leaving commits dangling and making recovery difficult.
   - Retain the local branch reference and record the retention reason in the final report.
3. **No Global Remote Prune**:
   - Never run global remote prunes (`git remote prune origin`). A global prune affects remote tracking branches across the entire repository and disturbs concurrent work in unrelated worktrees.
4. **Verify Worktree List**:
   ```bash
   git -C "$REPO_ROOT" worktree list
   ```
   Confirm that the retired worktree path is no longer listed.
