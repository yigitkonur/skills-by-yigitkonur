# Recovery, Resumption & Quota Safeguards

## 1. Process Reconciliation vs. Blind Kills

**Strictly prohibited**: Executing `kill -9`, blanket `pkill -f <agent>`, or terminating processes without inventory. Blind termination corrupts Git index files, orphans POSIX semaphores, and destroys partial work.

Before restarting an agent or retrying a task:
1. **Query Processes**: `herdr pane process-info --pane <PANE_ID>`
2. **Reconcile Git Locks Across Worktrees**:
   Discover the dynamic lock path (`git -C "$WORKTREE_PATH" rev-parse --git-path index.lock`). Check if actively held with `lsof`. Only remove if unheld and prior pane processes are dead.
3. **Reconcile Pending Files**: Check for unfinalized `.partial` reports before removing or restarting.

## 2. Safe Restart of Crashed Agent Sessions

**Never execute `herdr agent start` over a live TUI.**
1. Verify the pane is resting cleanly at a shell prompt (`$`, `%`):
   `herdr pane read --source visible --lines 5 <PANE_ID>`
2. Confirm previous processes have fully terminated via `herdr pane process-info --pane <PANE_ID>`.
3. Launch the agent with explicitly configured model/effort.

## 3. Quota & Hang Recovery Safeguards (§4.6)

Quota or hang recovery is invoked **only for an observed quota exhaustion or established stall**, never for a live spinner, active thinking turn, or brief silence alone.

When an agent encounters genuine quota exhaustion or a verified hard hang:
1. **Targeted Interruption**: Send a surgical `ctrl+c` to interrupt the stuck agent turn. Do not issue blanket kills.
2. **State & Conversation Inventory**: Record the exact AGY conversation ID (not merely pane/terminal), isolated worktree path, verified model, and any pending operations or uncommitted edits.
3. **Pre-Resume Verification**: Verify actual foreground process state and confirm no live TUI remains before resuming.
4. **Exact Conversation Resume**: Reconnect to the exact conversation history using its explicit ID:
   ```bash
   agy --conversation "$AGY_CONVERSATION_ID"
   ```
   **Never use `--continue`**, which attaches to the most recent conversation and can cross-contaminate lane state.
5. **Composer Verification & Single Prompt**: Verify the exact conversation ID and confirm an input-ready composer before transmitting **exactly ONE** prompt message: `"continue"`.
6. **Continuation vs. Blocker Rule**:
   - If actual tool progress and turns resume, continue the task.
   - If the same quota failure returns immediately, **stop**. Do not enter a retry loop, claim a quota reset, or guess unassigned model tiers. Either switch to an explicitly authorized available model tier or escalate a concrete capacity blocker to the manager.

## 4. Manager Session Recovery & Selective Resume

If the Engineering Manager session crashes or disconnects:
1. **Relinquishment Proof**: Confirm the previous manager process has actually terminated before initializing a replacement.
2. **Selective State & Report Intake**: Read the compact active checkpoint (`state.yaml`), active ownership, dedupe index, and pending effects. Read only relevant unconsumed or suspect reports from disk; **do not require re-reading all historical reports**.
3. **Structural Shape Verification**: Check expected top-level keys (`mission_id`, `status`, `manager`, `cto`, `report_root`, `assignments`, `decisions`) and structured mappings. Verify keys were not swallowed into multiline strings by indentation errors.
4. **Preserve Healthy Workers**: Do NOT terminate or restart healthy worker lanes that are actively synthesizing code. Re-establish observer handles.
5. **Attempts & Re-registration**: Keep manager attempts and registered identities honest; do not advance tasks on ambiguous provenance.

## 5. Bounded Recovery Rule & Blocker Escalation

- **Rule of Two Failures**: If two consecutive recovery attempts for the same failure mode fail to advance the task, **stop automated retries**.
- **Evidence Capture & Blocker Report**: Capture recent diagnostic output (`herdr agent read <TARGET> --source recent-unwrapped --lines 100`) and publish an immutable blocker report (`status: blocked`, `requested_action: unblock_decision`).
- **Notify Supervisor**: Dispatch native notice without `--wait` to the discovered manager return pane.
