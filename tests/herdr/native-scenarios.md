# Herdr Native Acceptance Scenarios & Forward-Test Specifications

## 1. Overview & Architecture Alignment

This document defines the runnable, finite acceptance scenarios for the Codex-first Herdr orchestration architecture within `skills-by-yigitkonur`. It establishes exact operational procedures for validating the hierarchical orchestration pattern:

$$\text{Codex CTO} \longrightarrow \text{Codex Engineering Manager (EM)} \longrightarrow \text{AGY Implementers / Fresh Reviewers / Integration Executors}$$

### 1.1 The 3-Axis Decoupling Invariant

All scenarios enforce explicit separation across three distinct state axes:

1. **Worker State (PTY & Screen Heuristics)**: `idle`, `working`, `blocked`, `done`, `unknown`. Represents the physical terminal and detected process status inside the Herdr pane.
2. **Observer State (Host Wait Handle)**: `none`, `waiting`, `settled`, `timed_out`. Represents the caller's synchronous observation handle (`herdr agent wait`). An observer timeout is never treated as a worker failure.
3. **Delivery State (Engineering Lifecycle)**: `assigned` $\to$ `implementing` $\to$ `committed_locally` $\to$ `clean_review` $\to$ `integrated_pr` $\to$ `candidate_gate`. Represents verified repository progress.

### 1.2 Evidence Classification & Integrity Taxonomy

To prevent speculative or fabricated claims, every scenario and observation in this catalog is strictly tagged under one of four integrity tiers:

- **`[HISTORICAL]`**: Empirical observations gathered during initial exploratory probes (e.g., probe environment `/tmp/herdr-native-probe.gZJMuX`, panes `w3H:p5`/`p6`/`p7`, tab `w3H:t5` on 2026-09-20). Serves as historical context and design rationale, not current execution claims.
- **`[SUPPORTED]`**: Functionality directly verified against the installed Herdr CLI (v0.9.0, protocol 22) and current runtime interfaces (`--help`, documented options, and observed JSON schemas).
- **`[PROPOSED]`**: Bounded, deterministic test procedures designed for execution by the forward-test controller lane.
- **`[UNVERIFIED]`**: Edge conditions, race conditions, or recovery branches that have not yet been executed in the current mission run and await forward-test execution.

### 1.3 Degraded AGY Mode Invariant

When Google Antigravity CLI (`agy`) launches inside a Herdr pane, agent detection heuristics may evaluate to `agent_status: unknown` if custom wrappers or local prompt formats mask standard detection markers.

**Operational Rule**: A status of `unknown` must **never** trigger automatic relaunch over an active TUI. If `herdr pane process-info --pane <PANE_ID>` confirms a live foreground AGY process and `herdr agent read <PANE_ID> --source visible` displays an active composer/prompt, the session is classified as **Degraded AGY Mode**. In this mode:
- Output is captured via `herdr agent read <PANE_ID> --source recent-unwrapped` or `--source visible`.
- Raw commands and test suites are executed via verified `herdr pane run <PANE_ID> <CMD>...`.
- Direct text and keys are delivered via `herdr pane send-text` and `herdr agent send-keys`.
- File handoffs are conducted via immutable YAML reports rather than relying on terminal detection transitions.

---

## 2. Acceptance Scenario Matrix

