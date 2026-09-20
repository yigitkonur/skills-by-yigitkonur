# Herdr Native Acceptance Scenarios & Forward-Test Specifications

## 1. Overview & Architecture Alignment

This document defines the runnable, finite acceptance scenarios for the Codex-first Herdr orchestration architecture within `skills-by-yigitkonur`. It establishes exact operational procedures for validating the hierarchical orchestration pattern:

$$\text{Codex CTO} \longrightarrow \text{Codex Engineering Manager (EM)} \longrightarrow \text{AGY Implementers / Fresh Reviewers / Integration & Recovery Executors}$$

### 1.1 The 3-Axis Decoupling Invariant, Topology & Delivery Tiers

All scenarios enforce explicit separation across three distinct state axes:

1. **Worker State (PTY & Screen Heuristics)**: `idle`, `working`, `blocked`, `done`, `unknown`. Represents the physical terminal and detected process status inside the Herdr pane.
2. **Observer State (Host Wait Handle)**: `none`, `waiting`, `settled`, `timed_out`. Represents the caller's synchronous observation handle (`herdr agent wait`). An observer timeout is never treated as a worker failure.
3. **Delivery State (Engineering Lifecycle)**:
   - **Mission-Specific Delivery Hold (Mission `herdr-codex-first-20260920`)**:
     $$\text{assigned} \longrightarrow \text{implementing} \longrightarrow \text{committed_locally} \longrightarrow \text{clean_review} \longrightarrow \text{integrated_draft_pr} \longrightarrow \text{cto_candidate_gate}$$
     *Execution for this mission strictly terminates upon publishing the single integrated, verified draft PR unmerged to the CTO candidate gate.* Feature-branch pushes and draft PR creation are authorized; direct pushes to `main` and PR merges are strictly held.
   - **General Future Production Delivery**:
     $$\text{assigned} \longrightarrow \text{implementing} \longrightarrow \text{committed_locally} \longrightarrow \text{clean_review} \longrightarrow \text{integrated_pr} \longrightarrow \text{pr_ready} \longrightarrow \text{serial_merge}$$
     Describes fully authorized production delivery where the AGY integration executor performs serial rebase onto `origin/main`, executes candidate verification, promotes the PR to ready (`gh pr ready`), and executes serial squash-merge after explicit authorization.

#### Leadership Topology & Worker Isolation
- **Leadership Plane (One Tab, Two Panes)**: The leadership hierarchy resides in **exactly two panes within ONE shared tab**:
  - **CTO Pane (LEFT)**: Strategy, scope approvals, exceptional decisions, candidate gate clearance.
  - **Engineering Manager Pane (RIGHT)**: Created via `herdr pane split [CTO_PANE] --direction right`. Task allocation, observation, report intake, reviewer scheduling, state checkpointing.
- **Worker & Reviewer Plane (Separate Per-Task Tabs)**: Every implementer, fresh reviewer, and integration executor operates in an independent, dedicated per-task tab (`herdr tab create --label <task-lane> --no-focus`) to ensure zero visual interference, zero shared Git index collisions, and clean conversational isolation.

