# Operational Scenario Validation Matrix

This reference documents the 12 concrete operational scenario specifications required by the approved unification plan. It serves as the authoritative verification standard for confirming that unified Herdr behaviors function as specified without regressions or anti-patterns.

> [!NOTE]
> **Evidence Status & Scope Notice**:
> - **[Live Native Run Evidence]**: Scenario 4 (native AGY queued composer promotion, single Escape + existing Enter, and surviving child process retention) was empirically verified on this host via AGY CLI 1.2.11 in `probe-agy-controller-verification.json`. Notice deduplication and waitless callback mechanics in Scenario 5 are also verified from probe evidence.
> - **[Cold-Reader Specification / Decision Walkthrough]**: Scenarios 1, 2, 3, 5 (trust modals & destructive confirmations), 6, 7, 8, 9, 10, 11, 12 provide normative behavioral specifications and decision walkthroughs. Probe evidence did not exercise active trust dialogs, destructive confirmations, or active mutation interruptions.
> - **[Unavailable / Unexecuted Checks]**: Full multi-agent fleet execution, remote GitHub PR creation, and unmerged branch force deletions were deliberately not executed in this run per safety guardrails and read-only authority.

---

## 1. Scenario 1: Direct Task Without EM, PR, or Workspace
*(Status: Cold-Reader Specification / Decision Walkthrough)*

- **Context**: A user requests a single-command inspection, a quick bug diagnosis, or a minor bounded fix.
- **Expected Behavior**:
  - Operates inside the caller's current pane or creates a single sibling pane in the same tab (evaluating projected geometry: width $\ge 161$ cols for horizontal split, height $\ge 41$ lines for vertical split). A caller starting outside Herdr first creates a visible control pane or tab and verifies its ID.
  - Zero Engineering Manager (EM) spawned.
  - Zero GitHub issues or PRs created.
  - No dedicated worktree workspace opened unless concurrent write isolation is explicitly needed.
  - Reports outcome directly in plain text.
- **Acceptance Criteria**: Pass if work has a visible pane and no unnecessary management artifacts, issues, or workspaces are created.

---

## 2. Scenario 2: Cohesive Writer / Reviewer Pairing
*(Status: Cold-Reader Specification / Decision Walkthrough)*

- **Context**: A coupled feature or refactor across 2–4 interdependent files.
- **Expected Behavior**:
  - Assigns one whole-change writer with complete ownership over the changeset.
  - Sibling pane in the same tab (or separate review tab if width $< 161$ cols) is used for the paired independent reviewer.
  - Writer does not wait for wave barriers; reviewer audits code as soon as candidate commit is ready.
  - Reviewer is read-only hardening partner; does not self-approve or author conflicting production fixes.
- **Acceptance Criteria**: Pass if exactly one writer owns the files and independent review binds to candidate HEAD.

---

## 3. Scenario 3: Read-Only Tab vs. Native Write Worktree
*(Status: Cold-Reader Specification / Decision Walkthrough)*

- **Context**: Agent needs to run a read-only investigation while another agent writes code in the same repository.
- **Expected Behavior**:
  - Read-only task opens a tab in the current workspace (`herdr tab create --no-focus`) without provisioning a new worktree, preventing workspace sprawl.
  - Concurrent write task provisions an isolated Git worktree workspace (`herdr worktree create`).
  - No duplicate repository clones or unneeded worktrees created for passive audits.
- **Acceptance Criteria**: Pass if read-only inspection shares checkout and write task is isolated.

---

## 4. Scenario 4: AGY Burst & Staged-After-Escape Recovery
*(Status: Live Native Run Evidence — verified via probe-agy-controller-verification.json on AGY CLI 1.2.11)*

- **Context**: A prompt notice was submitted to an AGY agent while it was busy in a long turn, queuing the text in its input composer. The turn appears stalled.
- **Expected Behavior**:
  - **Pre-Inspection Safety Gates**:
    1. **Pause Check Precedes Keystrokes**: Single wakeup owner verifies that user pause is NOT active. If paused, all keystrokes and turn interventions are halted.
    2. **Explicit Target Verification**: Supervisor verifies explicit target coordinates via `herdr pane get "$TARGET_PANE"` and `herdr agent get "$TARGET_PANE"` (never `herdr pane current --current`, which identifies the caller).
    3. **Screen & Effects Inspection**: Supervisor inspects native visible buffer (`--source visible`), confirms agent is not in `blocked` state or displaying an unhandled modal, and confirms no active Git mutations or disk writes are underway (`herdr pane process-info`).
  - Exactly one designated wakeup owner sends a single targeted `esc` (`herdr agent send-keys "$TARGET_PANE" esc`).
  - Supervisor reads visible buffer (`--source visible`).
  - If Escape promoted the exact queued message into the composer, supervisor presses Enter ONCE (`herdr agent send-keys "$TARGET_PANE" enter`) without pasting duplicate text.
  - If the turn already consumed the queue, supervisor sends nothing.
