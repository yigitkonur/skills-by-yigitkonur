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
| **CTO** | Strategic escalation point for mission-level blockers; authorizes EM session replacement if manager halts. | Non-pane host operates through manual observation boundary. |

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
If an agent CLI is permanently deadlocked on an unresponsive child process:
1. Send `ctrl+c` to terminate the hung child process:
   ```bash
   herdr agent send-keys <TARGET> ctrl+c
   ```
2. Read the visible screen to verify that the agent returned to its interactive prompt:
   ```bash
   herdr agent read <TARGET> --source visible --lines 15
   ```
3. If returned to prompt, issue a targeted continuation prompt.

### 4. Interactive Continuation Prompt
If the agent CLI is alive and sitting at its interactive prompt after an error or unexpected pause, send a single focused continuation prompt:
```bash
herdr agent prompt <TARGET> \
  "Your previous operation paused or encountered an error. Review terminal history, check git status, and resume from the last valid checkpoint."
```

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
2. **Reconcile Git Locks**:
   If an interrupted process left `.git/index.lock` behind:
   - Check whether any Git process is actively holding the lock:
     ```bash
     lsof "$WORKTREE_PATH/.git/index.lock" 2>/dev/null || true
     ```
   - If no process holds the file descriptor and the previous process is dead, safely remove the stale lock:
     ```bash
     rm -f "$WORKTREE_PATH/.git/index.lock"
     ```
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
3. **Carry Valid Work Forward**:
   - Reconcile active assignments and consumed report digests.
   - Do NOT terminate or restart healthy worker lanes that are actively synthesizing code.
   - Re-establish observer handles on existing worker panes.
4. **Resumed Notice to CTO**:
   Notify the CTO pane (`$CTO_PANE_ID`) of the resumed manager session with current milestone state.

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
