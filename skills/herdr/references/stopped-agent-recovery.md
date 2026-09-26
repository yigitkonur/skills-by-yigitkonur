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
   - **Comprehensive Process & Lock Verification**:
     An empty or failed `lsof` query alone is NOT proof of safe deletion:
     - Check for BOTH owned and unowned live Git processes touching the repository tree (`herdr pane process-info`, `pgrep -fl git`, `ps aux | grep git`).
     - Any unowned live Git process in the same repository, unresolved process ownership, or inspection error (e.g. permission limits or missing diagnostic tools) requires lock preservation.
     - Verify that the lock file belongs to the exact target repository checkout, is demonstrably stale and unheld, and no related processes are actively writing to it.
     - Only when the lock is proven stale, unheld, and zero live Git processes (owned or unowned) are active in that repository tree may `index.lock` be removed (`rm -f "$LOCK_PATH"`).
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

Keypress and composer handling routes strictly to the canonical procedure defined in [harness-antigravity.md](harness-antigravity.md):
1. **Inventory Identity, Modals & Pending Effects First**:
   - Check live coordinates and identity: `herdr pane current --current`.
   - Inspect visible screen state: `herdr agent read "$PANE_ID" --source visible --lines 25`.
   - **Modal Resolution**: If the agent is blocked on a trust dialog or question modal, do NOT send interrupts (`esc`/`ctrl+c`); resolve the modal via its visible choice.
   - Check for unfinalized `.partial` reports or active mutations.
2. **Preserve Input-Ready Same-Session Continuation**:
   - If the agent's composer is visible and resting in an input-ready state (`Prompt:`, `❯`), do NOT restart the TUI or interrupt the session. Deliver prompts or follow-ups directly to the active composer.
3. **Targeted Interruption via Canonical Safety Gates**:
   - If a genuine hang or 429 stall is established outside mutating boundaries, follow the staged safety sequence in [harness-antigravity.md](harness-antigravity.md) (single targeted `esc` or `ctrl+c`).
   - Reconcile child processes via `herdr pane process-info --pane "$PANE_ID"`.
4. **Preserve User Pause**:
   - If the session was explicitly paused by the human user, **all recovery prompts and new dispatches are strictly prohibited** until an explicit resume signal is received.
5. **Exact Session Resume Gate**:
   - Verify the exact session ID from Herdr session metadata:
     ```bash
     CONV_ID="$(herdr pane get "$PANE_ID" | jq -r '.result.pane.agent_session.value // empty')"
     ```
   - **Missing Session ID is a Blocker**: If the conversation ID cannot be verified, recovery must HALT. Never guess an ID, and **never use `--continue`** (which attaches to the most recent global conversation and contaminates state).
   - **TUI Exit Verification Before Restart**: Launch a resumed TUI (`agy --conversation "$CONV_ID" ...`) **only after the previous TUI has actually exited** and the pane is confirmed resting cleanly at a shell prompt (`$ `, `% `).
6. **Bounded Recovery Rule (Rule of Two)**:
   - If tool progress resumes, proceed normally.
   - If quota exhaustion (429) or hard stalls recur after recovery, **halt immediately**. Two equivalent failures exhaust the recovery budget. Escalate a concrete blocker with captured logs to the supervisor.

---

## 4. Manager Session Recovery & Selective Resume

If an Engineering Manager (EM) session crashes or disconnects during a Mode 3 Managed Mission:

1. **Relinquishment Proof**:
   Confirm that the previous manager's exact process and session have relinquished ownership (process terminated, PID absent, no active pane operations). Do NOT require disappearance or unlinking of the shared Herdr socket (`~/.config/herdr/herdr.sock`), as the manager does not own the server socket.
2. **Selective State & Report Intake**:
   - The replacement manager reads `state.yaml` at `<RUN_ROOT>/state.yaml`.
   - Restore manager checkpoint shape, dedupe index, unresolved pending effects, and preserved paused state.
   - **Corrupted Checkpoint Preservation**: If `state.yaml` is structurally malformed or corrupted, preserve the corrupted file first (`cp "$RUN_ROOT/state.yaml" "$RUN_ROOT/state.yaml.corrupt-$(date +%s)"`) before restoring from the last verified clean checkpoint. Never overwrite or clobber corrupted state without preservation.
   - **Conserve Context**: Intake only reports for active or un-checkpointed tasks; do NOT re-read all historical completed reports.
3. **Supervisor-Controlled Handover & Attempt Counters**:
   - The authorized supervisor (Root / Controller) controls manager identity and attempt handover.
   - Replaced managers or unregistered task producers do NOT increment attempt counters or register coordinates on their own.
4. **Worker Preservation**:
   - Query all live agent panes across workspaces via `herdr agent list`.
   - **Adopt Healthy Running Workers**: Do NOT terminate, restart, or duplicate active worker agents making steady progress in their worktrees. Map their live pane IDs to existing task assignments.
5. **Authority Boundary**:
   Assigned task executors do NOT infer managerial authority, coordinator roles, or nested subagent spawning without an explicit scope grant and verified native tool support.

---

## 5. Shared Herdr Server Safety Invariant

- **Never Stop the Server in an Active Session**:
  `herdr server stop` stops the server daemon for ALL sessions, closing every open pane and terminating all running agents on the machine.
- **Never Kill Daemon with `kill -9`**:
  If socket communication hangs, inspect `herdr status client` and `herdr status server`. Use isolated test sessions (`herdr --session test`) for experimental daemon debugging.
