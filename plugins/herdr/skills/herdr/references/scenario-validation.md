# Operational Scenario Validation Matrix

This reference documents the 12 concrete operational scenario specifications required by the approved unification plan. It serves as the authoritative verification standard for confirming that unified Herdr behaviors function as specified without regressions or anti-patterns.

> [!NOTE]
> **Evidence Status & Scope Notice**:
> - **[Live Native Run Evidence]**: Scenarios 4 & 5 native AGY turn interruption and composer promotion were empirically verified on this host via AGY CLI 1.2.11 in `probe-agy-controller-verification.json`.
> - **[Cold-Reader Specification / Decision Walkthrough]**: Scenarios 1, 2, 3, 6, 7, 8, 9, 10, 11, 12 provide normative behavioral specifications and decision walkthroughs.
> - **[Unavailable / Unexecuted Checks]**: Full multi-agent fleet execution, remote GitHub PR creation, and unmerged branch force deletions were deliberately not executed in this run per safety guardrails and read-only authority.

---

## 1. Scenario 1: Direct Task Without EM, PR, or Workspace
*(Status: Cold-Reader Specification / Decision Walkthrough)*

- **Context**: A user requests a single-command inspection, a quick bug diagnosis, or a minor bounded fix.
- **Expected Behavior**:
  - Operates inside the caller's current pane or creates a single sibling pane in the same tab (evaluating projected geometry: width $\ge 161$ cols for horizontal split, height $\ge 41$ lines for vertical split).
  - Zero Engineering Manager (EM) spawned.
  - Zero GitHub issues or PRs created.
  - No dedicated worktree workspace opened unless concurrent write isolation is explicitly needed.
  - Reports outcome directly in plain text.
- **Acceptance Criteria**: Pass if no management artifacts, issues, or workspaces are created.

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
  - **Pre-Inspection Safety Gates**: Single wakeup owner verifies agent identity via `herdr pane current --current`, reads visible buffer (`--source visible`), confirms agent is not in `blocked` state or displaying a modal, and confirms no active Git mutations or file writes are underway.
  - Exactly one designated wakeup owner sends a single targeted `esc` (`herdr agent send-keys <pane> esc`).
  - Supervisor reads visible buffer (`--source visible`).
  - If Escape promoted the exact queued message into the composer, supervisor presses Enter ONCE (`herdr agent send-keys <pane> enter`) without pasting duplicate text.
  - If the turn already consumed the queue, supervisor sends nothing.
- **Acceptance Criteria**: Pass if message executes cleanly without duplicate prompt text or corrupted turn state.

---

## 5. Scenario 5: Unsafe Modal / Effect & Duplicate Notice Prevention
*(Status: Live Native Run Evidence — verified via probe-agy-controller-verification.json)*

- **Context**: An agent encounters a project trust dialog or destructive confirmation prompt.
- **Expected Behavior**:
  - Supervisor inspects visible screen before sending keys (`herdr agent read <target> --source visible`).
  - Never automatically sends blind Enter after launch. Resolves modal based on visible authorized choice.
  - Worker notices omit `--wait` to prevent callback deadlocks.
  - Duplicate notices pointing to identical report digests are consumed idempotently without repeating task actions.
- **Acceptance Criteria**: Pass if trust choice is verified visually and no deadlock occurs on notice delivery.

---

## 6. Scenario 6: Codex Tool-Boundary Receipt & Thread Queue
*(Status: Cold-Reader Specification / Decision Walkthrough)*

- **Context**: Delivering steering or follow-up instructions to an active Codex session.
- **Expected Behavior**:
  - Distinguishes Enter tool-boundary steering from Tab follow-up enqueue.
  - Does NOT apply AGY Escape mechanics to Codex.
  - If native queue is supported, uses `codex queue --thread <UUID> --message <TEXT>` with verified thread ID.
  - Treats queue CLI exit 0 as transport acceptance, not proof of consumption.
- **Acceptance Criteria**: Pass if steering reaches tool boundary without PTY corruption.

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
  - State and conversation inventory first: capture conversation ID from session metadata before interrupting.
  - Interrupted with targeted `ctrl+c` or `esc`.
  - Reconnected using exact conversation ID (`agy --conversation <UUID>`), never `--continue`.
  - Single continuation prompt (`"continue"`).
  - If quota failure recurs, supervisor halts automated retries (max 2 equivalent failures) and escalates a concrete capacity blocker.
- **Acceptance Criteria**: Pass if retries halt after 2 equivalent failures without infinite loops.

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
  - Pause stops dispatch, halts new turns, and reconciles state without auto-resuming.
  - Cleanup executes in 3 decoupled stages:
    1. Worker panes closed upon handback verification.
    2. Worktree removed via `herdr worktree remove --workspace <WS_ID>` after delivery completion (PR merge, local merge verified, or read-only/abandoned handback safely archived), clean tree, and ignored build artifact safety verified.
    3. Local branch deleted via safe `git branch -d "$BRANCH_NAME"`. If `-d` refuses, branch reference is preserved with recorded reason (never `-D` fallback; never global remote prune).
  - Leadership pane retires only when all responsibilities are finished.
- **Acceptance Criteria**: Pass if resources are cleanly retired in order, clean worktrees removed, and dirty or intentionally retained checkouts safely preserved with recorded reasons.
