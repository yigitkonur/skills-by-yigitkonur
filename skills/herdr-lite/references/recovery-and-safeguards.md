# Recovery, Quota & Worktree Safeguards

This reference provides recovery procedures for hung sessions, quota limits, stuck Git locks, and safe worktree cleanup in Herdr-Lite.

---

## 1. Process Reconciliation vs. Blind Kills

**Strictly Prohibited**: Executing `kill -9`, blanket `pkill -f`, or killing processes without inspecting state. Blind kills orphan Git locks (`index.lock`), corrupt shared PTY buffers, and destroy work in progress.

Before restarting or unblocking a pane:
1. **Query Active Processes**:
   ```bash
   herdr pane process-info --pane "$PANE_ID"
   ```
2. **Reconcile Git Locks**:
   If Git commands fail with `Another git process seems to be running`:
   - Discover the lock file path:
     ```bash
     LOCK_PATH="$(git -C "$WORKTREE_PATH" rev-parse --git-path index.lock)"
     ```
   - Check if an active process holds the lock:
     ```bash
     lsof "$LOCK_PATH"
     ```
   - Only remove `index.lock` if `lsof` shows no active process holding it and prior pane processes are confirmed terminated.

---

## 2. Quota & Hang Recovery Safeguards

When an agent encounters genuine quota exhaustion or a verified hard hang:

1. **Targeted Interruption**:
   Send a surgical `ctrl+c` to interrupt the stuck agent turn:
   ```bash
   herdr agent send-keys "$PANE_ID" ctrl+c
   ```
2. **State Inventory**:
   Capture the exact AGY conversation ID from Herdr session metadata:
   ```bash
   AGY_CONVERSATION_ID="$(herdr pane get --pane "$PANE_ID" | jq -r '.result.pane.agent_session.value')"
   ```
3. **Pre-Resume Verification**:
   Confirm the process has terminated and the pane rests at a clean shell prompt (`$`, `%`):
   ```bash
   herdr pane read --source visible --lines 5 "$PANE_ID"
   ```
4. **Exact Conversation Resume**:
   Reconnect to the exact conversation history using its explicit ID:
   ```bash
   agy --conversation "$AGY_CONVERSATION_ID"
   ```
   > [!CAUTION]
   > **Never use `--continue`**. `--continue` attaches to the globally most recent conversation and can cross-contaminate lane state across parallel worktrees.
5. **Single Continuation Prompt**:
   Verify the composer is input-ready, then transmit **exactly ONE** prompt message: `"continue"`.
6. **Quota Stop Rule**:
   If the quota failure returns immediately, **stop**. Do not loop or retry. Escalate to the developer or switch to an authorized alternative model tier.

---

## 3. Worktree Removal Gate & Pane Retirement

Resource cleanup follows two strict gates:

### Gate A: Pane & Workspace Retirement
- Close the reviewer and implementer resources as soon as PR review is approved:
  ```bash
  herdr tab close "$REV_TAB_ID"
  herdr workspace close "$WORKSPACE_ID"
  ```
- Alternatively, close individual panes:
  ```bash
  herdr pane close "$REV_PANE_ID"
  herdr pane close "$IMPL_PANE_ID"
  ```

### Gate B: Worktree Removal Gate (`git worktree remove`)
- Worktree cleanup is a separate engineering gate; closing panes or workspaces does not authorize deleting dirty checkouts.
- **Cleanliness Check**:
  ```bash
  DIRTY_FILES="$(git -C "$WORKTREE_PATH" status --porcelain)"
  if [ -n "$DIRTY_FILES" ]; then
    echo "ERROR: Worktree is dirty. Preserving for review:"
    echo "$DIRTY_FILES"
    exit 1
  fi
  ```
- **Removal**:
  ```bash
  git worktree remove "$WORKTREE_PATH"
  ```
- **Branch Retirement & Prune**:
  Once the worktree is unlinked, delete the local merged branch and prune remotes:
  ```bash
  git branch -D "$BRANCH_NAME"
  git remote prune origin
  ```
- *No Force Deletion*: `git worktree remove --force` is strictly prohibited without explicit human authorization.
