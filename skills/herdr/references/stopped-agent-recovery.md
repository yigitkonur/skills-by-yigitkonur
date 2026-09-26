# Stopped Agent Recovery, Git Locks & Quota Safeguards

This reference provides procedures for unblocking hung agent sessions, recovering from Git lock contention, resolving quota exhaustion, and safely restarting processes without destroying active work.

---

## 1. Process Reconciliation vs. Blind Kills

> [!CAUTION]
> **Strictly Prohibited**: Executing `kill -9`, blanket `pkill -f <agent>`, or terminating processes without inventory. Blind termination corrupts Git index files, orphans POSIX semaphores, and destroys partial work.

Before restarting an agent or unblocking a pane:
1. **Query Process Tree**:
   ```bash
   herdr pane process-info --pane "$PANE_ID"
   ```
2. **Reconcile Git Locks Across Worktrees**:
   If Git commands fail with `Another git process seems to be running`:
   - Discover the lock file path dynamically:
     ```bash
     LOCK_PATH="$(git -C "$WORKTREE_PATH" rev-parse --git-path index.lock)"
     ```
   - Check if an active process currently holds the lock:
     ```bash
     lsof "$LOCK_PATH"
     ```
   - Only remove `index.lock` (`rm -f "$LOCK_PATH"`) if `lsof` confirms no active process holds it and prior pane processes are dead.
3. **Reconcile Pending Files**:
   Check for unfinalized `.partial` report files before restarting or cleaning up.

---

## 2. Safe Restart of Crashed Agent Sessions

**Never execute `herdr agent start` over a live TUI.**
1. **Verify Clean Shell Prompt**:
   Ensure the pane is resting cleanly at a shell prompt (`$ `, `% `):
   ```bash
   herdr pane read --source visible --lines 5 "$PANE_ID"
   ```
2. **Confirm Process Termination**:
   Verify prior agent processes have fully terminated via `herdr pane process-info --pane "$PANE_ID"`.
3. **Launch with Explicit Configuration**:
   Restart the agent with explicit model and effort flags:
   ```bash
   herdr agent start <NAME> --kind <KIND> --pane "$PANE_ID" -- [AGENT_ARGS]...
   ```

---

## 3. Quota Exhaustion & Stalled Turn Recovery

Quota or hang recovery is invoked **only for observed quota exhaustion (429) or established stalls**, never for an active thinking turn, live tool execution, or brief silence.

When an agent encounters genuine quota exhaustion or a verified hard hang:
1. **Targeted Interruption**:
   Send a surgical `ctrl+c` or `esc` to interrupt the stuck turn:
   ```bash
   herdr agent send-keys "$PANE_ID" ctrl+c
   ```
2. **State & Conversation Inventory**:
   Capture the exact conversation ID from Herdr session metadata:
   ```bash
   CONV_ID="$(herdr pane get "$PANE_ID" | jq -r '.result.pane.agent_session.value // empty')"
   ```
3. **Pre-Resume Verification**:
   Verify actual foreground process state and confirm no live TUI remains before resuming.
4. **Exact Conversation Resume**:
   Reconnect to the exact conversation history using its explicit ID:
   ```bash
   agy --conversation "$CONV_ID"
   ```
   **Never use `--continue`**, which attaches to the most recent global conversation and contaminates state.
5. **Single Continuation Prompt**:
   Verify an input-ready composer before transmitting exactly ONE prompt message: `"continue"`.
6. **Continuation vs. Blocker Rule**:
   - If actual tool progress and turns resume, continue the task.
   - If the same quota failure returns immediately, **stop**. Do not enter an infinite retry loop. Two equivalent failures halt retries. Escalate a concrete blocker to the supervisor.

---

## 4. Shared Herdr Server Safety Invariant

- **Never Stop the Server in an Active Session**:
  `herdr server stop` stops the server daemon for ALL sessions, closing every open pane and terminating all running agents on the machine.
- **Never Kill Daemon with `kill -9`**:
  If socket communication hangs, inspect `herdr status client` and `herdr status server`. Use isolated test sessions (`herdr --session test`) for experimental daemon debugging.
