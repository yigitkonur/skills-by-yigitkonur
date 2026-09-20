# Recovery, Intervention & Reconciling Stopped Agents

Read this reference when an agent pane appears stalled, unresponsive, blocked on input, or halted unexpectedly. This document defines the diagnosis sequence, targeted intervention mechanics, process reconciliation procedures, and crash recovery across all Herdr orchestration roles.

For canonical blocker and checkpoint report schemas, route to [report-contract.md](report-contract.md).

---

## 1. Role Authority & Recovery Boundaries

**Runtime identity is not role identity.** Do not assume recovery authority simply because you operate from a command-capable runtime. Interventions must respect the explicit role hierarchy:

| Role | Recovery Authority & Scope | Invariant |
|---|---|---|
| **Implementer / Reviewer** | Local error handling within assigned worktree only. If blocked by external dependencies or tool failure, report a blocker to the manager. | **Strictly prohibited from sending keystrokes, prompts, or termination signals to peer panes.** |
| **Engineering Manager (EM)** | Full authority to diagnose worker panes, resolve modals, send targeted continuation prompts, or restart crashed worker sessions. | Must inspect viewport and process info before intervening. Never issue blind process kills. |
| **Recovery Executor** | Delegated by EM to unblock stalled lanes, reconcile task inventories, and recover interrupted checkout states. | Reports all intervention outcomes and unconfirmed side effects to the manager. |
| **CTO** | Strategic escalation point for mission-level blockers; authorizes EM session replacement if manager halts. If operating in a native Herdr pane, receives native PTY prompts without `--wait`; if on a non-pane host, observes via the manual-observation boundary. | Non-pane host operates through manual observation boundary without callback promises. |

---

## 2. Phase 1: Read & Introspect Before Intervening

### The Cardinal Rule: Read Before Targeted Action
Never inject prompts, keystrokes, or cancellation signals into an agent pane without first reading its live state. A silent or non-reporting agent is not necessarily broken—it may be reasoning, compiling, or awaiting modal input.

```bash
# 1. Read the 2D rendered viewport (modals, spinners, thinking progress, prompt cursor)
herdr agent read <TARGET> --source visible --lines 25

# 2. Read unwrapped terminal transcript (error messages, tracebacks, recent tool outputs)
herdr agent read <TARGET> --source recent-unwrapped --lines 50

# 3. Check underlying process state in the pane
herdr pane process-info --pane <PANE_ID>
```

### State Classification Matrix

| Observed Screen / Process State | Diagnosis | Required Action |
|---|---|---|
| **Spinner active / thinking text streaming** | Agent is actively generating or executing a tool call. | **Do NOT interrupt or prompt.** Renew bounded wait (`herdr agent wait <TARGET> --timeout 60000`). |
| **Modal prompt / arrow menu visible (`ask_question`, `[y/N]`)** | Agent is paused on interactive input (`agent_blocked`). | **Do NOT send text.** Use the Modal Bridge via `herdr agent send-keys` (Phase 2). |
| **Agent prompt resting idle (`? for shortcuts`, `>`)** | Agent finished its turn but did not send notification. | Inspect filesystem for `.partial` or `.yaml` reports. If absent, issue a continuation prompt. |
| **Shell prompt resting idle (`$`, `%`)** | Agent CLI process crashed or exited cleanly. | Reconcile background processes, then restart agent session (Phase 4). |
| **Terminal frozen on subshell command** | Tool execution hung or caught in infinite loop. | Send targeted `ctrl+c` interrupt (Phase 2). |
| **Visible quota / rate limit (429, ResourceExhausted)** | Model quota exhausted; neither dead worker nor successful idle. | **Do NOT retry blindly on same model.** Preserve partial artifacts and owned pending effects. Route to Quota & Rate-Limit Protocol (Section 3.5). |
| **`error.code: pane_not_found`** | Pane was closed or workspace corrupted. | Check `herdr pane list`; verify if pane was relocated. |

---