| Scenario ID | Name / Purpose | Target Runtime & Role | Integrity Status | Primary Verification Metric |
|---|---|---|---|---|
| **SCEN-01** | Launch, Coordinate Discovery & Native Registration | Codex EM & AGY Worker | `[SUPPORTED]` / `[PROPOSED]` | JSON coordinate extraction & registration notice acknowledgment |
| **SCEN-02** | Explicit AGY $\to$ Idle Codex Handback | AGY Worker $\to$ Codex EM | `[HISTORICAL]` / `[PROPOSED]` | Atomic report publication & manager turn activation |
| **SCEN-03** | Asynchronous Handback to Busy Codex (Enter at Tool Boundary) | AGY Worker $\to$ Codex EM | `[HISTORICAL]` / `[PROPOSED]` | Input queued in TUI; zero stdin corruption at tool boundary |
| **SCEN-04** | Multi-Sender Fan-In & Idempotent Intake | 2 AGY Workers $\to$ Codex EM | `[HISTORICAL]` / `[PROPOSED]` | Sequential ingestion; duplicate event ID ignored |
| **SCEN-05** | Fault-Tolerant Intake (Missed Notice, Partial, Stale, Mutated) | AGY Worker $\to$ Codex EM | `[PROPOSED]` / `[UNVERIFIED]` | Sweep catches unnotified; `.partial`, stale, and mutated rejected |
| **SCEN-06** | Deferred Follow-Up via Tab Keystroke (Exclusive Composer) | Controller $\to$ Codex EM | `[HISTORICAL]` / `[PROPOSED]` | Input deferred across tool executions until full turn completion |
| **SCEN-07** | Observer Wait Cancellation vs. Worker Survival | Host Shell $\to$ Worker Pane | `[HISTORICAL]` / `[PROPOSED]` | Host wait exits on SIGINT; worker process continues undisturbed |
| **SCEN-08** | Targeted Escape Interruption & Side-Effect Reconciliation | Controller $\to$ Worker/EM | `[HISTORICAL]` / `[PROPOSED]` | Turn interrupted; background processes and Git state reconciled |
| **SCEN-09** | Manager Relinquishment, Crash Recovery & State Resume | Resumed Codex EM | `[HISTORICAL]` / `[PROPOSED]` | Old writer relinquished; `state.yaml` and reports carried forward |
| **SCEN-10** | Parallel Lane Allocation & Dynamic Capacity Refill | Multiple AGY Workers | `[SUPPORTED]` / `[PROPOSED]` | Isolated worktree paths; zero git lock collision; capacity refill |
| **SCEN-11** | Clean-Context Exact-SHA Review Gate & Invalidation | Fresh AGY Reviewer | `[PROPOSED]` / `[UNVERIFIED]` | Independent audit at candidate SHA; rebase invalidates review |
| **SCEN-12** | Safe Sequential Teardown & Evidence Preservation | Integration Executor | `[SUPPORTED]` / `[PROPOSED]` | Clean unmount; zero dirty force deletes; durable logs preserved |

---

## 3. Detailed Acceptance Scenario Specifications

### SCEN-01: Agent Launch, Coordinate Discovery & Native Registration

- **Objective**: Verify clean launch of Codex and AGY agents in dedicated panes, deterministic extraction of native coordinates via JSON, and completion of the mandatory return-address registration handshake.
- **Classification**: `[SUPPORTED]` (CLI syntax and JSON parsing verified); `[PROPOSED]` (Acceptance run sequence).
- **Prerequisites**:
  - Herdr server running (protocol 22).
  - Target workspace allocated (`HERDR_WORKSPACE_ID`).
  - Available runtime models discovered (`gpt-6-astra` for Codex, `gemini-3.8-flash-high` for AGY).
- **Execution Steps**:
  1. Allocate dedicated tab and split pane:
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
  4. Worker submits registration notice to Manager pane (`$MANAGER_PANE_ID`) without `--wait`:
     ```bash
     herdr agent prompt "$MANAGER_PANE_ID" "Registration notice:
     - mission_id: herdr-codex-first-20260920
     - task_id: scen01_probe
     - attempt: 1
     - pane_id: $WORKER_PANE_ID
     - tab_id: $WORKER_TAB_ID
     - terminal_id: $WORKER_TERM_ID
     - runtime: agy
     - model: Gemini 3.8 Flash (High)
     - cwd: $WORKER_CWD
     Ready for assignment acknowledgment."
     ```
  5. Manager records worker identity in `state.yaml` under `assignments.<task_id>` and replies with assignment acknowledgment.
- **Pass/Fail & Observable Signals**:
  - **Pass**: `herdr pane current` returns valid JSON with non-empty string fields for `pane_id`, `tab_id`, and `cwd`. `herdr agent prompt` exits code 0 with `{"type":"agent_prompted"}`. Manager logs registration state as `verified_native_identity_and_received_notice`.
  - **Degraded Signal**: If `herdr agent get $WORKER_PANE_ID` shows `agent_status: unknown`, verify `herdr pane process-info --pane $WORKER_PANE_ID` shows live `agy` child process and proceed under Degraded AGY Mode.
  - **Fail**: Command exits non-zero; `pane current` emits unparseable non-JSON; prompt rejected with `agent_blocked`.
- **Evidence to Retain**:
  - Captured JSON from `herdr pane current`.
  - Exact registration payload logged in manager `state.yaml`.
- **Cleanup Boundary**:
  - Close test pane via `herdr pane close $WORKER_PANE_ID` if not reused.

---

### SCEN-02: Explicit AGY $\to$ Idle Codex Handback

