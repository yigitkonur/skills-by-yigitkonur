---
name: herdr
description: "Use if orchestrating coding agents, parallel subagents, isolated Git worktrees, and clean-context PR reviews using the Herdr multiplexer."
---

# Herdr

Herdr is an external multiplexer and supervisor control plane for interactive AI coding agents (OpenAI Codex CLI, Google Antigravity CLI / AGY, Claude Code, Cursor, and Gemini). It decouples topology (`workspace` → `tab` → `pane`), OS processes (`pty`), and cognitive agents (`agent`), enabling a supervisor to orchestrate multiple workers concurrently without trapping them in headless subshells or blinding human operators.

Orchestration follows an explicit chain of authority: **CTO** → **Engineering Manager (EM)** → **AGY Implementers, Fresh Reviewers, Integration Executors, and Recovery Executors**.

---

## 1. Role Selection (Cold Reader Intake)

Every cold reader identifies its assigned role first. The same skill and references are read by all participants; role determines which sections to execute and which to skip.

| Assigned Role | Authority & Scope | Execute | Skip |
|---|---|---|---|
| **CTO** | Strategic governance, architectural gates, candidate evidence sign-off. Bounded EM observation via compact reads and report reconciliation when notices are missing. | §1, §2 (conditional), §7 references | §3–§6 execution (delegate to EM) |
| **Engineering Manager (EM)** | Central orchestration: `state.yaml`, task dispatch, capacity, report intake, reviewer Q/A relay, milestone publication. | §1–§7 | Direct feature code authoring; pushing to `main` |
| **Implementer** | Feature implementation, TDD, local commits, atomic report publication in assigned worktree. | §1, §2, §3, §4 (own work), §7 references | Editing `state.yaml`; managing peers; bootstrapping management |
| **Fresh Reviewer** | Independent read-only audit of exact candidate commit SHA in clean context. | §1, §2, §5, §7 references | Editing production code; advancing branches; spawning subagents |
| **Integration Executor** | Baseline reconciliation, worktree provisioning, serial rebase, packaging validation, delivery mechanics. | §1, §2, §6, §7 references | Parallel drafting; merging without candidate gate approval |
| **Recovery Executor** | Bounded diagnostic probes, process reconciliation, Git lock clearing, crashed session restart. | §1, §2, §7 (recovery reference) | Blind kills (`kill -9` / `pkill`); relaunching over live TUIs |

> [!IMPORTANT]
> **No Management Hierarchy Bootstrapping**: Assigned AGY roles select only execution and evidence paths. Never infer you are an orchestrator, spawn nested subagent hierarchies, or modify `state.yaml`. All multi-agent coordination flows through the designated EM.

> [!IMPORTANT]
> **Runtime Is Not Role**: Execution engine (`codex`, `agy`, `claude`) does not define organizational role. Mission briefs assign role authority. The fleet uses heterogeneous model tiers suited to each role.

---

## 2. Discover, Register, Verify

### 2a. Verify Herdr Environment

```bash
test "${HERDR_ENV:-}" = 1 || echo "WARNING: Not inside a Herdr-managed pane"
```

CTO may operate outside a Herdr pane (e.g., terminal session or API). When `HERDR_ENV` is unset, the CTO uses bounded EM observation via report files and compact `herdr agent read` commands targeted at known pane IDs — without discovering own pane coordinates.

### 2b. Discover Own Coordinates (Pane Roles Only)

Agents running inside Herdr panes discover their own identity:

```bash
SELF_PANE_ID="${HERDR_PANE_ID:-$(herdr pane current | jq -r .result.pane.pane_id)}"
SELF_TAB_ID="${HERDR_TAB_ID:-$(herdr pane current | jq -r .result.pane.tab_id)}"
SELF_TERM_ID="${HERDR_TERMINAL_ID:-$(herdr pane current | jq -r .result.pane.terminal_id)}"
SELF_CWD="$(herdr pane current | jq -r .result.pane.cwd)"
```

Self-coordinates identify *this* agent. They are distinct from the supervisor's return address, which is provided in the mission brief as `$MANAGER_PANE_ID`.

### 2c. Verify Actual TUI Runtime and Model

Before accepting assignment, verify the actual active model matches the requested model. Launch arguments alone are not proof:

1. Check runtime identity via native TUI controls (e.g., AGY model menu, Codex status bar).
2. Record both `requested_model` and `observed_model` in registration.
3. If they differ, report before substituting — do not silently proceed with the wrong model.

### 2d. Worker Registration

Register confirmed identity with the manager's return address. Do not use `--wait`:

```bash
herdr agent prompt "$MANAGER_PANE_ID" \
  "Registration: task=$TASK_ID attempt=$ATTEMPT mission=$MISSION_ID status=registered \
   pane=$SELF_PANE_ID tab=$SELF_TAB_ID terminal=$SELF_TERM_ID \
   runtime=$RUNTIME requested_model=$REQUESTED_MODEL observed_model=$OBSERVED_MODEL \
   cwd=$SELF_CWD."
```