## 3. Phase 2: Targeted Intervention Protocols

### 1. The Modal Bridge (`herdr agent send-keys`)
When an agent stops at an interactive question or tool approval dialog, Herdr protects the terminal by rejecting prompts with `error.code: agent_blocked`.

Resolve the modal mechanically using pre-validated key tokens:
```bash
# Navigate down and select option
herdr agent send-keys <TARGET> down enter

# Confirm default yes prompt
herdr agent send-keys <TARGET> enter

# Cancel or dismiss interactive prompt
herdr agent send-keys <TARGET> esc
```

### 2. Targeted Escape (`esc`) Intervention
`esc` is a targeted intervention after reading visible screen evidence. It interrupts an active conversational turn or aborts a stuck model prompt:
```bash
herdr agent send-keys <TARGET> esc
```

> [!WARNING]
> **The Detached Background Process Hazard**: Pressing `esc` interrupts the interactive agent composer, but background tool commands or compilation scripts already dispatched to OS child subshells may continue running.
> Always inspect the native task inventory and process tree (`herdr pane process-info --pane <PANE_ID>`) after `esc` to verify whether background side effects persist.

### 3. Hung Tool Call Recovery (`ctrl+c`)
If an agent CLI is deadlocked on an unresponsive child process or long-running tool:
1. Send `ctrl+c` via Herdr key tokens:
   ```bash
   herdr agent send-keys <TARGET> ctrl+c
   ```
> [!WARNING]
> **TTY Raw-Mode & Application Semantics**:
> In interactive terminal sessions running in raw mode, `ctrl+c` transmits the ASCII byte `\x03` across the PTY. Unlike canonical (cooked) terminal mode where the TTY line discipline automatically signals the foreground process group with OS `SIGINT`, raw-mode byte delivery is consumed directly by the application's event loop.
> The application may handle, defer, or ignore `\x03`, and may or may not forward `SIGINT` to child processes running in subshells. Sending `ctrl+c` does not guarantee POSIX signal dispatch, does not prove child process termination, and leaves background child side effects (partial writes, file descriptor holds, lock acquisition) unknown.
2. Verify process state and terminal status:
   Never assume child termination. Always inspect `herdr pane process-info --pane <PANE_ID>` and read the visible screen (`herdr agent read <TARGET> --source visible --lines 15`) to confirm that child processes have actually exited and the agent has returned to a clean interactive prompt before sending further input.
3. If returned to prompt, issue a targeted continuation prompt.

### 4. Interactive Continuation Prompt
If the agent CLI is alive and sitting at its interactive prompt after an error or unexpected pause, send a single focused continuation prompt:
```bash
herdr agent prompt <TARGET> \
  "Your previous operation paused or encountered an error. Review terminal history, check git status, and resume from the last valid checkpoint."
```

### 5. Quota & Rate-Limit Recovery Protocol
When an agent pane encounters visible API rate limits or quota exhaustion (e.g. HTTP 429, `ResourceExhausted`):
1. **Neither Dead Worker Nor Successful Idle**:
   - The underlying agent process has not crashed back to a shell prompt, nor has it cleanly finished its turn or task.
   - Never treat a quota stall as clean task completion or idle settlement.
2. **Preserve Artifacts & Owned Pending Effects**:
   - Preserve unfinalized `.partial` reports under `report_root` and all in-progress worktree modifications.
   - Do not discard partial files or revert uncommitted working tree progress without inspection.
3. **Cease Blind Same-Model Retries**:
   - Repeatedly submitting continuation prompts (`herdr agent prompt`) or restarting the agent with the same exhausted model compounds rate limits and wastes mission time. Stop blind retries immediately upon observing quota exhaustion evidence.
4. **Authorized Available Model Re-registration Gate**:
   - Switching models is permitted **only** if an alternative model is explicitly authorized by mission policy and capacity allocations.
   - Model replacement requires verified native AGY explicit re-registration: relaunching or re-configuring the agent with the authorized `--model <AUTHORIZED_MODEL>` flag, updating the registered model in `state.yaml`, and adhering to the manager-owned `attempt` policy.