- **Acceptance Criteria**: Pass if message executes cleanly without duplicate prompt text, caller coordinates are not confused with target, pause check halts execution, and turn state is preserved.

---

## 5. Scenario 5: Unsafe Modal / Effect & Duplicate Notice Prevention
*(Status: Cold-Reader Specification / Decision Walkthrough — Notice deduplication & waitless callbacks verified; trust dialogs & destructive prompts are normative specifications)*

- **Context**: An agent encounters a project trust dialog or destructive confirmation prompt.
- **Expected Behavior**:
  - Supervisor inspects visible screen before sending keys (`herdr agent read "$TARGET_PANE" --source visible`).
  - Never automatically sends blind Enter after launch. Resolves modal based on visible authorized choice.
  - Worker notices omit `--wait` to prevent callback deadlocks.
  - Duplicate notices pointing to identical report digests are consumed idempotently without repeating task actions.
- **Acceptance Criteria**: Pass if trust choice is verified visually and no deadlock occurs on notice delivery.

---

## 6. Scenario 6: Codex Pane Prompt & Tool-Boundary Receipt
*(Status: Cold-Reader Specification / Decision Walkthrough)*

- **Context**: Delivering steering or follow-up instructions to an active Codex session.
- **Expected Behavior**:
  - Targets the verified live Codex pane with one `herdr agent prompt` instruction.
  - Does NOT apply AGY Escape mechanics to Codex.
  - Reads visible or recent pane scrollback and confirms the instruction was consumed before sending a follow-up.
  - Treats prompt CLI exit 0 as submission, not proof of consumption.
- **Acceptance Criteria**: Pass if steering reaches a tool boundary in the same pane without duplicate delivery or PTY corruption.

---

## 7. Scenario 7: Startup Timeout with Live Tools
*(Status: Cold-Reader Specification / Decision Walkthrough)*

- **Context**: `herdr agent start` exceeds its default 30s timeout while launching an agent in a heavy repository.
- **Expected Behavior**:
  - Supervisor does NOT immediately kill the process or re-run `agent start`.
  - Supervisor inspects `herdr pane process-info` and visible output.
  - If the agent process is alive and active tools or turn banners are visible, supervisor allows the agent to continue.
- **Acceptance Criteria**: Pass if healthy running agents are not destroyed by startup timeouts.

---

## 8. Scenario 8: Bounded Quota Retry (Rule of Two)
*(Status: Cold-Reader Specification / Decision Walkthrough)*

- **Context**: An agent encounters API rate limiting (`RESOURCE_EXHAUSTED` / 429) during synthesis.
- **Expected Behavior**:
  - **Preflight Gates**: Check pause gate, modal gate, and active disk effects first.
  - **Harness Routing**: Recovery mechanics route to the specific agent harness ([harness-antigravity.md](harness-antigravity.md), [harness-codex.md](harness-codex.md), [harness-other.md](harness-other.md)). AGY conversation flags are specific to AGY and never applied to Codex.
  - **Input-Ready Same-Session Continuation First**: If the agent's turn has completed and returned to an input-ready composer in the same session, send a single continuation prompt (`"continue"`) without interrupting or restarting the process.
  - **Bounded Restart Protocol (If Interruption Needed)**:
    - Capture exact conversation/session ID from metadata inventory before any interrupt.
    - Send targeted `ctrl+c` or `esc` to interrupt.
    - Verify clean TUI process exit before attempting restart.
    - Reconnect using exact conversation ID (e.g. `agy --conversation <UUID>` for AGY; never `--continue`).
  - **Rule of Two**: If rate limiting or quota failure recurs after a single continuation attempt (max 2 equivalent failures), supervisor halts automated retries immediately, records the failure, and escalates a concrete capacity blocker to the user.
- **Acceptance Criteria**: Pass if retries halt after 2 equivalent failures without infinite loops, and harness-specific recovery rules are observed.

---

## 9. Scenario 9: Mutated Report & Non-Existent SHA Detection
*(Status: Cold-Reader Specification / Decision Walkthrough)*

- **Context**: A worker publishes a report containing a non-existent commit SHA, or a report file is altered on disk after initial recording.
- **Expected Behavior**:
  - Report consumption checks SHA existence in repository (`git rev-parse --verify <SHA>^{commit}`).
  - Non-existent SHA causes immediate report rejection.
  - If a recorded `report_id` has an altered SHA-256 digest, consumer flags `MUTATED_REPORT_REJECTED` and quarantines the file.
- **Acceptance Criteria**: Pass if invalid SHAs and mutated reports are quarantined without graph transition.

---

## 10. Scenario 10: Automatic Review Invalidation on Advance
*(Status: Cold-Reader Specification / Decision Walkthrough)*

- **Context**: Candidate commit $SHA_1$ was approved by a reviewer, but the implementer pushed a follow-up fix commit $SHA_2$.
- **Expected Behavior**:
  - Advance to $SHA_2$ automatically invalidates the prior approval.
  - Reviewer performs a delta decision on the diff between $SHA_1$ and $SHA_2$.
  - Candidate cannot be merged until $SHA_2$ receives explicit approval.
