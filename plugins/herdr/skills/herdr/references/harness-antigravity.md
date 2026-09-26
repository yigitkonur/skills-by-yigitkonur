# Antigravity (AGY) Harness Physics

This reference defines operational physics, turn queue dynamics, pre-Escape safety gates, modal handling, child process reconciliation, and recovery protocols specific to the Antigravity (AGY) CLI runtime within Herdr.

---

## 1. AGY Turn Queue Dynamics

In the Antigravity interactive TUI:
- **Queued Input During Active Turns**: If text followed by Enter is submitted to an AGY pane while the agent is in an active turn (`working`), AGY does NOT immediately execute the text. Instead, it buffers the message in an internal visible queue until the current turn, subagent run, or tool call chain finishes.
- **Single Wakeup Owner Invariant**: Exactly ONE supervisor or controller is authorized to wake or nudge an AGY session. Multiple senders broadcasting keys or prompts create unresolvable race conditions and duplicate prompt staging.
- **Wait for Idle When Possible**: Whenever workflow permits, wait for AGY to reach `idle` before submitting new prompts. Injecting prompts while the agent is writing files or invoking tools risks composer corruption.

---

## 2. Staged-After-Escape Recovery Protocol

This protocol is invoked ONLY when an AGY queue stalls during an extended active turn with queued messages. It is **never** used for a modal-blocked agent, an idle agent, or during mutating operations.

```
[ Queue Stalled During Active Turn ]
                 │
                 ▼
[ Step 1: Pre-Escape Inspection & Safety Gates ]
  • Inspect live identity (herdr pane current)
  • Inspect visible screen (herdr agent read --source visible)
  • Is agent blocked on a modal? ──► YES ──► DO NOT SEND ESCAPE! Resolve modal via arrows/enter.
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

### Detailed Procedure & Gates:

### 2.1 Pre-Escape Safety Gates (Must Precede Any Key)
1. **Verify Session Identity**:
   Confirm caller coordinates and target pane via `herdr pane current`. Ensure you are targeting the verified AGY pane.
2. **Inspect Visible Buffer**:
   ```bash
   herdr agent read "$PANE_ID" --source visible --lines 25
   ```
3. **Safety Check — Modals**:
   If the agent is in state `blocked` or displays a modal/dialog (e.g. project trust prompt, question menu, permission prompt), **DO NOT SEND ESCAPE**. Sending Escape to a modal can dismiss the dialog unexpectedly or abort startup. Resolve the modal mechanically using arrow keys and Enter.
4. **Safety Check — Active Mutations**:
   If `herdr pane process-info` or visible output shows active file writes, Git operations (`git commit`, `git rebase`), compiler execution, or package installation, **hold Escape**. Wait for a safe boundary before sending any key. Blind keys during modal display or mutation are strictly prohibited.

### 2.2 Execution & Post-Escape State Branching
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

### 2.3 Child Subprocess vs. Cognitive Turn Disconnection
Captured native evidence (verified via `probe-agy-controller-verification.json`):
- Sending Escape interrupts the cognitive LLM turn. However, surviving child processes (e.g. background bash scripts, sleep commands, compiler invocations) may continue executing to exit status $0$.
- In the probe verification, the agent's internal self-summary reported zero interruptions because its background child process completed cleanly, yet captured native screen output proved that the cognitive LLM turn was interrupted and required Enter submission.
- **Rule**: Do NOT conflate child process survival with cognitive turn continuity, and do NOT equate child exit $0$ with uninterrupted agent flow. Always inspect both `herdr pane process-info` and visible buffer output to reconcile process and cognitive state.

---

## 3. Project Trust Modal Resolution

When AGY starts inside a newly provisioned Git worktree directory, it presents an interactive project trust confirmation prompt:

```text
Do you trust the contents of this project?
> Yes, proceed
  No, exit
```

### Trust Invariants:
1. **Inspect Before Sending Keys**:
   Readiness metadata (`agent_status: idle`, `interactive_ready: true`) can be reported while the trust prompt is still visibly displayed on screen. **Never blindly send Enter after launch**.
2. **Verification & Selection**:
   ```bash
   herdr agent read "$PANE_ID" --source visible --lines 15
   ```
   - If the visible output confirms the trust dialog for the authorized repository, send exactly one Enter:
     ```bash
     herdr agent send-keys "$PANE_ID" enter
     ```
   - If the agent has already passed the prompt and displays an empty composer, **do not send Enter**. An unconditional Enter on an empty composer can submit unwanted blank turns or disrupt startup.

---

## 4. Session Resumption & Conversation Integrity

When resuming an AGY session after a pause, crash, or terminal reconnect:

1. **Exact Conversation ID Required**:
   Always resume using the exact AGY conversation UUID:
   ```bash
   agy --conversation "$AGY_CONVERSATION_ID"
   ```
2. **Never Use `--continue`**:
   `agy --continue` attaches to whichever conversation was updated most recently on the host. In a multi-worktree environment, this causes catastrophic cross-lane state contamination.
3. **Single Continuation Prompt**:
   Verify an input-ready composer before transmitting exactly ONE prompt message: `"continue"`.

---

## 5. Bounded Quota Recovery

If AGY returns an API rate-limit or quota exhaustion error (`RESOURCE_EXHAUSTED` / 429):
1. **Rule of Two**: Two equivalent infrastructure or quota failures halt automated retries.
2. **Verify Actual Progress**: A spinning indicator alone does not prove quota reset. Look for real tool calls and turns before declaring recovery.
3. **Authorized Tiering**: If switching models to bypass quota, use only explicitly authorized model flags (e.g. `--model gemini-3.8-flash`). Never guess non-existent model identifiers or downgrade without authorization.
