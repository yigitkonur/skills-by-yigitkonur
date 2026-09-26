# Antigravity (AGY) Harness Physics & Queue Management

This reference defines operational physics, turn queue dynamics, manager intake sequences, pre-Escape safety gates, modal handling, child process reconciliation, and recovery protocols specific to the Antigravity (AGY) CLI runtime (scoped to observations on AGY CLI 1.2.11) within Herdr.

---

## 1. Core Queue Prevention (The Primary Design)

Queue prevention is the primary architecture; Escape recovery is a secondary fallback. Preventing queue stalls eliminates the need for repeated interruptions:

### 1.1 The Manager Turn Sequence
To prevent incoming report notices from queuing behind long managerial operations:
1. **Sweep Queued Notices & Unconsumed Reports First**:
   Every management turn must begin by sweeping queued notices in the terminal and scanning `report_root` for newly published unconsumed reports before initiating status polling, log reading, or deep investigations.
2. **Short, Complete Management Turns**:
   Keep supervisory turns bounded to a complete cycle: **Intake $\to$ Decision $\to$ Dispatch $\to$ Checkpoint (`state.yaml`) $\to$ Yield**. Intake must be allowed to verify multiple queued notices and reports coherently without an arbitrary tool-count cap, while keeping long diagnostics and builds delegated.
3. **Delegate Lengthy Diagnostics & Build Waits**:
   Never tie up a manager session running long builds, test suites, or exhaustive diagnostic investigations. Delegate diagnostics and build waits to task workers or dedicated diagnostic lanes.
4. **Prompt Producer Yield**:
   Task workers and report producers must yield immediately after publishing a handback report and transmitting their notice.

### 1.2 Explicit Wakeup Ownership Hierarchy
- **Root / Controller** is the sole wakeup owner for the Engineering Manager (EM).
- **The EM / Direct Parent** is the sole wakeup owner for its assigned task workers.
- **Single Wakeup Owner Invariant**: Exactly ONE supervisor is authorized to wake or nudge an AGY session. Multiple senders must never send Escape or prompts concurrently.
- **No Routine ACK Cascades**: Never send unnecessary acknowledgment messages ("ACK of ACK") that inflate turn queues and trigger starvation.

---

## 2. AGY Turn Queue Dynamics (CLI 1.2.11)

In the Antigravity interactive TUI:
- **Queued Input During Active Turns**: If text followed by Enter is submitted to an AGY pane while the agent is in an active turn (`working`), AGY buffers the message in an internal visible queue until the current turn, subagent run, or tool call sequence finishes.
- **Wait for Idle When Possible**: Whenever workflow permits, wait for AGY to reach `idle` before submitting new prompts. Injecting prompts while an agent is writing files or invoking tools can interleave input before the agent is ready.

---

## 3. Staged-After-Escape Recovery Protocol

This protocol is invoked ONLY when an AGY queue stalls during an extended active turn with queued messages. It is **never** used for a modal-blocked agent, an idle agent, or during mutating operations.

```
[ Queue Stalled During Active Turn ]
                 │
                 ▼
[ Step 1: Pre-Escape Inspection & Safety Gates ]
  • Inspect live identity (herdr pane current --current)
  • Inspect visible screen (herdr agent read --source visible)
  • Is agent blocked on a modal? ──► YES ──► DO NOT SEND ESCAPE! Resolve modal via visible choice.
  • Are Git mutations / writes underway? ─► YES ─► Wait for safe boundary.
                 │ (Clean safe boundary confirmed)
                 ▼
[ Step 2: Send ONE Targeted Escape ]
  herdr agent send-keys "$PANE_ID" esc
                 │
                 ▼
[ Step 3: Inspect Visible State ]
  herdr agent read "$PANE_ID" --source visible --lines 25
                 │
        ┌────────┴──────────────────────────────┐
        ▼                                        ▼
[ Exact Message Staged in Composer ]     [ Messages Already Consumed ]
  Screen shows native Interrupted notice    Verify recorded receipt IDs in
  and promoted queued message text.        state.yaml / disk artifacts.
        │                                        │
        ▼                                        ▼
[ Step 4: Submit Existing Text ]         Add nothing! Do NOT send Enter
  herdr agent send-keys "$PANE_ID" enter  or paste duplicate prompts.
  (Submit EXISTING text once; NO duplicate paste!)
```