The manager acknowledges registration before releasing the assignment. Registration without acknowledgment is not authorization to begin engineering work.

---

## 3. Bound, Decompose, Assign (EM)

The EM decomposes the mission into independently verifiable tasks with disjoint ownership:

- **One writer per writable surface**. Concurrent writers use separate worktrees in task-owned external paths or verified ignored locations. Never share worktrees.
- **Dispatch all ready disjoint work in the same wave**. Reviews proceed while other writers continue. Refill capacity as workers publish handbacks.
- **Begin with 2 concurrent workers** as calibration when host limits are unknown, then scale to available capacity. No permanent cap.
- **Serialize heavy builds and integration** (compiler leases, full test suites, serial rebase). Parallelize code drafting and diff review.
- **Worktree allocation**: Use task-owned external roots or explicitly scoped ignored paths. The `.worktrees/` convention requires confirmation that the path is actually gitignored or external; do not assume it.

### Tab and Pane Allocation

```bash
herdr tab create --workspace "$WS_ID" --cwd "$WORKTREE_PATH" --label "$TASK_ID" --no-focus
herdr pane split --pane "$PANE_ID" --direction right --cwd "$WORKTREE_PATH" --no-focus
```

---

## 4. Execute (AGY Workers)

### 4a. Implementation

Write failing test first (Red). Satisfy with minimal code (Green). Commit locally with conventional message. Preserve prior commits on the branch.

### 4b. Candidate Handback

When work is complete (or blocked), publish an immutable YAML report to the shared run root and notify the manager. The report and publication pipeline follow the canonical contract in [references/report-contract.md](references/report-contract.md).

**Notice** — push to manager return pane without `--wait`:

```bash
herdr agent prompt "$MANAGER_PANE_ID" \
  "REPORT NOTICE: mission_id=$MISSION_ID task_id=$TASK_ID attempt=$ATTEMPT \
   report_id=$REPORT_ID pane_id=$SELF_PANE_ID tab_id=$SELF_TAB_ID \
   report_path=$REPORT_PATH status=$STATUS requested_action=$ACTION"
```

- Workers must **never** pass `--wait` when notifying. `--wait` blocks the worker and causes callback deadlocks if the manager prompts back.
- Messages are the primary notification mechanism. Bounded native observation and report reconciliation serve as fallback for missing feedback — not always-wake guarantees.
- **Tab** is optional deferred input requiring exclusive composer ownership. Never use Tab for urgent alerts or operational fan-in; Enter is the operational default.

### 4c. Push Notification Mechanics

- **Bracketed Paste**: Wraps text in DEC Mode 2004 (`\x1b[200~...\x1b[201~`), preventing premature execution.
- **300ms Staged Enter Delay**: Pause before transmitting `\r` (Enter), preventing dropped characters.
- **`herdr agent wait`**: Event-driven kernel wait. Timeout is in milliseconds. Default settled states: `idle`, `done`, `blocked`. A start timeout means the agent has not transitioned yet — it is not proof of launch failure.

```bash
herdr agent wait <target> --until idle --until done --until blocked --timeout <MS>
```

An observer timeout is not a worker failure. An idle worker is not a completed mission. `unknown` remains unknown — settlement grants permission to inspect screen and filesystem evidence, not to assume outcome.

---

## 5. Independent Review (Fresh Context)

### 5a. Clean-Context Exact-SHA Review

Spawn a fresh AGY reviewer in a dedicated pane. The reviewer checks out the exact candidate commit SHA with zero context pollution:

```bash
herdr pane split --pane "$PARENT_PANE_ID" --direction right --cwd "$REVIEW_PATH" --no-focus
# In the review pane:
git checkout <CANDIDATE_SHA>
```

Never review code in the implementer's active pane. Reviews may proceed while other writers continue on disjoint tasks.

### 5b. Review Invalidation

Review binds strictly to an exact commit SHA. Any subsequent commit or rebase that changes HEAD automatically invalidates the prior review. A fresh review is required on the new HEAD.

### 5c. Repair Cycle

If changes are requested, the original implementer fixes in its worktree and publishes a new candidate handback with the updated SHA. The review cycle repeats from §5a.

---

## 6. Serial Integration & Delivery

The Integration Executor combines verified lane commits into a single integrated candidate:

1. **Rebase** each verified lane onto current baseline, resolving conflicts.
2. **Run repository validation and generation** per the target repo's documented checks.
3. **Verify** exact integrated HEAD with full test suite. Exact changed HEAD invalidates all prior reviews and checks — revalidation is required.
4. **Deliver** as authorized by the mission (e.g., draft PR handed back unmerged, or authorized merge). Future merge guidance belongs in the mission brief, not hardcoded here.

> [!IMPORTANT]
> Integration is serial. Parallel writers produce candidates; the Integration Executor combines them one at a time into a verified moving baseline. Never merge without passing the candidate evidence gate.

---

## 7. Cleanup & Evidence-Preserving Handback

### 7a. Cleanup Rules