5. **Escalate Capacity Blocker**:
   - If no alternative model is authorized or available in the project capacity pool, publish an immutable blocker report (`requested_action: unblock_decision` / capacity blocker) with qualified screen evidence.
   - **Strictly Prohibited**: Making billing modifications, editing platform configuration files, or altering underlying agent frameworks.

---

## 4. Phase 3: Process Reconciliation vs. Blind Kills

### The No-Blind-Kills Invariant
**Strictly prohibited**: Executing `kill -9`, blanket `pkill -f <agent>`, or terminating processes without inventory. Blind process termination corrupts Git index files, orphans POSIX semaphores, and destroys partial work.

### Process Reconciliation Procedure
Before restarting an agent or retrying a task:
1. **Query Pane Processes**:
   ```bash
   herdr pane process-info --pane <PANE_ID>
   ```
2. **Reconcile Git Locks Across Worktrees**:
   In Git worktrees, `.git` is a gitlink file pointing to the repository's worktree administrative directory, not a directory itself. Never target `.git/index.lock` directly with static paths.
   Discover the actual lock path dynamically:
   ```bash
   LOCK_PATH="$(git -C "$WORKTREE_PATH" rev-parse --git-path index.lock)"
   if [ -f "$LOCK_PATH" ]; then
     # Check if an active process currently holds an open file descriptor on the lock
     if lsof "$LOCK_PATH" >/dev/null 2>&1; then
       echo "Lock $LOCK_PATH is actively held by a running process. Do NOT remove."
     else
       # Ensure prior git/tool processes in the pane are dead before removing
       herdr pane process-info --pane "$PANE_ID"
       rm -f "$LOCK_PATH"
     fi
   fi
   ```
   Never interpret a masked `lsof` failure as safe removal; verify whether the lock is actively held and confirm previous pane processes are dead before removing any lock.
3. **Reconcile Pending File Artifacts**:
   Check for unfinalized `.partial` report files under `report_root`. Reconcile whether the content is complete before removing or finalizing.

---

## 5. Phase 4: Restarting Crashed Agent Sessions

### The Live TUI Protection Rule
**Never execute `herdr agent start` over a live TUI.** Launching a new agent session into a pane that already hosts an active agent corrupts the terminal viewport, traps the cursor, and causes duplicate prompt consumption.

### Safe Restart Sequence
If and only if `herdr pane process-info` confirms the previous agent process has fully exited back to the shell:
1. Verify the pane is resting at a shell prompt (`$`, `%`):
   ```bash
   herdr pane read --source visible --lines 5 <PANE_ID>
   ```
2. Launch the agent using the configured model:
   ```bash
   herdr agent start <AGENT_NAME> --kind <KIND> --pane <PANE_ID> -- --model <MODEL>
   ```
3. Re-submit the mission brief, instructing the agent to carry forward existing worktree progress:
   ```bash
   herdr agent prompt <PANE_ID> \
     "Resuming task $TASK_ID (attempt $ATTEMPT). Worktree checkout at $WORKTREE_PATH contains prior progress. Reconcile git status, review report_root, and complete remaining criteria."
   ```

---

## 6. Phase 5: Manager Session Recovery & Resumption

If the Engineering Manager (EM) session crashes, freezes, or disconnects:

1. **Relinquishment Proof**:
   Before initializing a replacement manager, prove that the previous manager process has actually stopped or relinquished its authority. Disconnection alone is insufficient evidence of termination.
2. **State & Report Intake**:
   The incoming manager must read `state.yaml`, the approved plan, `decisions.md`, and all immutable YAML reports under `report_root`.