### 3.1 Pre-Escape Safety Gates (Must Precede Any Key)
1. **Verify Session Identity**:
   Confirm caller coordinates and target pane via `herdr pane current --current`. Ensure you are targeting the verified AGY pane.
2. **Inspect Visible Buffer**:
   ```bash
   herdr agent read "$PANE_ID" --source visible --lines 25
   ```
3. **Safety Check — Modals**:
   If the agent is in state `blocked` or displays a modal/dialog (e.g. project trust prompt, question menu, permission prompt), **DO NOT SEND ESCAPE**. Sending Escape to a modal can dismiss the dialog unexpectedly or abort startup. Resolve the modal based on visible authorized choices.
4. **Safety Check — Active Mutations**:
   If `herdr pane process-info` or visible output shows active file writes, Git operations (`git commit`, `git rebase`), compiler execution, or package installation, **hold Escape**. Wait for a safe boundary before sending any key. Blind keys during modal display or mutation are strictly prohibited.
5. **Preserve User Pause**:
   If the session was explicitly paused by the human user, do NOT send Escape or prompts without explicit authorization to unpause.

### 3.2 Execution & Post-Escape State Branching
At a safe boundary, the single designated wakeup owner proceeds:
1. **Send Exactly ONE Targeted Escape**:
   ```bash
   herdr agent send-keys "$PANE_ID" esc
   ```
2. **Inspect Visible State**:
   ```bash
   herdr agent read "$PANE_ID" --source visible --lines 25
   ```
3. **Branch Based on Observed State**:
   - **Case A: Exact Queued Message Staged in Composer**:
     Escape interrupted the cognitive turn and promoted the queued message into the active composer (verified by an `[Interrupted]` notice on screen). Verify that the staged text matches the intended message. Submit the **EXISTING** text with exactly ONE Enter:
     ```bash
     herdr agent send-keys "$PANE_ID" enter
     ```
     **Never paste the message a second time**. Duplicating the paste corrupts the prompt buffer and submits duplicate prompts.
   - **Case B: Messages Already Consumed**:
     Do NOT assume an empty queue or working state alone proves consumption. Verify actual consumed receipt IDs or checkpoint effects (e.g. recorded reports in `state.yaml` or on disk). If consumed, **send nothing**.
   - **Case C: Composer Empty & Input-Ready with Unconsumed IDs**:
     If the queue was cleared or state is uncertain, reconstruct missing IDs from durable disk artifacts and submit one concise notice:
     ```bash
     herdr agent prompt "$PANE_ID" "Consume existing report <REPORT_ID> at <PATH>"
     ```

### 3.3 Child Subprocess vs. Cognitive Turn Disconnection
Captured native evidence (verified via `probe-agy-controller-verification.json` on AGY CLI 1.2.11):
- Sending Escape interrupts the cognitive LLM turn. However, surviving child processes (e.g. background bash scripts, sleep commands, compiler invocations) may continue executing to exit status $0$.
- In probe verification, the agent's internal self-summary erroneously reported zero interruptions because its background child process completed cleanly, yet captured native screen output proved that the cognitive LLM turn was interrupted and required Enter submission.
- **Rule**: Do NOT conflate child process survival with cognitive turn continuity, and do NOT equate child exit $0$ with uninterrupted agent flow. Always inspect both `herdr pane process-info` and visible buffer output to reconcile process and cognitive state.

---

## 4. Project Trust Modal Resolution

When AGY starts inside a newly provisioned Git worktree directory, it presents an interactive project trust confirmation prompt:

```bash
herdr agent read "$PANE_ID" --source visible --lines 15
```

1. **Inspect Visible Options**: Read the options displayed on the terminal screen (e.g. `Trust folder`, `Allow once`, `Exit`).
2. **Targeted Selection**:
   - Navigate to the authorized selection using `herdr agent send-keys "$PANE_ID" <up|down>`.
   - Confirm the selection using `herdr agent send-keys "$PANE_ID" enter`.
3. **Never Blindly Send Enter**: Sending Enter blindly on launch risks submitting blank prompts or selecting unintended options if the composer is already active.
