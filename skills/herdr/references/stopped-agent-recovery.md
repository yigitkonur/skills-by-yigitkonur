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
1. **Check Pause State First**:
   If the session or repository was explicitly paused by the human user, **all restarts, launches, prompts, and mutating operations are strictly prohibited** until an explicit resume signal is received. Read-only process reconciliation (`herdr pane process-info`) is permitted to inspect state, but does NOT authorize restarting the agent.
2. **Verify Clean Shell Prompt**:
   Ensure the pane is resting cleanly at a shell prompt (`$ `, `% `):
   ```bash
   herdr pane read --source visible --lines 5 "$PANE_ID"
   ```
3. **Confirm Process Termination**:
   Verify prior agent processes have fully terminated via `herdr pane process-info --pane "$PANE_ID"`.
4. **Launch with Explicit Configuration**:
   Restart the agent with explicit model and effort flags:
   ```bash
   herdr agent start <NAME> --kind <KIND> --pane "$PANE_ID" -- [AGENT_ARGS]...
   ```

---

## 3. Quota Exhaustion & Stalled Turn Recovery

Quota or hang recovery is invoked **only for observed quota exhaustion (429) or established stalls**, never for an active thinking turn, live tool execution, or brief silence.

1. **Check Pause State First**:
   If the session was explicitly paused by the human user, **all recovery prompts, keypresses (`esc`/`ctrl+c`), modal selections, and new dispatches are strictly prohibited** until an explicit resume signal is received. Read-only inspection (`herdr pane read`, `herdr pane get`) is permitted to assess state, but does NOT authorize recovery actions or key injection.
2. **Target Identity & State Inspection**:
   - **Target vs. Caller**: `herdr pane current --current` identifies the *caller* pane, NOT the target agent. Verify the target agent explicitly via `herdr pane get "$TARGET_PANE"`, `herdr agent get "$TARGET_AGENT"`, and `herdr pane process-info --pane "$TARGET_PANE"`, cross-checking against registered assignment metadata. A stale or detached caller blocks focus fallback; an explicit, separately verified authorized target can still be observed.
   - Inspect target visible screen: `herdr agent read "$TARGET_PANE" --source visible --lines 25`.
   - **Modal Resolution**: If the target agent is blocked on a trust dialog or question modal, do NOT send interrupts (`esc`/`ctrl+c`); resolve the modal via its visible authorized option.
   - Check for unfinalized `.partial` reports or active mutations.
3. **Preserve Input-Ready Same-Session Continuation**:
   - If the target agent's composer is visible and resting in an input-ready state (`Prompt:`, `❯`), do NOT restart the TUI or interrupt the session. Deliver prompts or follow-ups directly to the active composer.
4. **Targeted Interruption via Harness-Specific Gates**:
   - If a genuine hang or 429 stall is established outside mutating boundaries, dispatch recovery to the canonical harness reference:
     - **Antigravity (AGY)**: Follow [harness-antigravity.md](harness-antigravity.md) (single targeted `esc` or `ctrl+c`, visible check, single Enter on promoted prompt, child process reconciliation).
     - **Codex**: Follow [harness-codex.md](harness-codex.md) (single pane-targeted prompt, scrollback receipt check, and no AGY Escape mechanics).
     - **Other Harnesses**: Follow [harness-other.md](harness-other.md).
   - Reconcile child processes via `herdr pane process-info --pane "$TARGET_PANE"`.
5. **Exact Session Resume Gate (Harness-Specific)**:
   - If the previous TUI exited or must be relaunched, verify the exact session ID from Herdr session metadata:
     ```bash
     CONV_ID="$(herdr pane get "$TARGET_PANE" | jq -r '.result.pane.agent_session.value // empty')"
     ```
   - **Missing Session ID is a Blocker**: If the session ID cannot be verified, recovery must HALT. Never guess an ID, and **never use `--continue`** (which attaches to the most recent global conversation and contaminates state).
   - **TUI Exit Verification Before Restart**: Launch a resumed session (e.g. `agy --conversation "$CONV_ID"` for AGY) **only after the previous TUI has actually exited** and the pane is confirmed resting cleanly at a shell prompt (`$ `, `% `). AGY conversation syntax is strictly AGY-specific and must never be applied to Codex or other harnesses.
