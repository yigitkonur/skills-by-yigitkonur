# Stopped Agent Recovery, Git Locks & Manager Resumption

This reference provides procedures for unblocking hung agent sessions, recovering from Git lock contention, resolving quota exhaustion, and safely resuming crashed manager sessions without destroying active work.

---

## 1. Process Reconciliation vs. Blind Kills

> [!CAUTION]
> **Strictly Prohibited**: Executing `kill -9`, blanket `pkill -f <agent>`, or terminating processes without inventory. Blind termination corrupts Git index files, orphans POSIX semaphores, and destroys partial work.

Before restarting an agent or unblocking a pane:
1. **Query Process Tree**:
   ```bash
   herdr pane process-info --pane "$PANE_ID"
   ```
2. **Reconcile Git Locks with Target-Bound Absolute Paths**:
   If Git commands fail with `Another git process seems to be running`:
   - Discover the absolute lock file path bound to the target repository:
     ```bash
     LOCK_PATH="$(git -C "$WORKTREE_PATH" rev-parse --path-format=absolute --git-path index.lock)"
     ```
     *(Note: omitting `--path-format=absolute` from a primary clone returns a relative `.git/index.lock`, which misidentifies the target if later checked from a different cwd).*
   - Check if an active process holds the lock:
     ```bash
     lsof "$LOCK_PATH"
     ```
   - **Inspection Error vs. Absence of Lock Holder**: An empty or failed `lsof` query alone is NOT proof of safe deletion. Reconcile owned Git processes (`herdr pane process-info`, `pgrep -fl git`) and ensure inspection errors (e.g. permission limits or missing tool) are distinguished from true absence.
   - Only remove `index.lock` (`rm -f "$LOCK_PATH"`) when no owned Git processes are active in that repository tree.
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
1. **State & Conversation Inventory First**:
   Capture the exact conversation ID from Herdr session metadata *before* sending interrupts:
   ```bash
   CONV_ID="$(herdr pane get "$PANE_ID" | jq -r '.result.pane.agent_session.value // empty')"
   ```
2. **Targeted Interruption**:
   Send a surgical `ctrl+c` or `esc` to interrupt the stuck turn:
   ```bash
   herdr agent send-keys "$PANE_ID" ctrl+c
   ```
3. **Reconcile Child Processes**:
   Check `herdr pane process-info`: Escape or turn interruption may leave background child processes running. Confirm whether child processes need to finish or be stopped.
4. **Preserve User Pause**:
   If the session was explicitly paused by the human user, do NOT resume without authorization.
5. **Exact Conversation Resume**:
   Reconnect to the exact conversation history using its explicit ID:
   ```bash
   agy --conversation "$CONV_ID"
   ```
   **Never use `--continue`**, which attaches to the most recent global conversation and contaminates state.
6. **Continuation vs. Blocker Rule**:
   - If actual tool progress resumes, continue the task.
   - If quota exhaustion (429) recurs, **stop**. Do not enter an infinite retry loop. Two equivalent failures halt retries. Escalate a concrete blocker to the supervisor.

---

## 4. Manager Session Recovery & Selective Resume

If an Engineering Manager (EM) session crashes or disconnects during a Mode 3 Managed Mission:

1. **Relinquishment Proof**:
   Confirm that the previous manager process has terminated (PID absent, socket unlinked) before provisioning a replacement manager.
2. **Selective State & Report Intake**:
   - The replacement manager reads `state.yaml` at `<RUN_ROOT>/state.yaml`.
   - Read active assignments, current DAG wave, dedupe index, and unresolved effects.
   - **Do NOT re-read all historical completed reports**: Intake only reports for active or un-checkpointed tasks to conserve context.
3. **Structural Shape Verification**:
   Verify that `state.yaml` satisfies required top-level schema keys:
   - `mission_id`, `status`, `manager` (coordinates), `cto` (coordinates), `report_root`, `assignments`, `decisions`.
   - If `state.yaml` is structurally malformed or corrupted, restore from the last verified checkpoint before resuming.
4. **Worker Preservation**:
   - Query all live agent panes across workspaces via `herdr agent list`.
   - **Adopt healthy running workers**: Do NOT terminate, restart, or duplicate active worker agents that are making steady progress in their worktrees. Map their live pane IDs to existing task assignments.
5. **Re-Registration**:
   Register the new manager handle with updated coordinates (`pane_id`, `tab_id`), incrementing attempt counters where applicable while preserving mission history.
6. **Authority Boundary**:
   Assigned task executors do NOT infer managerial authority, coordinator roles, or nested subagent spawning without an explicit scope grant and verified native tool support.

---

## 5. Shared Herdr Server Safety Invariant

- **Never Stop the Server in an Active Session**:
  `herdr server stop` stops the server daemon for ALL sessions, closing every open pane and terminating all running agents on the machine.
- **Never Kill Daemon with `kill -9`**:
  If socket communication hangs, inspect `herdr status client` and `herdr status server`. Use isolated test sessions (`herdr --session test`) for experimental daemon debugging.
