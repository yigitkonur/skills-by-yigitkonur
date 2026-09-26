# Lifecycle, Resource Teardown & Cleanup Gates

Resource cleanup follows three distinct, decoupled engineering stages: pane retirement, worktree checkout removal, and local branch retirement. Decoupling these stages prevents orphaned processes, data loss, and git reference corruption.

```
[ Task Complete & Verified ]
            │
            ▼
[ Stage 1: Pane Retirement ] ──────► Close owned worker / reviewer panes
            │                        (Preserves checkout directory on disk)
            ▼
[ Stage 2: Worktree Removal Gate ] ─► Verify clean tree + merge verified
            │                        herdr worktree remove --workspace <WS_ID>
            ▼
[ Stage 3: Branch Retirement ] ────► Delete local branch (git branch -d/-D)
                                     Prune remote references
```

---

## 1. Stage 1: Terminal & Pane Retirement

- **Worker Pane Retirement**:
  - Once an owned worker's handback report is received and verified durable on disk, ownership is reconciled, and no further operations remain in that pane, close the pane:
    ```bash
    herdr pane close "$PANE_ID"
    ```
  - Terminal release does NOT wait for PR merge or milestone completion. Releasing finished terminals promptly frees memory and PTY allocations.
- **Side-by-Side Review Preservation**:
  - When using the side-by-side implementer/reviewer pattern, the implementer pane is retained while the reviewer is actively auditing or testing. Both panes are retired after the review verdict is reached.
- **Session Retention Rule**:
  - If a session must be retained for follow-up debugging, record an explicit retention reason and release trigger in the manager state. Conversation IDs and artifacts must be safe outside the process before closing.
- **Leadership Retirement**:
  - Leadership panes (EM or supervisor) retire ONLY when no remaining coordination, integration, or delivery responsibilities exist. Never retire leadership prematurely at an arbitrary wave boundary.
  - Never close active user-owned panes.

---

## 2. Stage 2: Worktree Removal Gate

> [!CAUTION]
> **Worktree Removal is NOT Terminal Closure**:
> Closing a terminal pane does NOT delete its Git worktree checkout.
> Deleting a worktree checkout permanently removes the working directory from the filesystem.

### Prerequisites Before Worktree Removal:
1. **Merge / Preservation Verification**:
   - If delivered via PR: verify PR is confirmed merged on remote:
     ```bash
     gh pr view "$PR_URL" --json state -q .state | grep -iq "MERGED"
     ```
   - If delivered locally: verify candidate commit is merged into target branch:
     ```bash
     git -C "$REPO_ROOT" merge-base --is-ancestor "$CANDIDATE_SHA" "$TARGET_BRANCH"
     ```
   - If abandoned: verify decision is explicitly authorized and artifacts/diff are preserved.
2. **Cleanliness Verification**:
   - Verify zero uncommitted or untracked changes remain:
     ```bash
     test -z "$(git -C "$WORKTREE_PATH" status --porcelain)"
     ```
3. **Artifact Safety**:
   - Confirm reports, logs, and evidence are stored at the run root outside the worktree.

### Removal Command:
```bash
herdr worktree remove --workspace "$WORKSPACE_ID"
```

### Critical Invariants:
- **Refuses Dirty Trees**: `herdr worktree remove` automatically refuses if uncommitted changes exist. Never pass `--force` without explicit verification that untracked changes are disposable.
- **Preserve Ambiguous Checkouts**: Dirty or ambiguous worktrees are **retained with a recorded reason**; never force-delete.
- **No Global Zero-Worktree Prune**: Never run global worktree prune or seek a "zero worktrees on host" goal. Other branches, features, or teammates may have valid active worktrees. Touch ONLY what this task created.

---

## 3. Stage 3: Local Branch Retirement & Prune

Git refuses to delete a local branch while it is checked out in an active worktree. Therefore, local branch cleanup occurs **strictly after Stage 2**:

1. **Delete Local Branch**:
   ```bash
   git -C "$REPO_ROOT" branch -d "$BRANCH_NAME" 2>/dev/null || git -C "$REPO_ROOT" branch -D "$BRANCH_NAME"
   ```
2. **Prune Remote References**:
   ```bash
   git -C "$REPO_ROOT" remote prune origin
   ```
3. **Verify Clean Root Worktree List**:
   ```bash
   git -C "$REPO_ROOT" worktree list
   ```
   Confirm that the retired worktree path is no longer listed.