6. **Bounded Recovery Rule (Rule of Two)**:
   - If tool progress resumes, proceed normally.
   - If quota exhaustion (429) or hard stalls recur after recovery, **halt immediately**. Two equivalent failures exhaust the recovery budget. Escalate a concrete blocker with captured logs to the supervisor.

---

## 4. Manager Session Recovery & Selective Resume

If an Engineering Manager (EM) session crashes or disconnects during a Mode 3 Managed Mission:

1. **Check Pause State First**:
   If a user pause is active, replacement manager provisioning, recovery prompts, and new task dispatches are strictly prohibited until explicit resume is authorized. Read-only state inspection of `state.yaml` is permitted.
2. **Relinquishment Proof**:
   Confirm that the previous manager's exact process and session have relinquished ownership (process terminated, PID absent, no active pane operations). Do NOT require disappearance or unlinking of the shared Herdr socket (`~/.config/herdr/herdr.sock`), as the manager does not own the server socket.
3. **Structural Shape & Key Validation (Detect Swallowed Keys)**:
   Before acting on `<RUN_ROOT>/state.yaml`, perform concrete structural shape verification:
   - **Top-Level Required Keys**: Must contain `mission_id`, `status`, `manager`, `cto`, `report_root`, `assignments`, and `decisions`.
   - **Required Mapping Types**: `manager`, `cto`, and `assignments` must be mappings/dictionaries, not string scalars.
   - **Multiline Scalar Check**: Verify keys were not swallowed into an unquoted or improperly indented multiline scalar (e.g., ensure `assignments:` appears as an unindented top-level key, not indented under a preceding block scalar).
   - **Syntax & Shape Verification Command**:
     ```bash
     python3 -c '
     import sys, yaml
     state_path = sys.argv[1]
     try:
         with open(state_path, "r", encoding="utf-8") as f:
             data = yaml.safe_load(f)
     except Exception:
         sys.exit(1)
     req = ["mission_id", "status", "manager", "cto", "report_root", "assignments", "decisions"]
     if not isinstance(data, dict) or not all(k in data for k in req):
         sys.exit(2)
     if not isinstance(data.get("assignments"), dict) or not isinstance(data.get("manager"), dict) or not isinstance(data.get("cto"), dict):
         sys.exit(3)
     ' "$RUN_ROOT/state.yaml"
     ```
   - **Preserve Corrupt Evidence First**: If `state.yaml` is structurally malformed or corrupted, preserve the corrupted file immediately (`cp "$RUN_ROOT/state.yaml" "$RUN_ROOT/state.yaml.corrupt-$(date +%s)"`) before restoring from the last verified clean checkpoint. Never overwrite or clobber corrupted state without preservation.
4. **Selective State & Report Intake**:
   - Restore manager checkpoint shape, dedupe index, unresolved pending effects, and preserved paused state.
   - **Conserve Context**: Intake only reports for active or un-checkpointed tasks; do NOT re-read all historical completed reports.
5. **Supervisor-Controlled Handover & Attempt Counters**:
   - The authorized supervisor (Root / Controller) controls manager identity and attempt handover.
   - Replaced managers or unregistered task producers do NOT increment attempt counters or register coordinates on their own.
6. **Worker Preservation**:
   - Query all live agent panes across workspaces via `herdr agent list`.
   - **Adopt Healthy Running Workers**: Do NOT terminate, restart, or duplicate active worker agents making steady progress in their worktrees. Map their live pane IDs to existing task assignments.
7. **Authority Boundary**:
   Assigned task executors do NOT infer managerial authority, coordinator roles, or nested subagent spawning without an explicit scope grant and verified native tool support.

---

## 5. Shared Herdr Server Safety Invariant

- **Never Stop the Server in an Active Session**:
  `herdr server stop` stops the server daemon for ALL sessions, closing every open pane and terminating all running agents on the machine.
- **Never Kill Daemon with `kill -9`**:
  If socket communication hangs, inspect `herdr status client` and `herdr status server`. Use isolated test sessions (`herdr --session test`) for experimental daemon debugging.