- Clean up only **owned, completed, clean** resources. Verify no unresolved operations or pending effects before removal.
- Archive evidence (reports, transcripts, test output) before removing worktrees or closing tabs.
- No default force removal. Reconcile Git index locks (`.git/index.lock`) and unfinalized `.partial` files before restarting sessions.
- Follow strict order: verify report published → archive evidence → close tab (`herdr tab close`) → remove worktree (`git worktree remove`).

### 7b. Mission Handback

Publish a final immutable handback report to the shared run root with:
- Exact candidate HEAD, branch, identity, model, skill path revision.
- Evidence summary and check results.
- Pending effects and unknown side effects (if any).
- Integration dependencies that remain unresolved.

Notify the manager (and CTO via EM) without `--wait`.

---

## Screen Inspection & Recovery

### Read Sources

| Source | Syntax | Use |
|---|---|---|
| `recent-unwrapped` | `herdr agent read <T> --source recent-unwrapped --lines <N>` | **Default**: transcripts, code, LLM output. Merges soft wraps. |
| `visible` | `herdr agent read <T> --source visible --lines <N>` | **Modals**: questionnaires, spinners, confirmation prompts. |
| `recent` | `herdr agent read <T> --source recent --lines <N>` | **Columnar**: ASCII diagrams, tables, aligned grids. |
| `detection` | `herdr agent read <T> --source detection` | **Heuristic**: regex rule introspection (`herdr agent explain`). |

If `recent-unwrapped` cannot display a full deliverable on the Alternate Screen, read the published report file directly from disk.

### Modal Bridge

When an agent is `blocked` on interactive confirmation, Herdr rejects `herdr agent prompt` with `error.code: agent_blocked`. Resolve mechanically:

1. Inspect: `herdr agent read <target> --source visible --lines 20`
2. Respond: `herdr agent send-keys <target> down enter`

### Degraded AGY Mode

When Herdr detection reports `unknown` for a known AGY process:

1. Confirm foreground AGY via `herdr pane process-info --pane <PANE_ID>`.
2. Verify visible composer via `herdr agent read <TARGET> --source visible`.
3. Use `herdr pane run <PANE_ID> <COMMAND>...` as verified fallback (injects text + Enter). Never use on an unverified shell or relaunch over a live TUI.

### Targeted Intervention

- **`esc`**: Interrupts stuck prompts or active turns. May leave background work running with unknown side effects. Always inspect process inventory and owned effects afterwards.
- **`ctrl+c`**: Terminates the foreground child command. Verify return to interactive prompt. Does not guarantee all background processes stopped — inspect owned process tree.
- **No blind kills**: Never use blanket `kill -9` or `pkill`. Reconcile state before restart.

Detailed recovery runbooks: [references/stopped-agent-recovery.md](references/stopped-agent-recovery.md).

---

## Durable Artifacts

Two kinds of durable mission artifact:

1. **Mutable Manager Checkpoint**: `state.yaml` alone in the shared run root. Maintained exclusively by the EM.
2. **Immutable YAML Reports**: Producer reports (`<task>-a<attempt>-<purpose>.yaml`) and manager milestones (`manager-m<N>-<purpose>.yaml`), published atomically to the shared run root.

All report schemas, the atomic publication pipeline, notice format, consumption semantics, idempotent digest checks, and reviewer Q/A protocol are defined in [references/report-contract.md](references/report-contract.md).

### Reporting Invariants

- **Manager alone increments attempts**. Producers match their assigned `attempt`.
- **Idempotent consumption**. Manager records SHA-256 digests; duplicate notices are no-ops; mutated same-ID reports are rejected.
- **Receipt is not approval**. Report receipt updates `state.yaml`; task advancement requires independent technical review.
- **10-minute silent boundary**. If operating without external notice or state transition for 10 minutes, publish a checkpoint at the next safe tool boundary.

---

## Canonical References

| Reference | When to Read | Topics |
|---|---|---|
| [references/report-contract.md](references/report-contract.md) | Authoring, publishing, validating, or consuming reports. | YAML schema, atomic publication pipeline, notice format, consumption semantics, digest checks, reviewer Q/A. |
| [references/event-monitoring.md](references/event-monitoring.md) | Supervising terminals, reading Alt-Screen, delivering prompts, diagnosing unknown states. | Screen inspection buffers, bracketed paste, no-wait constraints, Tab input, modal bridge, degraded mode. |
| [references/stopped-agent-recovery.md](references/stopped-agent-recovery.md) | Unblocking stalled, modal-blocked, hung, or crashed sessions. | Diagnosis matrix, modal resolution, targeted `esc`/`ctrl+c`, Git lock reconciliation, safe TUI restart. |
| [references/mission-briefs.md](references/mission-briefs.md) | Dispatching tasks or receiving assignments. | Brief templates, coordinate discovery, acceptance criteria, callback mandate. |
| [references/parallel-capacity.md](references/parallel-capacity.md) | Planning concurrency waves or managing worktrees. | Capacity calibration, resource invariants, build leases, dependency waves, delivery lifecycle, exact-SHA review invalidation. |