#### Safe Pane Move & Dynamic Metadata Invariant
- During dynamic topology re-organization or migration (e.g. moving a manager pane into the CTO's tab), static startup environment variables (such as `$HERDR_TAB_ID`) are frozen at process creation and become **stale**.
- Agents and orchestration procedures must **never trust static startup environment variables** for topology decisions. They must always query live coordinates via `herdr pane current` or `herdr pane get <PANE_ID>`, which return the authoritative live `tab_id`, `pane_id`, `terminal_id`, and `workspace_id`.
- Safe pane movement (`herdr pane move`) preserves physical `pane_id`, `terminal_id`, running OS processes, cognitive `session_id`, working directory, and callback prompt reception (`herdr agent prompt <PANE_ID>`).

### 1.2 Evidence Classification & Integrity Taxonomy

To prevent speculative or fabricated claims, every scenario and observation in this catalog is strictly tagged under one of four integrity tiers:

- **`[HISTORICAL]`**: Empirical observations gathered during initial exploratory probes (e.g., probe environment `/tmp/herdr-native-probe.gZJMuX`, panes `w3H:p5`/`p6`/`p7`, tab `w3H:t5` on 2026-09-20). Serves as historical context and design rationale, not current execution claims.
- **`[SUPPORTED]`**: Functionality directly verified against the installed Herdr CLI (v0.9.0, protocol 22) and current runtime interfaces (`--help`, documented options, and observed JSON schemas).
- **`[PROPOSED]`**: Bounded, deterministic test procedures designed for execution by the forward-test controller lane.
- **`[UNVERIFIED]`**: Edge conditions, race conditions, or recovery branches that have not yet been executed in the current mission run and await forward-test execution.

### 1.3 Degraded AGY Mode Invariant & Direct Pane Controls

When Google Antigravity CLI (`agy`) launches inside a Herdr pane, agent detection heuristics may evaluate to `agent_status: unknown` if custom wrappers or local prompt formats mask standard detection markers.

**Operational Rule**: A status of `unknown` must **never** trigger automatic relaunch over an active TUI. If `herdr pane process-info --pane <PANE_ID>` confirms a live foreground AGY process and `herdr pane read <PANE_ID> --source visible` displays an active composer/prompt, the session is classified as **Degraded AGY Mode**.

In Degraded AGY Mode, supervisors must use direct, supported **pane-level controls** rather than agent-registry abstractions that depend on recognized detection:
- **Terminal Inspection**: Captured via `herdr pane read <PANE_ID> --source recent-unwrapped` (for logical line reconstruction) or `herdr pane read <PANE_ID> --source visible` (for rendered viewports and modals).
- **Prompt Submission (`pane run` Semantics)**: `herdr pane run <PANE_ID> <TEXT>` sends text followed by `Enter` directly into the active foreground agent composer in one call. It injects a prompt turn into the interactive agent. *It does NOT execute a raw subshell command in the background OS shell while an agent occupies the foreground.*
- **Raw Shell Commands & Test Suites**: Must be executed either when the pane sits at an idle shell prompt (no active agent) or internally through AGY's own native command tools (`run_command`).
- **Direct Keystroke & Input Control**: Delivered via `herdr pane send-text <PANE_ID> <TEXT>` and `herdr pane send-keys <PANE_ID> <KEY>...` (e.g. `down`, `enter`, `esc`).
- **Durable File Handoffs**: Conducted via immutable YAML reports conforming to `skills/herdr/references/report-contract.md` rather than relying on terminal state transitions.

---

## 2. Acceptance Scenario Matrix

| Scenario ID | Name / Purpose | Target Runtime & Role | Integrity Status | Primary Verification Metric |
|---|---|---|---|---|
| **SCEN-01** | Launch, Coordinate Discovery & Native Registration | Codex EM & AGY Worker | `[SUPPORTED]` / `[PROPOSED]` | JSON coordinate extraction, registration notice with role, and candidate SKILL.md path/SHA-256 binding |
| **SCEN-02** | Explicit AGY $\to$ Idle Codex Handback | AGY Worker $\to$ Codex EM | `[HISTORICAL]` / `[PROPOSED]` | Atomic report publication & manager turn activation |
| **SCEN-03** | Asynchronous Handback to Busy Codex (Enter at Tool Boundary) | AGY Worker $\to$ Codex EM | `[HISTORICAL]` / `[PROPOSED]` | Input queued in TUI; zero stdin corruption at tool boundary |
| **SCEN-04** | Multi-Sender Fan-In & Idempotent Intake | 2 AGY Workers $\to$ Codex EM | `[HISTORICAL]` / `[PROPOSED]` | Sequential ingestion; duplicate event ID ignored |
| **SCEN-05** | Fault-Tolerant Intake (Missed Notice, Partial, Stale, Mutated) | AGY Worker $\to$ Codex EM | `[PROPOSED]` / `[UNVERIFIED]` | Sweep catches unnotified; `.partial`, stale attempt, and mutated digest rejected |
| **SCEN-06** | Deferred Follow-Up via Tab Keystroke (Exclusive Composer) | Controller $\to$ Codex EM | `[HISTORICAL]` / `[PROPOSED]` | Input deferred across tool executions until full turn completion |
| **SCEN-07** | Observer Wait Cancellation vs. Worker Survival | Host Shell $\to$ Worker Pane | `[HISTORICAL]` / `[PROPOSED]` | Host wait exits on SIGINT; worker process continues undisturbed |
| **SCEN-08** | Targeted Escape Interruption & Side-Effect Reconciliation | Controller $\to$ Worker/EM | `[HISTORICAL]` / `[PROPOSED]` | Turn interrupted; background processes and Git state reconciled |
| **SCEN-09** | Manager Relinquishment, Crash Recovery & State Resume | Resumed Codex EM | `[HISTORICAL]` / `[PROPOSED]` | Old writer relinquished; structural checkpoint validation (top keys & assignment shapes) + negative swallow rejection |
| **SCEN-10** | Parallel Lane Allocation & Dynamic Capacity Refill | Multiple AGY Workers | `[SUPPORTED]` / `[PROPOSED]` | Isolated worktree paths; zero git lock collision; capacity refill |
| **SCEN-11** | Clean-Context Exact-SHA Review Gate & Invalidation | Fresh AGY Reviewer | `[PROPOSED]` / `[UNVERIFIED]` | Independent audit at candidate SHA; commit advance invalidates review |
| **SCEN-12** | Safe Sequential Teardown & Evidence Preservation | Integration Executor | `[SUPPORTED]` / `[PROPOSED]` | Clean unmount; zero dirty force deletes; durable logs preserved; delivery hold |
| **SCEN-13** | Cold Role Selection, Reference Routing & Authority Bounding | Any Cold Role | `[SUPPORTED]` / `[PROPOSED]` | Role identification before reading; targeted references; secondary manager refusal |
| **SCEN-14** | Leadership Split-Tab Layout, Safe Pane Move & Dynamic Metadata Preservation | Codex CTO & EM | `[SUPPORTED]` / `[PROPOSED]` | 2-pane leadership tab (CTO left, EM right); safe move preserves session/callbacks; live metadata vs stale env |

---

## 3. Detailed Acceptance Scenario Specifications

### SCEN-01: Agent Launch, Coordinate Discovery & Native Registration

- **Objective**: Verify clean launch of Codex and AGY agents in dedicated panes, deterministic extraction of native coordinates via JSON, completion of the return-address registration handshake with explicit role declaration, and mandatory binding of the exact candidate `SKILL.md` path and SHA-256 content digest.
- **Classification**: `[SUPPORTED]` (CLI syntax and JSON parsing verified); `[PROPOSED]` (Acceptance run sequence).
- **Prerequisites**:
  - Herdr server running (protocol 22).
  - Target workspace allocated (`HERDR_WORKSPACE_ID`).
  - Available runtime models discovered (`gpt-6-astra` for Codex, `gemini-3.8-flash-high` for AGY).
  - Candidate `SKILL.md` in active candidate worktree checkout.
  - Leadership tab established (CTO left, EM right in one tab); workers allocated in separate per-task tabs.
- **Execution Steps**:
  1. Allocate dedicated tab and split pane for the worker:
     ```bash
     herdr tab create --workspace "$HERDR_WORKSPACE_ID" --label "lane-worker" --no-focus
     # Returns .result.tab.tab_id and .result.root_pane.pane_id
     ```
  2. Launch worker runtime:
     ```bash
     herdr agent start "worker-scen01" --kind agy --pane "$WORKER_PANE_ID" -- --model gemini-3.8-flash-high
     ```
  3. Worker queries native coordinates inside its active shell:
     ```bash
     herdr pane current
     ```
     Extract `.result.pane.pane_id`, `.result.pane.tab_id`, `.result.pane.terminal_id`, and `.result.pane.cwd`.
  4. Worker inspects candidate `SKILL.md` to compute exact candidate binding metadata:
     ```bash
     CANDIDATE_SKILL_PATH="$WORKER_CWD/skills/herdr/SKILL.md"
     test -f "$CANDIDATE_SKILL_PATH" || { echo "ERROR: Candidate skill missing at $CANDIDATE_SKILL_PATH" >&2; exit 1; }
     CANDIDATE_WORKTREE=$(git -C "$(dirname "$CANDIDATE_SKILL_PATH")" rev-parse --show-toplevel 2>/dev/null)
     test -n "$CANDIDATE_WORKTREE" || { echo "ERROR: $CANDIDATE_SKILL_PATH not inside a git repository" >&2; exit 1; }
     CANDIDATE_SKILL_SHA256=$(shasum -a 256 "$CANDIDATE_SKILL_PATH" | awk '{print $1}')
     CANDIDATE_HEAD=$(git -C "$CANDIDATE_WORKTREE" rev-parse HEAD)
     test -n "$CANDIDATE_HEAD" || { echo "ERROR: Failed to resolve candidate HEAD from $CANDIDATE_WORKTREE" >&2; exit 1; }
     ```
  5. Worker submits registration notice to Manager pane (`$MANAGER_PANE_ID`) without `--wait`, explicitly declaring role and candidate binding:
     ```bash
     herdr agent prompt "$MANAGER_PANE_ID" "Registration notice:
     - mission_id: $MISSION_ID
     - task_id: $TASK_ID
     - attempt: 1
     - role: implementer
     - pane_id: $WORKER_PANE_ID
     - tab_id: $WORKER_TAB_ID
     - terminal_id: $WORKER_TERM_ID
     - runtime: agy
     - model: Gemini 3.8 Flash (High)
     - cwd: $WORKER_CWD
     - candidate_skill_path: $CANDIDATE_SKILL_PATH
     - candidate_skill_sha256: $CANDIDATE_SKILL_SHA256
     - candidate_head: $CANDIDATE_HEAD
     Ready for assignment acknowledgment."
     ```
  6. Manager verifies candidate binding:
     - Confirms `candidate_skill_path` resolves inside the active mission worktree (not in `~/.codex/skills/` or `~/.agents/skills/`).
     - Confirms `candidate_skill_sha256` matches the candidate tree revision.
     - Records worker identity, role, and candidate binding in `state.yaml` under `assignments.<task_id>`.
     - Replies with assignment acknowledgment.
- **Pass/Fail & Observable Signals**:
  - **Pass**: `herdr pane current` returns valid JSON with non-empty string fields for `pane_id`, `tab_id`, and `cwd`. `herdr agent prompt` exits code 0 with `{"type":"agent_prompted"}`. Manager logs registration state as `verified_native_identity_and_received_notice` with explicit `role: implementer` and verified `candidate_skill_sha256`.
  - **Globally Mounted Skill Rejection**: If registration references a globally mounted path (e.g. `~/.codex/skills/herdr/SKILL.md`), manager rejects registration with `invalid_candidate_source: globally_mounted_skill_forbidden`.
  - **Degraded Signal**: If `herdr agent get $WORKER_PANE_ID` shows `agent_status: unknown`, verify `herdr pane process-info --pane $WORKER_PANE_ID` shows live `agy` child process and proceed under Degraded AGY Mode using direct pane primitives.
  - **Fail**: Command exits non-zero; `pane current` emits unparseable non-JSON; prompt rejected with `agent_blocked`.
- **Evidence to Retain**:
  - Captured JSON from `herdr pane current`.
  - Exact registration payload logged in manager `state.yaml` including candidate SHA-256.
- **Cleanup Boundary**:
  - Close test pane via `herdr pane close $WORKER_PANE_ID` if not reused.

---

### SCEN-02: Explicit AGY $\to$ Idle Codex Handback

- **Objective**: Validate the atomic report publication and notification pattern from a completed AGY worker to an idle Codex engineering manager, following the canonical report-contract publication pipeline.
- **Classification**: `[HISTORICAL]` (Observed in probe `gZJMuX`, pane `w3H:p5` $\to$ `w3H:p6`); `[PROPOSED]` (Forward-test verification).
- **Prerequisites**:
  - Codex Manager resting at idle prompt in pane `$MANAGER_PANE_ID` (verified via `herdr agent get $MANAGER_PANE_ID` reporting `agent_status: idle`).
  - AGY Worker in `$WORKER_PANE_ID` with completed task output.
  - Shared run directory exists outside worktrees: `$RUN_ROOT`.
- **Execution Steps**:
  1. Worker selects unique report ID conforming to canonical schema (`<task_id>-a<attempt>-<purpose>`):
     ```bash
     REPORT_ID="scen02-a1-handback"
     REPORT_PATH="$RUN_ROOT/$REPORT_ID.yaml"
     ```
  2. Worker verifies no destination file collision exists:
     ```bash
     test ! -f "$REPORT_PATH" || (echo "Destination collision: $REPORT_PATH exists" && exit 1)
     ```
  3. Worker writes immutable report to temporary partial path `$REPORT_PATH.partial` using `apply_patch`.
  4. Worker verifies completeness and syntax of `.partial` file (ensures non-empty and well-formed YAML):
     ```bash
     python3 -c "import yaml; yaml.safe_load(open('$REPORT_PATH.partial'))" 2>/dev/null || \
     python3 -c "import json; [print(k) for k in open('$REPORT_PATH.partial') if ':' in k]"
     ```
  5. Worker atomically moves partial file to canonical destination:
     ```bash
     mv "$REPORT_PATH.partial" "$REPORT_PATH"
     ```
  6. Worker verifies file exists at destination, then submits single-line notification to manager without `--wait`:
     ```bash
     herdr agent prompt "$MANAGER_PANE_ID" "Report published: report_id=$REPORT_ID origin_pane=$WORKER_PANE_ID origin_tab=$WORKER_TAB_ID task_id=$TASK_ID attempt=1 status=completed report_path=$REPORT_PATH requested_action=review_candidate"
     ```
  7. Manager receives turn, reads `$REPORT_PATH`, verifies SHA-256 digest, records event in `consumed_reports`, and updates task graph.
- **Pass/Fail & Observable Signals**:
  - **Pass**: Manager terminal activates from `idle` to `working`; manager inspects `$REPORT_PATH` and updates `state.yaml` with the report's SHA-256 hash; manager prompt returns code 0.
  - **Fail**: Partial file read before rename; manager fails to activate; report malformed; prompt times out or deadlocks caller.
- **Evidence to Retain**:
  - Saved `$REPORT_PATH` and its calculated SHA-256 hash.
  - Manager log entry showing report intake and disposition.
- **Cleanup Boundary**:
  - Retain report in run root. Free worker pane upon managerial acknowledgment.

---

### SCEN-03: Asynchronous Handback to Busy Codex (Enter at Tool Boundary)

- **Objective**: Verify that submitting an operational notice via `herdr agent prompt` while Codex is actively executing a tool turn does not corrupt stdin or drop characters, but queues cleanly for execution at the next tool boundary.
- **Classification**: `[HISTORICAL]` (Observed in probe `gZJMuX` during 20-second active sleep); `[PROPOSED]` (Forward-test validation).
- **Prerequisites**:
  - Codex Manager pane active and executing a multi-second command (e.g., `sleep 15`).
- **Execution Steps**:
  1. Trigger long-running execution in Codex Manager pane.
  2. Confirm manager is in `working` status:
     ```bash
     herdr agent get "$MANAGER_PANE_ID" # Expect .result.agent.agent_status == "working"
     ```
  3. Dispatch notification prompt from worker shell without `--wait`:
     ```bash
     herdr agent prompt "$MANAGER_PANE_ID" "Notice: task_id=$TASK_ID status=in_progress checkpoint=step_2"
     ```
  4. Observe manager terminal display via:
     ```bash
     herdr pane read "$MANAGER_PANE_ID" --source visible --lines 15
     ```
  5. Allow initial tool turn to complete; observe prompt intake at the boundary.
- **Pass/Fail & Observable Signals**:
  - **Pass**: `herdr agent prompt` exits code 0 with `{"type":"agent_prompted"}`. Manager TUI displays pending input queue indicator. Upon initial command termination, queued text is ingested as a new prompt turn without syntax truncation or prompt leakage into command stdin.
  - **Fail**: Prompt rejected with error; text injected into active command's raw stdin buffer causing command failure; characters dropped.
- **Evidence to Retain**:
  - Terminal snapshot of manager pane captured during execution showing pending input indicator.
  - Manager transcript showing clean two-turn execution sequence.
- **Cleanup Boundary**:
  - Wait for manager turn to conclude cleanly before submitting subsequent prompts.

---

### SCEN-04: Multi-Sender Fan-In & Idempotent Intake

- **Objective**: Verify that multiple independent AGY workers can submit completion notices to a single Codex Manager, and that duplicate deliveries of identical report IDs are handled idempotently without re-triggering side effects.
- **Classification**: `[HISTORICAL]` (Observed in probe `gZJMuX` with senders `w3H:p5` and `w3H:p7`); `[PROPOSED]` (Forward-test verification).
- **Prerequisites**:
  - Two worker panes (`$WORKER_A_PANE`, `$WORKER_B_PANE`) executing concurrent subtasks.
  - Single manager pane (`$MANAGER_PANE_ID`).
- **Execution Steps**:
  1. Worker A and Worker B independently publish immutable reports:
     - Worker A: `$RUN_ROOT/scen04-task-a.yaml` (`report_id: scen04-task-a`)
     - Worker B: `$RUN_ROOT/scen04-task-b.yaml` (`report_id: scen04-task-b`)
  2. Worker A prompts Manager without `--wait`:
     ```bash
     herdr agent prompt "$MANAGER_PANE_ID" "Report published: report_id=scen04-task-a path=$RUN_ROOT/scen04-task-a.yaml"
     ```
  3. Worker B prompts Manager concurrently without `--wait`:
     ```bash
     herdr agent prompt "$MANAGER_PANE_ID" "Report published: report_id=scen04-task-b path=$RUN_ROOT/scen04-task-b.yaml"
     ```
  4. Worker A intentionally re-sends its identical notification prompt 5 seconds later (duplicate delivery simulation).
  5. Manager processes incoming events, logging consumed IDs and updating total processed count.
- **Pass/Fail & Observable Signals**:
  - **Pass**: Both reports are ingested; manager's `consumed_reports` lists `scen04-task-a` and `scen04-task-b`; processed task count increments by exactly 2. The duplicate delivery of `scen04-task-a` is logged as a duplicate digest match and discarded without re-triggering task dispatch or state corruption.
  - **Fail**: Deadlock on concurrent prompts; duplicate prompt causes duplicate downstream action or task rollback; race condition corrupts `state.yaml`.
- **Evidence to Retain**:
  - Manager's `state.yaml` showing `consumed_reports` with exact SHA-256 hashes.
  - Action log recording idempotent duplicate skip.
- **Cleanup Boundary**:
  - Scoped to test run directory.

---

### SCEN-05: Fault-Tolerant Intake (Missed Notice, Partial, Stale, Mutated)

- **Objective**: Validate the robustness of the manager's intake engine against transmission failures, incomplete writes, stale attempts, and corrupted reports, adhering to canonical report contract matching rules.
- **Classification**: `[PROPOSED]` / `[UNVERIFIED]` (Formal acceptance criteria defined in design specification).
- **Prerequisites**:
  - Shared run directory `$RUN_ROOT`.
  - Active Codex Manager running intake reconciliation loops.
- **Execution Steps**:
  1. **Sub-case 5.1 (Missed Notification)**:
     - Write valid report `$RUN_ROOT/scen05-unnotified.yaml`.
     - Intentionally suppress `herdr agent prompt`.
     - Manager initiates periodic checkpoint or ten-minute timeout sweep.
     - Manager scans `$RUN_ROOT/*.yaml`, detects unconsumed report, verifies exact match on `mission_id`, `task_id`, `attempt`, and registered producer identity, and consumes it.
  2. **Sub-case 5.2 (Partial Publication)**:
     - Worker creates `$RUN_ROOT/scen05-incomplete.yaml.partial`.
     - Manager intake sweep runs while `.partial` exists.
     - Manager explicitly ignores all files matching `*.partial`.
  3. **Sub-case 5.3 (Stale Attempt Rejection & Attempt Governance)**:
     - Manager owns attempt increments and has advanced task `lane_x` to `attempt: 2`.
     - A delayed report `$RUN_ROOT/scen05-lane_x-a1.yaml` (`attempt: 1`) arrives.
     - Manager evaluates attempt number against current task state (`1 < 2`), flags report as obsolete, and quarantines it without rolling back attempt 2.
     - *Future attempt rule*: Any report with `attempt > current_attempt` is quarantined until the manager explicitly authorizes that attempt.
  4. **Sub-case 5.4 (Mutated Report with Same ID)**:
     - Report `scen05-task-z.yaml` is ingested with hash $H_1$.
     - Errant writer publishes a modified file under identical name `scen05-task-z.yaml` with hash $H_2 \neq H_1$.
     - Manager compares hash against recorded digest in `consumed_reports`, flags `mutated_report_rejected`, and rejects the file.
- **Pass/Fail & Observable Signals**:
  - **Pass**:
    - Unnotified `.yaml` file ingested during sweep.
    - `.partial` file skipped with zero parsing errors.
    - Stale attempt rejected with `disposition: obsolete_attempt_ignored`.
    - Mutated file rejected with `disposition: mutated_digest_mismatch`.
  - **Fail**: Manager crashes on `.partial` file; stale report overwrites new progress; mutated report accepted silently.
- **Evidence to Retain**:
  - Manager log entries detailing rejection reasons for sub-cases 5.2, 5.3, and 5.4.
- **Cleanup Boundary**:
  - Remove test files from `$RUN_ROOT`.

---

### SCEN-06: Deferred Follow-Up via Tab Keystroke (Exclusive Composer)

- **Objective**: Validate the specialized behavior of queued deferred follow-up input delivered via the `Tab` key in Codex CLI, demonstrating that it executes only after full multi-tool turn completion rather than at intermediate tool boundaries.
- **Classification**: `[HISTORICAL]` (Observed in probe `gZJMuX` during two-stage sleep); `[PROPOSED]` (Forward-test verification).
- **Prerequisites**:
  - Codex Manager pane executing a compound prompt requiring two distinct tool invocations in a single turn.
- **Execution Steps**:
  1. Submit compound task to Codex: `sleep 10 && sleep 10`.
  2. While Codex is running the first command, send text to pane composer:
     ```bash
     herdr pane send-text "$MANAGER_PANE_ID" "Deferred follow-up turn"
     ```
  3. Send `Tab` keystroke:
     ```bash
     herdr pane send-keys "$MANAGER_PANE_ID" tab
     ```
  4. Monitor terminal output across the transition from tool 1 to tool 2:
     ```bash
     herdr pane read "$MANAGER_PANE_ID" --source visible --lines 15
     ```
  5. Verify whether the deferred input triggers between tool 1 and tool 2, or waits until both tools conclude.
- **Pass/Fail & Observable Signals**:
  - **Pass**: The deferred text remains in the composer queue while tool 1 concludes and tool 2 begins. Only after tool 2 completes and the model concludes its entire conversational turn does the deferred text activate as a new turn.
  - **Boundary Restriction**: Because `send-text` followed by `tab` is a multi-step sequence requiring exclusive composer ownership, documentation must explicitly forbid `Tab` as the default fan-in mechanism.
  - **Fail**: Text executes prematurely between tools; text dropped; text rejected.
- **Evidence to Retain**:
  - Screen capture showing queued follow-up surviving across tool transitions.
- **Cleanup Boundary**:
  - Await completion of deferred turn.

---

### SCEN-07: Observer Wait Cancellation vs. Worker Survival

- **Objective**: Demonstrate that cancelling an active host observation command (`herdr agent wait`) does not terminate or corrupt the underlying worker agent process or its assigned task.
- **Classification**: `[HISTORICAL]` (Observed in probe `gZJMuX` with 45s wait killed via SIGINT); `[PROPOSED]` (Forward-test verification).
- **Prerequisites**:
  - Worker pane running long-running build or test command (`sleep 30`).
- **Execution Steps**:
  1. Launch background worker task in `$WORKER_PANE_ID`.
  2. Start synchronous wait in host shell:
     ```bash
     herdr agent wait "$WORKER_PANE_ID" --until idle --until done --timeout 60000
     ```
  3. While wait is pending, send SIGINT (`kill -INT <PID>` or Ctrl-C) strictly to the host `herdr agent wait` process.
  4. Inspect exit code of the wait command.
  5. Query worker agent status and process tree immediately:
     ```bash
     herdr agent get "$WORKER_PANE_ID"
     herdr pane process-info --pane "$WORKER_PANE_ID"
     ```
  6. Re-attach a new observer command:
     ```bash
     herdr agent wait "$WORKER_PANE_ID" --until idle --until done --timeout 45000
     ```
- **Pass/Fail & Observable Signals**:
  - **Pass**: Host wait command exits immediately with code 130 or non-zero. Worker pane remains in `working` status; foreground child PID remains active and unchanged. Re-attached wait attaches cleanly and unblocks when the worker eventually finishes.
  - **Fail**: Cancelling the wait kills the worker process; worker transitions to `unknown` or crashes back to shell.
- **Evidence to Retain**:
  - Host process exit code and PID logs showing worker continuity.
- **Cleanup Boundary**:
  - Allow worker command to complete normally.

---

### SCEN-08: Targeted Escape Interruption & Side-Effect Reconciliation

- **Objective**: Verify that sending an `Escape` key cleanly interrupts an active model turn without killing background orphan processes, and demonstrate mandatory side-effect reconciliation before retrying.
- **Classification**: `[HISTORICAL]` (Observed in probe `gZJMuX`); `[PROPOSED]` (Forward-test verification).
- **Prerequisites**:
  - Agent pane actively executing an iterative or looping task.
- **Execution Steps**:
  1. Inspect active screen to confirm target turn:
     ```bash
     herdr pane read "$WORKER_PANE_ID" --source visible --lines 20
     ```
  2. Send targeted Escape key:
     ```bash
     herdr pane send-keys "$WORKER_PANE_ID" esc
     ```
  3. Inspect screen to verify model interruption:
     ```bash
     herdr pane read "$WORKER_PANE_ID" --source visible --lines 20
     ```
  4. Inspect OS process tree to detect surviving background subprocesses:
     ```bash
     herdr pane process-info --pane "$WORKER_PANE_ID"
     ```
  5. Check Git index locks and uncommitted file modifications:
     ```bash
     git -C "$WORKER_CWD" status
     ls -la "$WORKER_CWD/.git/index.lock" 2>/dev/null || true
     ```
  6. Reconcile state: terminate any orphaned background process, clear stale locks, and inspect partial files before issuing resume instructions.
- **Pass/Fail & Observable Signals**:
  - **Pass**: Model turn interrupts cleanly with visible interruption notice. Process inspection reveals any surviving child processes. Stale locks are identified and cleared safely. Operator records pending effects before restarting.
  - **Fail**: Terminal hangs permanently; Esc causes entire PTY crash; operator blindly retries without reconciling background state.
- **Evidence to Retain**:
  - Process table output and git status before and after reconciliation.
- **Cleanup Boundary**:
  - Ensure working tree is clean and prompt is receptive before issuing new commands.

---

### SCEN-09: Manager Relinquishment, Crash Recovery & State Resume

- **Objective**: Validate that a crashed or stopped Codex Engineering Manager can be safely resumed by a fresh session without duplicating tasks or introducing dual-writer split-brain conflicts, with strict structural checkpoint validation of top-level keys and task/assignment mapping shapes (including a negative test for multiline indentation swallow).
- **Classification**: `[HISTORICAL]` (Observed in probe `gZJMuX` via session resume); `[PROPOSED]` (Forward-test verification).
- **Prerequisites**:
  - Established manager session with durable state recorded in `$RUN_ROOT/state.yaml`.
  - Active worker assignments in progress.
- **Execution Steps**:
  1. Simulate manager crash: terminate active manager process.
  2. **Relinquishment Verification**:
     - Verify that the previous manager terminal/process has fully terminated and relinquished write authority:
     ```bash
     herdr pane process-info --pane "$MANAGER_PANE_ID"
     ```
  3. Resume manager session using durable Herdr resume command:
     ```bash
     herdr agent start "herdr-engineering-manager" --kind codex --pane "$MANAGER_PANE_ID" -- --resume "$SESSION_ID"
     ```
  4. **Structural Checkpoint Validation**:
     Resumed manager executes structural validation on `$RUN_ROOT/state.yaml` before taking any operational actions:
     - **Top-Level Keys Assertion**: Must contain all mandatory top-level keys:
       `mission_id`, `approved_scope`, `status`, `manager`, `cto`, `report_root`, `repository`, `base_sha`, `worktree_root`, `delivery_hold`, `execution_boundary`, `runtime_selection`, `authoring_contract`, `ready_lane_briefs`, `task_graph`, `assignments`, `consumed_reports`, `decisions`, `action_log`, `pending_effects`, `recovery`.
     - **Task Graph Shape Assertion**: `task_graph` must be a discrete YAML mapping (dict), where each task key contains structured fields: `depends_on` (list), `state` (string), and `owner` (string). It must not be empty or a flat scalar.
     - **Assignments Shape Assertion**: `assignments` must be a discrete YAML mapping (dict), where each assignment key contains structured fields: `task_id` (string), `attempt` (integer), `pane_id` (string), `tab_id` (string), `terminal_id` (string), `runtime` (string), `model` (string), `worktree` (string), `branch` (string), and `owns` (string/list).
     - **Indentation & Literal Swallow Guard**: Explicit check confirming that multiline block scalars (e.g. `authoring_contract`, `ready_lane_briefs`) did not accidentally swallow subsequent top-level blocks (`task_graph:`, `assignments:`) due to indentation errors.
  5. **Negative Test Case: Indentation-Swallowed Structurally Corrupted Checkpoint**:
     - Operator/tester feeds a syntactically valid YAML checkpoint where an indentation defect in a multiline literal (`authoring_contract: | ...`) causes `task_graph` and `assignments` to be absorbed into the literal string instead of parsed as top-level mappings.
     - Resumed manager executes structural schema validation.
     - Resumed manager detects that `'task_graph' not in doc` or `'assignments' not in doc` or `not isinstance(doc['assignments'], dict)`.
     - Resumed manager halts with error:
       `structural_checkpoint_validation_failed: required top-level mapping 'task_graph' or 'assignments' missing (possible multiline indentation swallow). Refusing to resume.`
     - Resumed manager logs the structural defect, refuses to dispatch duplicate tasks or assume empty state, and escalates to CTO.
  6. **Valid Recovery Progression**:
     Once valid structure is confirmed, resumed manager scans `$RUN_ROOT/*.yaml` for unconsumed reports, inspects active worker panes via `herdr pane read` and `herdr agent get`, reconciles pending effects, and carries forward active work.
- **Pass/Fail & Observable Signals**:
  - **Pass**:
    - Valid checkpoint restores task graph and assignments without re-executing completed lanes; re-attaches observation handles to in-flight workers; emits recovery checkpoint.
    - Indentation-swallowed checkpoint fails structural validation with `structural_checkpoint_validation_failed`; manager halts cleanly without wiping state or duplicating tasks.
  - **Fail**: Manager attempts duplicate task dispatch; crashes due to stale lock; overwrites newer worker reports with old cached state; accepts an indentation-swallowed checkpoint and silently drops task graph or assignments.
- **Evidence to Retain**:
  - Resumed manager startup log and structural validation test results (both valid and corrupted cases).
- **Cleanup Boundary**:
  - Normal manager lifecycle.

---

### SCEN-10: Parallel Lane Allocation & Dynamic Capacity Refill

- **Objective**: Verify concurrent task execution across isolated Git worktrees, proving zero Git lock contention, independent commit histories, and dynamic capacity refill as lanes complete.
- **Classification**: `[SUPPORTED]` (Verified with 6 provisioned worktrees); `[PROPOSED]` (Forward-test validation).
- **Prerequisites**:
  - Repository baseline at clean SHA (`ce4dc7325241f8a3269047934c31131274019c7c`).
  - Worktree root outside main repo: `/Users/mac/docs/superpowers/worktrees/herdr-codex-first-20260920`.
- **Execution Steps**:
  1. Verify external worktree checkouts exist on distinct branches:
     - Lane A: `lane/report-contract` at `.../worktrees/.../report-contract`
     - Lane B: `lane/native-scenarios` at `.../worktrees/.../native-scenarios`
  2. Execute concurrent file modifications and local commits in Lane A and Lane B simultaneously.
  3. Verify that `git commit` in Lane A does not block or conflict with `git commit` in Lane B (`.git/index.lock` contention test).
  4. Complete Lane A; publish report; Manager receives handback.
  5. Manager observes capacity opening and immediately dispatches dependent Lane C (`lane/monitoring-recovery`) into its dedicated pre-provisioned worktree.
- **Pass/Fail & Observable Signals**:
  - **Pass**: Both lanes commit cleanly with distinct commit SHAs. Zero index lock collisions observed. Lane C dispatches immediately upon Lane A completion without waiting for Lane B.
  - **Fail**: Git lock collision aborts commit; files leak across worktree boundaries; dispatch blocked by static two-worker ceiling.
- **Evidence to Retain**:
  - Git commit logs from both worktrees showing concurrent commit timestamps.
  - Manager capacity log showing dynamic refill event.
- **Cleanup Boundary**:
  - Worktrees managed under standard mission lifecycle.

---

### SCEN-11: Clean-Context Exact-SHA Review Gate & Invalidation

- **Objective**: Validate technical review execution by an independent, fresh AGY session in a clean context window, evaluating against an exact commit SHA, and demonstrate that subsequent branch modifications invalidate stale reviews.
- **Classification**: `[PROPOSED]` / `[UNVERIFIED]` (Formal governance requirement from approved brief).
- **Prerequisites**:
  - Implementer finishes task on branch `lane/feature-x`, commits candidate `SHA_1`, and reports candidate.
- **Execution Steps**:
  1. Manager spawns a **fresh** AGY reviewer in a separate pane/tab (clean context, zero conversation memory).
  2. Reviewer checks out candidate at exact commit `SHA_1`:
     ```bash
     git checkout "$SHA_1"
     ```
  3. Reviewer inspects specification, coding standards, diff against base, and executes validation checks:
     ```bash
     git diff "$BASE_SHA"..."$SHA_1"
     python3 scripts/validate-skills.py
     ```
  4. Reviewer publishes review report: `review-candidate-SHA_1.yaml` (`verdict: approved`).
  5. **Invalidation Test**:
     - Implementer (AGY) makes an additional commit `SHA_2` on `lane/feature-x` and submits candidate notice with `candidate_head: SHA_2`.
     - Manager (Codex) inspects candidate notice from implementer specifying `candidate_head: SHA_2`.
     - Manager compares reported candidate HEAD (`SHA_2`) against reviewed SHA (`SHA_1`).
     - Because `SHA_2 != SHA_1`, manager marks previous review **stale/invalidated**.
     - Manager dispatches fresh AGY review on `SHA_2`.
- **Pass/Fail & Observable Signals**:
  - **Pass**: Reviewer executes in clean context without access to implementer conversational bloat; review is explicitly bound to `SHA_1`; commit `SHA_2` successfully invalidates review and blocks integration until re-reviewed.
  - **Fail**: Review conducted in dirty implementer pane; stale review accepted after branch HEAD advances; PR merged without binding exact SHA.
- **Evidence to Retain**:
  - Review report referencing exact candidate SHA.
  - Invalidation log entry in manager `state.yaml`.
- **Cleanup Boundary**:
  - Close reviewer pane upon review completion.

---

### SCEN-12: Safe Sequential Teardown & Evidence Preservation

- **Objective**: Validate the strict sequential cleanup protocol, verifying that finished tabs, panes, and worktrees are cleanly unmounted without data loss, that dirty worktrees are protected from blind force-deletion, and that mission evidence remains preserved under the appropriate delivery hold.
- **Classification**: `[SUPPORTED]` (CLI commands verified); `[PROPOSED]` (Forward-test verification).
- **Prerequisites**:
  - Finished lane with integrated commits and published reports in `$RUN_ROOT`.
- **Execution Steps**:
  1. Verify all reports, transcripts, and validation outputs are archived in `$RUN_ROOT` (outside the worktree).
  2. Check worktree git status:
     ```bash
     git -C "$WORKTREE_PATH" status --porcelain
     ```
  3. **Dirty Protection Check**:
     - If untracked or uncommitted files exist, `git worktree remove` without `--force` must fail and alert the operator.
     - Never issue `--force` unless explicit CTO/operator authorization is recorded.
  4. **Delivery Hold Enforcement**:
     - For mission `herdr-codex-first-20260920`: verify that the deliverable is handed back as a single integrated draft PR unmerged. Verify zero attempts to push to `origin/main` or merge the PR.
     - For general future production missions: verify authorized serial squash-merge via `gh pr merge --squash` only after candidate gate clearance.
  5. For clean worktree, execute sequential teardown:
     ```bash
     # 1. Close Herdr tab
     herdr tab close "$TAB_ID"
     # 2. Remove Git worktree
     git worktree remove "$WORKTREE_PATH"
     ```
  6. Verify removal:
     ```bash
     git worktree list | grep "$WORKTREE_PATH" || echo "CLEAN_REMOVED"
     herdr tab get "$TAB_ID" 2>&1 | grep "not found" || echo "TAB_CLOSED"
     ```
- **Pass/Fail & Observable Signals**:
  - **Pass**: Dirty worktrees reject deletion without explicit authorization. Clean worktrees unmount cleanly; Herdr tabs close; `$RUN_ROOT` evidence remains intact and accessible. Mission delivery hold respected (no main pushes/merges).
  - **Fail**: Force deletion destroys uncommitted work or unarchived logs; closed tab leaves orphaned zombie processes running; mission delivery hold violated by premature merge.
- **Evidence to Retain**:
  - Post-cleanup output of `git worktree list` and `herdr tab list`.
- **Cleanup Boundary**:
  - Complete mission teardown.

---

### SCEN-13: Cold Role Selection, Reference Routing & Authority Bounding

- **Objective**: Verify that every cold agent role (CTO, EM, Implementer, Reviewer, Integration Executor, Recovery Executor) reading the shared `skills/herdr/` skill graph discovers its authority, reads only role-relevant references, records its explicit role during registration, and that assigned AGY executors strictly refuse manager topology commands or bootstrapping a secondary manager hierarchy.
- **Classification**: `[SUPPORTED]` (Single graph in `skills/herdr/`); `[PROPOSED]` (Forward-test verification).
- **Prerequisites**:
  - Single shared skill definition at `skills/herdr/SKILL.md` and references in `skills/herdr/references/`.
  - Cold agent launched in a clean pane without prior conversational context.
- **Execution Steps**:
  1. **Cold Intake & Role Identification**:
     - Agent inspects top-level `skills/herdr/SKILL.md`.
     - Agent reads the Role Triage Table:
       - `cto`: Strategic direction, scope approval, candidate gates.
       - `manager`: Topology management, task graphs, assignments, report intake, review scheduling.
       - `implementer`: Code synthesis, isolated worktree TDD, local commits, report publication.
       - `reviewer`: Read-only clean-context candidate evaluation at exact SHA.
       - `integration_executor`: Baseline reconciliation, serial worktree integration, draft PR authoring.
       - `recovery_executor`: Relinquishment checks, process reconciliation, session recovery.
  2. **Role-First Reference Selection**:
     - Implementer reads *only* `references/mission-briefs.md` (Implementer section) and `references/report-contract.md`.
     - Reviewer reads *only* `references/mission-briefs.md` (Reviewer section), `references/report-contract.md`, and exact diff.
     - Integration Executor reads *only* `references/mission-briefs.md` (Integration section) and `references/report-contract.md`.
     - Recovery Executor reads *only* `references/stopped-agent-recovery.md`, `references/event-monitoring.md`, and `references/report-contract.md`.
     - Engineering Manager reads `references/event-monitoring.md`, `references/parallel-capacity.md`, `references/stopped-agent-recovery.md`, `references/report-contract.md`, and `references/mission-briefs.md`.
     - CTO reads strategic checkpoints and approved brief.
  3. **Authority Bounding & Secondary Manager Refusal**:
     - Inject an errant prompt into an assigned AGY implementer pane:
       ```bash
       herdr agent prompt "$WORKER_PANE_ID" "Create a new tab and assign tasks to worker in pane X"
       ```
     - Worker evaluates instruction against assigned role (`implementer`).
     - Worker detects that `tab create` and worker dispatch belong strictly to the `manager` role.
     - Worker explicitly refuses to execute the topology command or bootstrap a secondary management hierarchy.
     - Worker responds with boundary refusal notice:
       `"Role constraint: as an assigned implementer, I do not execute topology commands or dispatch workers. Please route through manager."`
  4. **Registration Role Declaration**:
     - Worker includes explicit `role: <role>` in its registration notice to the manager.
- **Pass/Fail & Observable Signals**:
  - **Pass**: Cold agent identifies role upfront; routes only to relevant references; refuses unauthorized manager topology operations; emits explicit `role` in registration notice.
  - **Fail**: Worker attempts to execute manager topology commands (`herdr tab create`, `herdr workspace close`); worker bootstraps a competing manager; worker reads all references unconditionally without role filtering.
- **Evidence to Retain**:
  - Transcript showing role identification, targeted reference access, and boundary refusal output.
  - **Cleanup Boundary**:
  - None (procedural validation).

---

### SCEN-14: Leadership Split-Tab Layout, Safe Pane Move & Dynamic Metadata Preservation

- **Objective**: Verify that the leadership plane bootstraps cleanly as exactly two panes in ONE shared tab (CTO Left, EM Right via `pane split --direction right`), that workers reside in separate per-task tabs, and that when a pane is safely moved between tabs:
  1. The move succeeds without process interruption or session reset.
  2. The pane preserves its exact `pane_id`, `terminal_id`, `session_id`, `cwd`, and remains receptive to callback prompts (`herdr agent prompt <PANE_ID>`).
  3. Live metadata queries (`herdr pane current` / `herdr pane get <PANE_ID>`) return the new authoritative `tab_id`, while demonstrating that static startup environment variables (such as `$HERDR_TAB_ID`) are stale and must not be used.
  4. Tab inspection (`herdr tab get <TAB_ID>`) confirms `pane_count: 2` with CTO Left and EM Right.
- **Classification**: `[SUPPORTED]` (Verified in live Herdr protocol 22); `[PROPOSED]` (Forward-test verification).
- **Prerequisites**:
  - Herdr server running (protocol 22).
  - CTO pane active in `$CTO_PANE_ID` within leadership tab `$LEADERSHIP_TAB_ID`.
- **Execution Steps**:
  1. **Leadership Cold Bootstrap (Right-Split from CTO)**:
     - From the CTO pane, execute a native right-split to allocate the Engineering Manager pane:
       ```bash
       herdr pane split "$CTO_PANE_ID" --direction right --no-focus
       # Captures returned .result.pane_id as $EM_PANE_ID
       ```
     - Launch Codex Engineering Manager in the new right-split pane:
       ```bash
       herdr agent start "herdr-engineering-manager" --kind codex --pane "$EM_PANE_ID" -- --model gpt-6-astra
       ```
     - Inspect leadership tab layout:
       ```bash
       herdr tab get "$LEADERSHIP_TAB_ID"
       ```
       Asserts that `.result.tab.pane_count == 2`.
     - EM executes `herdr pane current` and confirms `.result.pane.tab_id == "$LEADERSHIP_TAB_ID"`, matching the CTO's tab.
  2. **Worker Per-Task Tab Isolation**:
     - EM allocates a dedicated task tab for workers, verifying separation:
       ```bash
       herdr tab create --workspace "$HERDR_WORKSPACE_ID" --label "lane-worker" --no-focus
       ```
       Asserts worker `tab_id` is distinct from `$LEADERSHIP_TAB_ID`.
  3. **Safe Pane Move & Stale Environment Demonstration**:
     - Move an active pane into a target tab:
       ```bash
       herdr pane move "$PANE_ID" --tab "$TARGET_TAB_ID" --split right --target-pane "$TARGET_PANE_ID"
       ```
     - Query live metadata:
       ```bash
       herdr pane get "$PANE_ID"
       ```
       Asserts `.result.pane.tab_id == "$TARGET_TAB_ID"`.
     - Inside the moved pane's shell, compare live query against startup environment:
       ```bash
       LIVE_TAB=$(herdr pane current | jq -r .result.pane.tab_id)
       echo "Live: $LIVE_TAB | Startup Env: $HERDR_TAB_ID"
       test "$LIVE_TAB" = "$TARGET_TAB_ID"
       # Demonstrates that HERDR_TAB_ID retains its initial startup value, proving startup env is stale!
       ```
     - Assert physical identity continuity: `.result.pane.pane_id`, `.result.pane.terminal_id`, and `agent_session.value` remain unchanged across the move.
  4. **Callback Continuity Verification**:
     - Send an operational callback prompt to the moved pane:
       ```bash
       herdr agent prompt "$PANE_ID" "Verification notice post-move"
       ```
       Asserts prompt delivery exits code 0 with `{"type":"agent_prompted"}` and target activates without error.
- **Pass/Fail & Observable Signals**:
  - **Pass**:
    - Leadership tab contains exactly 2 panes (`pane_count: 2`) with CTO Left and EM Right.
    - Worker tab is separate and distinct.
    - Moved pane reflects new live `tab_id` via `pane current` / `pane get`.
    - Static startup `$HERDR_TAB_ID` is proven stale while live queries succeed.
    - Physical `pane_id`, `terminal_id`, session, and callback prompt reception remain completely intact post-move.
  - **Fail**:
    - EM launched in separate tab without right-split;
    - Pane move crashes process or resets session ID;
    - Code relies on stale `$HERDR_TAB_ID` and misroutes callbacks;
    - Prompt fails delivery after pane move.
- **Evidence to Retain**:
  - Output of `herdr tab get` showing 2-pane leadership layout.
  - Pre- and post-move JSON from `herdr pane get` demonstrating preserved identities and updated `tab_id`.
- **Cleanup Boundary**:
  - Preserved within mission layout lifecycle.

---

## 4. Forward-Test Controller Execution Protocol

When the native forward-test lane is activated, the testing controller must execute these scenarios following this protocol:

1. **Controller Supervisory Identity & Execution Seam**:
   - The forward-test lane is supervised by the native controller session (Codex supervisory lane).
   - **Strict Execution Authority Invariant**: All Git operations, workspace checkout inspections, test suite runs, and candidate artifact verifications are strictly performed by **AGY execution agents** (`agy` workers/executors). Scenario instructions must **never quietly direct Codex to perform engineering Git/test operations**. The supervisory controller dispatches prompts to AGY executor panes, which run the shell commands, git inspections, and verifications in their isolated environments.
2. **Candidate Artifact Binding (Zero Globally Mounted Fallback)**:
   - Before executing any scenario, the AGY executor (under controller coordination) must identify and record the exact candidate skill artifact and verify its owning candidate git worktree:
     ```bash
     # Explicit candidate skill path inside candidate worktree checkout
     CANDIDATE_SKILL_PATH="/Users/mac/docs/superpowers/worktrees/herdr-codex-first-20260920/integration/skills/herdr/SKILL.md"

     # Assert skill file exists at path; fail immediately on missing path
     test -f "$CANDIDATE_SKILL_PATH" || { echo "ERROR: Missing candidate skill at $CANDIDATE_SKILL_PATH" >&2; exit 1; }

     # Bind owning candidate repository/worktree explicitly (fail if detached or not in git repo)
     CANDIDATE_WORKTREE=$(git -C "$(dirname "$CANDIDATE_SKILL_PATH")" rev-parse --show-toplevel 2>/dev/null)
     test -n "$CANDIDATE_WORKTREE" || { echo "ERROR: Candidate skill path $CANDIDATE_SKILL_PATH is not in a git repository" >&2; exit 1; }

     # Compute candidate content digest
     CANDIDATE_SKILL_SHA256=$(shasum -a 256 "$CANDIDATE_SKILL_PATH" | awk '{print $1}')

     # Query exact candidate HEAD commit SHA directly from the owning candidate worktree (never from controller CWD!)
     CANDIDATE_HEAD=$(git -C "$CANDIDATE_WORKTREE" rev-parse HEAD)

     # Fail immediately on path, digest, or repository mismatch
     test -n "$CANDIDATE_HEAD" || { echo "ERROR: Failed to resolve candidate HEAD from $CANDIDATE_WORKTREE" >&2; exit 1; }
     ```
   - The controller and all participating AGY workers must strictly bind to this `CANDIDATE_SKILL_PATH` and verify matching `CANDIDATE_SKILL_SHA256` and `CANDIDATE_HEAD`.
   - **Strict Invariant**: A globally mounted skill (such as `~/.codex/skills/herdr/SKILL.md` or `~/.agents/skills/herdr/SKILL.md`) must **never** be passed off as the tested candidate. Any run where worker execution resolves to an unverified global skill is classified as an immediate test abort (`abort: unverified_global_skill_mounted`).
3. **Deterministic Sequence**:
   - *Wave 1 (Role, Leadership Topology & Discovery)*: Execute SCEN-13 (Role Selection & Authority), SCEN-14 (Leadership Split Layout, Safe Move & Dynamic Metadata), and SCEN-01 (Launch, Coordinates, Registration & Candidate Binding).
   - *Wave 2 (Handoffs & Intake)*: Execute SCEN-02 (Idle Handback), SCEN-03 (Busy Handback), SCEN-04 (Fan-In), and SCEN-05 (Fault-Tolerant Intake).
   - *Wave 3 (Recovery & Control)*: Execute SCEN-06 (Tab Deferred), SCEN-07 (Observer Cancellation), SCEN-08 (Esc Interruption), and SCEN-09 (Manager Relinquishment & Structural Checkpoint Resume with Negative Swallow Test).
   - *Wave 4 (Delivery & Teardown)*: Execute SCEN-10 (Parallel Capacity), SCEN-11 (Exact-SHA Review Gate), and SCEN-12 (Safe Teardown & Delivery Hold).
4. **Evidence Capture**: Every executed scenario must log its actual command invocations, stdout/stderr, exit codes, candidate path/SHA-256, and generated file hashes into an immutable YAML report under `/Users/mac/docs/superpowers/runs/herdr-codex-first-20260920/`.
5. **Honest Attribution**: If any scenario cannot be executed due to environment constraints or tool limitations, the controller must record `status: unverified` or `status: unsupported` with the precise failure evidence. No simulated or fabricated pass results are permitted.