- **Objective**: Validate the atomic report publication and notification pattern from a completed AGY worker to an idle Codex engineering manager.
- **Classification**: `[HISTORICAL]` (Observed in probe `gZJMuX`, pane `w3H:p5` $\to$ `w3H:p6`); `[PROPOSED]` (Forward-test verification).
- **Prerequisites**:
  - Codex Manager resting at idle prompt in pane `$MANAGER_PANE_ID` (verified via `herdr agent get $MANAGER_PANE_ID` reporting `agent_status: idle`).
  - AGY Worker in `$WORKER_PANE_ID` with completed task output.
  - Shared run directory exists outside worktrees: `$RUN_ROOT=/Users/mac/docs/superpowers/runs/herdr-codex-first-20260920`.
- **Execution Steps**:
  1. Worker writes immutable report to temporary partial path:
     ```bash
     REPORT_PATH="$RUN_ROOT/scen02-worker-a1-report.yaml"
     # Worker writes $REPORT_PATH.partial using apply_patch
     ```
  2. Worker verifies completeness and syntax of `.partial` file:
     ```bash
     python3 -c "import yaml; yaml.safe_load(open('$REPORT_PATH.partial'))"
     ```
  3. Worker atomically moves partial file to canonical `.yaml`:
     ```bash
     mv "$REPORT_PATH.partial" "$REPORT_PATH"
     ```
  4. Worker submits single-line notification to manager without `--wait`:
     ```bash
     herdr agent prompt "$MANAGER_PANE_ID" "Report published: report_id=scen02-worker-a1 report_path=$REPORT_PATH task_id=scen02 attempt=1 status=completed"
     ```
  5. Manager receives turn, reads `$REPORT_PATH`, verifies SHA-256 digest, records event in `consumed_reports`, and updates task graph.
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
     herdr agent prompt "$MANAGER_PANE_ID" "Notice: task_id=scen03 status=in_progress checkpoint=step_2"
     ```
  4. Observe manager terminal display via:
     ```bash
     herdr agent read "$MANAGER_PANE_ID" --source visible --lines 15
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
     - Worker A: `$RUN_ROOT/scen04-task-a.yaml` (`event_id: scen04.a.1`)
     - Worker B: `$RUN_ROOT/scen04-task-b.yaml` (`event_id: scen04.b.1`)
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
  - **Pass**: Both reports are ingested; manager's `consumed_reports` lists `scen04.a.1` and `scen04.b.1`; processed task count increments by exactly 2. The duplicate delivery of `scen04.a.1` is logged as a duplicate digest match and discarded without re-triggering task dispatch or state corruption.
  - **Fail**: Deadlock on concurrent prompts; duplicate prompt causes duplicate downstream action or task rollback; race condition corrupts `state.yaml`.
- **Evidence to Retain**:
  - Manager's `state.yaml` showing `consumed_reports` with exact SHA-256 hashes.
  - Action log recording idempotent duplicate skip.
- **Cleanup Boundary**:
  - Scoped to test run directory.

---

### SCEN-05: Fault-Tolerant Intake (Missed Notice, Partial, Stale, Mutated)

- **Objective**: Validate the robustness of the manager's intake engine against transmission failures, incomplete writes, stale attempts, and corrupted reports.
- **Classification**: `[PROPOSED]` / `[UNVERIFIED]` (Formal acceptance criteria defined in design specification).
- **Prerequisites**:
  - Shared run directory `$RUN_ROOT`.
  - Active Codex Manager running intake reconciliation loops.
- **Execution Steps**:
  1. **Sub-case 5.1 (Missed Notification)**:
     - Write valid report `$RUN_ROOT/scen05-unnotified.yaml`.
     - Intentionally suppress `herdr agent prompt`.
     - Manager initiates periodic checkpoint or ten-minute timeout sweep.
     - Manager scans `$RUN_ROOT/*.yaml`, detects unconsumed report, verifies digest, and consumes it.
  2. **Sub-case 5.2 (Partial Publication)**:
     - Worker creates `$RUN_ROOT/scen05-incomplete.yaml.partial`.
     - Manager intake sweep runs while `.partial` exists.
     - Manager explicitly ignores all files matching `*.partial`.
  3. **Sub-case 5.3 (Stale Attempt)**:
     - Manager advances task `lane_x` to `attempt: 2`.
     - A delayed report `$RUN_ROOT/scen05-lane_x-a1.yaml` (`attempt: 1`) arrives.
     - Manager evaluates attempt number against current task state, flags report as obsolete, and quarantines it without rolling back attempt 2.
  4. **Sub-case 5.4 (Mutated Report with Same ID)**:
     - Report `scen05-task-z.yaml` is ingested with hash $H_1$.
     - Malicious or errant writer publishes a modified file under identical name `scen05-task-z.yaml` with hash $H_2 \neq H_1$.
     - Manager compares hash against recorded digest in `consumed_reports`, flags `mutated_report_rejected`, and raises an alert.
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
     herdr agent send-keys "$MANAGER_PANE_ID" tab
     ```
  4. Monitor terminal output across the transition from tool 1 to tool 2:
     ```bash
     herdr agent read "$MANAGER_PANE_ID" --source visible --lines 15
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
     herdr agent read "$WORKER_PANE_ID" --source visible --lines 20
     ```
  2. Send targeted Escape key:
     ```bash
     herdr agent send-keys "$WORKER_PANE_ID" esc
     ```
  3. Inspect screen to verify model interruption:
     ```bash
     herdr agent read "$WORKER_PANE_ID" --source visible --lines 20
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