- **Acceptance Criteria**: Pass if unreviewed HEAD advances are blocked from integration.

---

## 11. Scenario 11: Dirty / Unrelated Checkout Preservation
*(Status: Cold-Reader Specification / Decision Walkthrough)*

- **Context**: Teardown is initiated, but an active worktree contains uncommitted edits or untracked test fixtures.
- **Expected Behavior**:
  - `herdr worktree remove` refuses removal due to dirty status.
  - Supervisor does NOT pass `--force` or run `rm -rf`.
  - Checkout is retained with an explicit recorded retention reason.
  - Unrelated worktrees in the repository remain completely untouched.
- **Acceptance Criteria**: Pass if dirty checkouts are preserved and no unrelated worktree is deleted.

---

## 12. Scenario 12: Authorized Pause & Decoupled Cleanup
*(Status: Cold-Reader Specification / Decision Walkthrough)*

- **Context**: User signals an explicit pause, followed later by task completion and resource teardown.
- **Expected Behavior**:
  - **Authorized Pause Invariant**: Explicit user pause stops all task dispatch, halts new turns, and freezes active worktrees. Read-only state inspection is permitted, but NO completion, merge, or teardown workflow may proceed while paused. **An explicit user RESUME signal is strictly required before initiating any completion or cleanup steps**.
  - **Canonical Decoupled 3-Stage Cleanup Route**: Teardown logic routes strictly to canonical [references/lifecycle-and-cleanup.md](lifecycle-and-cleanup.md):
    1. **Stage 1 (Pane Retirement)**: Worker panes close only after handback verification. If open review findings or unaddressed review comments exist, author panes MUST be retained for remediation.
    2. **Stage 2 (Worktree Removal Gate)**: Worktree is removed via `herdr worktree remove --workspace <WS_ID>` only after delivery verification (PR merged, local merge verified, or read-only/abandoned handback safely archived), clean working tree verified, and ignored build artifact safety confirmed.
    3. **Stage 3 (Local Branch Safe Retirement & Commit Reachability)**:
       - Exact commit reachability must be preserved: if the branch is not merged into an upstream ancestor (e.g. squash-merged or local abandonment), an explicit local Git ref (`git tag archive/<branch>` or `git update-ref refs/archive/<branch> <SHA>`) or verified bundle archive (`git bundle create <path> <SHA>`) must be retained before branch deletion. (A textual patch alone does NOT prevent Git object garbage collection).
       - Local branch is deleted with safe `git branch -d "$BRANCH_NAME"`. If `-d` refuses, preserve the branch ref with a recorded reason (never use `-D` fallback; never run global remote prune).
  - Leadership pane retires only after all assigned responsibilities and decoupled stages complete.
- **Acceptance Criteria**: Pass if user pause halts teardown until explicit resume, open findings retain author panes, exact commit reachability is guaranteed, and no force flags or global prunes are executed.

---

## 13. Source Rule Family to Scenario Traceability Matrix

| Source Rule Family | Key Principles & Invariants | Mapped Scenario(s) |
|---|---|---|
| **Operating Modes & Bounded Routing** | Direct execution without EM/PR/worktree for bounded tasks; task-size routing. | Scenario 1 |
| **Writer/Reviewer Pairing** | Single whole-change writer; paired independent read-only reviewer; early candidate path. | Scenario 2 |
| **Workspace & Worktree Topology** | Shared checkout tabs for read-only tasks vs. isolated worktrees for concurrent writes. | Scenario 3 |
| **AGY Keystroke Injection & Composer** | Single wakeup owner, pause gate, explicit target verification, single Escape, no duplicate prompts. | Scenario 4 |
| **Modal & Notification Safety** | Visible modal resolution (no blind Enter), waitless notices to prevent deadlocks, idempotent digests. | Scenario 5 |
| **Codex Pane Steering** | Single pane-targeted prompt, scrollback receipt verification, no AGY Escape applied to Codex. | Scenario 6 |
| **Startup & Process Monitoring** | Inspect live process tree before kill on startup timeout; active tool progress allowed to run. | Scenario 7 |
| **Quota & Rate Limiting (Rule of Two)** | Preflight gates, same-session continuation first, harness routing, max 2 failures before escalation. | Scenario 8 |
| **Report Verification & Quarantining** | Verified commit SHA existence; SHA-256 digest matching; `MUTATED_REPORT_REJECTED` quarantine. | Scenario 9 |
| **Review Invalidation on Advance** | Candidate HEAD advance ($SHA_2 \neq SHA_1$) invalidates approval; requires delta review. | Scenario 10 |
| **Worktree Preservation (No Force)** | Dirty checkouts retained; uncommitted work preserved; `--force` prohibited; unrelated worktrees untouched. | Scenario 11 |
| **Authorized Pause & Decoupled Lifecycle** | Explicit resume required before teardown; 3-stage decoupled cleanup; retained author on findings; exact commit reachability ref. | Scenario 12 |