3. **Checkpoint Write & Resume Verification**:
   Never rely solely on YAML parse success. Indentation slips during context compaction or edits can silently swallow structured blocks into adjacent multiline scalar strings (e.g. common-brief indentation swallowing assignment-shaped text into a YAML literal) or misplace historical decision entries.
   Whenever writing or resuming `state.yaml`, verify both keys and internal shapes before proceeding:
   - **Top-Level Keys**: Verify presence of expected keys (`mission_id`, `status`, `manager`, `cto`, `report_root`, `task_graph`, `assignments`, `consumed_reports`, `decisions`).
   - **Assignment Shapes**: `assignments` must be a dictionary where each entry is a structured mapping containing `task_id`, `attempt`, `pane_id`, `tab_id`, and explicit file ownership—not a swallowed string literal.
   - **Task Graph Shapes**: `task_graph` entries must remain structured mappings with explicit `depends_on` sequences and valid lifecycle states.
   - **Writer vs. Reviewer Topology & Sole-Writer Invariant**: Distinguish write-enabled assignments (implementers, integration executors) from read-only reviewers. Every active writing assignment must have sole-writer ownership over its isolated checkout and designated writer pane. Read-only review assignments (auditing candidates via exact-SHA or detached snapshots) must be clearly designated as non-writers, ensuring no competing writers exist on the same surface while permitting concurrent reviewer checkouts.
   - **Decisions List**: Verify `decisions` remains an explicit sequence of entries and has not been absorbed by adjacent multiline scalar blocks.
   - **No New Parser/Framework**: Perform these checks using standard structural inspection; coordinate report schemas by pointer to [report-contract.md](report-contract.md) without introducing new artifact kinds or external parsing frameworks.
4. **Leadership Tab Topology & Invariants**:
   - The Engineering Manager (EM) shares the dedicated leadership tab with the CTO (two panes only: CTO on the left, EM on the right, sharing `tab_id`). Worker and reviewer lanes operate in separate tabs.
   - When recovering or resuming a manager session, preserve existing session identities; the CTO alone migrates live panes (such as moving live `p8`), and agents must never move, split, or restart live panes autonomously.
   - Cold bootstrap creates the EM pane via a right horizontal split from the CTO pane (`herdr pane split --direction right ...`) and verifies the shared `tab_id` and horizontal layout (CTO at x=0, EM to the right at x>0 via `herdr tab get` and `herdr pane layout`).
5. **Carry Valid Work Forward**:
   - Reconcile active assignments and consumed report digests.
   - Do NOT terminate or restart healthy worker lanes that are actively synthesizing code.
   - Re-establish observer handles on existing worker panes.
6. **Resumed Notice to CTO**:
   Check CTO registration in `state.yaml` / mission brief:
   - If the CTO is registered in a native Herdr pane (e.g. `$CTO_PANE_ID`, such as pane `w3H:p3`), dispatch a native notice prompt without `--wait`.
   - If the CTO is operating on a non-pane host, record the resumed milestone in `state.yaml` and publish a structured manager report for manual observation via the manual-observation boundary.

---

## 7. Phase 6: The Bounded Recovery Rule & Blocker Escalation

### The Rule of Two Failures
To prevent infinite retry loops and wasted tokens:
1. **Two Equivalent Failures**: If two consecutive recovery attempts for the same failure mode fail to advance the task, **stop all automated retries**.
2. **Preserve Evidence**: Capture the full terminal transcript to a diagnostic log:
   ```bash
   herdr agent read <TARGET> --source recent-unwrapped --lines 200
   ```
3. **Publish Immutable Blocker Report**:
   Create and publish a formal blocker report conforming to [report-contract.md](report-contract.md):
   - `status: blocked`
   - Match exact assigned `mission_id`, `task_id`, and `attempt` (producers never increment attempts unilaterally; corrections use fresh `report_id`s within the assigned attempt).
   - Record verified runtime/terminal coordinates (session UUID is optional when unexposed by runtime).
   - `blockers`: Structured list with unique ID, concrete description, reproduction evidence, options considered, and recommended path.
   - `requested_action: unblock_decision`
4. **Notify Supervisor**: Dispatch native notice without `--wait` to the discovered manager return pane (`$MANAGER_PANE_ID`).