- **Objective**: Validate that a crashed or stopped Codex Engineering Manager can be safely resumed by a fresh session without duplicating tasks or introducing dual-writer split-brain conflicts.
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
  4. Resumed manager executes recovery sequence:
     - Read `$RUN_ROOT/state.yaml`.
     - Scan `$RUN_ROOT/*.yaml` for unconsumed reports.
     - Inspect active worker panes via `herdr agent get` and `herdr agent read`.
     - Reconcile pending effects without re-dispatching already completed or active tasks.
- **Pass/Fail & Observable Signals**:
  - **Pass**: Resumed manager restores task graph from `state.yaml`; recognizes completed lanes without re-executing them; re-attaches observation handles to in-flight workers; emits recovery checkpoint.
  - **Fail**: Manager attempts duplicate task dispatch; crashes due to stale lock; overwrites newer worker reports with old cached state.
- **Evidence to Retain**:
  - Resumed manager startup log and reconciled `state.yaml`.
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
     - Implementer makes an additional commit `SHA_2` on `lane/feature-x`.
     - Manager checks current branch HEAD: `git rev-parse HEAD` returns `SHA_2`.
     - Manager compares current HEAD against reviewed SHA (`SHA_1`).
     - Because `SHA_2 != SHA_1`, manager marks previous review **stale/invalidated**.
     - Manager dispatches fresh review on `SHA_2`.
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

- **Objective**: Validate the strict sequential cleanup protocol, verifying that finished tabs, panes, and worktrees are cleanly unmounted without data loss, that dirty worktrees are protected from blind force-deletion, and that mission evidence remains preserved.
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
  4. For clean worktree, execute sequential teardown:
     ```bash
     # 1. Close Herdr tab
     herdr tab close "$TAB_ID"
     # 2. Remove Git worktree
     git worktree remove "$WORKTREE_PATH"
     ```
  5. Verify removal:
     ```bash
     git worktree list | grep "$WORKTREE_PATH" || echo "CLEAN_REMOVED"
     herdr tab get "$TAB_ID" || echo "TAB_CLOSED"
     ```
- **Pass/Fail & Observable Signals**:
  - **Pass**: Dirty worktrees reject deletion without explicit authorization. Clean worktrees unmount cleanly; Herdr tabs close; `$RUN_ROOT` evidence remains intact and accessible.
  - **Fail**: Force deletion destroys uncommitted work or unarchived logs; closed tab leaves orphaned zombie processes running.
- **Evidence to Retain**:
  - Post-cleanup output of `git worktree list` and `herdr tab list`.
- **Cleanup Boundary**:
  - Complete mission teardown.

---

## 4. Forward-Test Controller Execution Protocol

When the native forward-test lane is activated, the testing controller must execute these scenarios following this protocol:

1. **Controller Identity**: The forward-test lane is driven by a fresh native Codex controller session, communicating with native AGY workers as executors.
2. **Deterministic Sequence**: Execute SCEN-01 through SCEN-04 as the baseline connectivity wave. Execute SCEN-05 through SCEN-09 as the recovery and fault-tolerance wave. Execute SCEN-10 through SCEN-12 as the parallel capacity and delivery wave.
3. **Evidence Capture**: Every executed scenario must log its actual command invocations, stdout/stderr, exit codes, and generated file hashes into an immutable YAML report under `/Users/mac/docs/superpowers/runs/herdr-codex-first-20260920/`.
4. **Honest Attribution**: If any scenario cannot be executed due to environment constraints or tool limitations, the controller must record `status: unverified` or `status: unsupported` with the precise failure evidence. No simulated or fabricated pass results are permitted.
