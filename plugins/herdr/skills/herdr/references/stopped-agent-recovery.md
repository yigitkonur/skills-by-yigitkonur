# Recovery & Resumption

## 1. Process Reconciliation vs. Blind Kills
**Strictly prohibited**: Executing `kill -9`, blanket `pkill -f <agent>`. Blind termination corrupts Git index files and orphans locks.

Before restarting an agent:
1. **Query Processes**: `herdr pane process-info --pane <PANE_ID>`
2. **Reconcile Git Locks**:
   Discover dynamic lock path (`git -C "$WORKTREE_PATH" rev-parse --git-path index.lock`).
   Check if actively held with `lsof`. Only remove if unheld and prior processes are dead.

## 2. Restarting Crashed Agent Sessions
**Never execute `herdr agent start` over a live TUI.**
1. Verify the pane is at a shell prompt (`$`, `%`): `herdr pane read --source visible --lines 5 <PANE_ID>`
2. Launch the agent using the configured model.

## 3. Quota Recovery (Section 4.6)
When an agent exhausts its quota:
1. Interrupt the specific agent gracefully with `Ctrl+C`. Do not loop on an exhausted tier.
2. Reconnect to the exact conversation history using its ID, explicitly using `--conversation` (do NOT use `--continue`):
   ```bash
   agy --conversation "$AGY_CONVERSATION_ID"
   ```
3. Send a single prompt message: `"continue"`

## 4. Manager Session Recovery
If the EM crashes:
1. Prove relinquishment.
2. Read `state.yaml` and immutable reports. Verify structured YAML shapes (no swallowed blocks).
3. Do NOT restart healthy worker lanes that are actively synthesizing code. Re-establish observer handles.

## 5. Bounded Recovery Rule
If two consecutive recovery attempts for the same failure mode fail to advance the task, **stop automated retries**. Publish a blocker report with `status: blocked` and notify the supervisor without `--wait`.
