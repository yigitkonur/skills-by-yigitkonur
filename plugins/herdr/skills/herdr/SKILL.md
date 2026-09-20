---
name: herdr
description: "Use if orchestrating coding agents, parallel subagents, isolated Git worktrees, and clean-context PR reviews using the Herdr multiplexer."
---

# Herdr

Herdr is a multiplexer and supervisor control plane for AI coding agents. It decouples topology (`workspace` → `tab` → `pane`), OS processes (`pty`), and cognitive agents.

Orchestration follows an explicit chain: **CTO** → **Engineering Manager (EM)** → **AGY Executors**.

---

## 1. Role Selection (Cold Reader Intake)

Every cold reader identifies its assigned role first. Read only the sections and references for your role.

| Assigned Role | Authority & Scope | Execute | Skip |
|---|---|---|---|
| **CTO** | Strategic governance, architectural gates, candidate evidence sign-off. | §1, §2 (CTO path) | §3–§6 execution (delegate to EM) |
| **Engineering Manager (EM)** | Central orchestration: `state.yaml`, task dispatch, report intake, reviewer scheduling, milestone publication. | §1–§7 | Direct feature code authoring; pushing to `main` |
| **Implementer** | Feature implementation, local commits, atomic report publication in assigned worktree. | §1, §2, §4, references/report-contract.md | §3 (EM-only); editing `state.yaml` |
| **Fresh Reviewer** | Independent read-only audit of exact candidate commit SHA in clean context. | §1, §2, §5, references/report-contract.md | §3, §4, §6; editing production code |
| **Integration/Recovery**| Worktree integration or bounded diagnostic probes/recovery. | §1, §2, §6, references/stopped-agent-recovery.md | §3–§5 |

> [!IMPORTANT]
> **No Management Bootstrapping**: Assigned AGY roles select only execution and evidence paths. Never infer you are an orchestrator or spawn nested subagents.
> **Runtime Is Not Role**: Execution engine (`codex`, `agy`) does not define organizational role.

---

## 2. Discover, Register, Verify

### 2a. Cold Bootstrap Sequence (CTO → EM → Workers)

Before workers exist, the CTO establishes the leadership pair. Leadership resides in **exactly two panes in ONE shared tab**: CTO on the LEFT, EM on the RIGHT. Workers and reviewers run in separate per-task tabs.

1. **CTO creates the EM pane** via horizontal right split, then launches Codex EM with authorized model/effort into the returned shell pane:
   ```bash
   herdr pane split --pane "$CTO_PANE_ID" --direction right --cwd "$RUN_ROOT" --no-focus
   herdr agent start "herdr-engineering-manager" --kind codex --pane "$EM_PANE_ID" -- --model "$EM_MODEL"
   ```
2. **Verify Leadership Topology**:
   Confirm SAME tab, exactly two panes, CTO left (x=0) and EM right (x>0):
   ```bash
   herdr tab get "$LEADERSHIP_TAB_ID"
   herdr pane layout "$LEADERSHIP_TAB_ID"
   ```
3. **CTO dispatches EM brief** with mission scope, run root path, CTO return address (`$CTO_PANE_ID`), and authorized model tiers.
4. **EM allocates workers/reviewers** into separate dedicated tabs and launches native AGY:
   ```bash
   herdr tab create --workspace "$WS_ID" --cwd "$TASK_CWD" --label "$TASK_LABEL" --no-focus
   herdr agent start "$AGENT_LABEL" --kind agy --pane "$WORKER_PANE_ID" -- --model "$WORKER_MODEL"
   ```
5. **Session Invariant**: Preserve existing healthy sessions; never run duplicate bootstrap or launch a new agent over a live TUI. Check installed `--help` for syntax rather than guessing.
6. **Non-Pane CTO Boundary**: When the CTO operates from a Root PTY outside Herdr, explicit-target CLI commands (`herdr agent read`, etc.) work, but native prompt callbacks targeting the CTO do not exist (`cto.pane_id: null`). The CTO reads reports and `state.yaml` directly from the shared run root on disk.

### 2b. Live Coordinates & Model Verification (All Panes)

Always resolve live coordinates via `herdr pane current`. Do NOT trust static startup environment variables (e.g. `HERDR_TAB_ID`) as panes may move:
```bash
SELF_PANE_ID="$(herdr pane current | jq -r .result.pane.pane_id)"
SELF_TAB_ID="$(herdr pane current | jq -r .result.pane.tab_id)"
SELF_TERM_ID="$(herdr pane current | jq -r .result.pane.terminal_id)"
SELF_CWD="$(herdr pane current | jq -r .result.pane.cwd)"
```

`herdr pane current` confirms physical coordinates, but does NOT prove active model or composer readiness. Verify active model and effort independently via native runtime indicators (e.g. TUI footer/menu).

### 2c. Registration & Acknowledgment

Register confirmed identity with the manager's return address without `--wait`:
- **Preflight match** (identity, model, and role verified as authorized): Proceed directly without waiting for explicit ACK.
- **Preflight mismatch, unclear authority, or restart/relaunch context**: Preserve explicit acknowledgment before proceeding.

---

## 3. Bound, Decompose, Assign (EM)

The EM runs a continuous loop: **report intake** → **strict identity/evidence decision** → **next ready dispatch or escalation** → **checkpoint**.

- **Small Work Default**: Default to 1 writer and 1 independent reviewer for a cohesive coupled unit of work.
- **Parallel Capacity**: Dispatch all ready disjoint work in the same wave. Refill capacity as workers publish handbacks. True parallelism requires independent results; do not artificially spawn multiple workers for interdependent files.
- **Checkpointing**: Maintain `state.yaml` with active state, ownership, dedupe index, and pending effects. Do not copy historical transcripts. Read past reports from disk when needed.

---

## 4. Execute (AGY Implementers)

- **Implementation**: Make minimal changes to satisfy the spec. If the task changes application code, use appropriate behavioral tests (TDD). Documentation changes are exempt from mandatory red/green TDD. Commit locally.
- **Handback**: Publish an immutable YAML report via the verified 4-step pipeline and send a concise notice to the manager (no `--wait`). See [references/report-contract.md](references/report-contract.md).
- **Communication**: Plain questions and routine progress use short native messages with Question ID, context, and return route. Enter is the default. Tab is optional and requires exclusive composer ownership. See [references/event-monitoring.md](references/event-monitoring.md).

---

## 5. Independent Review & Early Candidate Path

- **Exact-SHA Review**: Reviews bind strictly to an exact commit SHA in clean context. The reviewer verifies the candidate SHA in a frozen read-only checkout. Unconditional `git checkout` is unsafe in a shared read-only worktree; allocate a separate exact-SHA checkout only if tests mutate state or the author must continue working simultaneously. Reviewers audit code, tests, and diffs; reviewers never author fixes or inherit EM dispatch authority.
- **Delta Review**: If the implementer modifies the branch and produces a new SHA, the old review is invalidated. The same independent reviewer can perform a delta review on the new HEAD, checking only the changed diff and impacted rules. The reviewer explicitly issues a new decision for the new HEAD.
- **Early Coherent Local Candidate Path**: Scoped work may be composed locally for whole-candidate checks and review without requiring redundant per-file lane approvals. Local composition is not release approval. One AGY writer may sequentially prepare, write, generate/package, and execute authorized PR mechanics with explicit ownership, keeping independent review separate.
- **Review Loop Bounds**: Two equivalent failed corrections or two review/fix rounds require a changed approach or concrete escalation, never a third blind retry or automatic approval. Cosmetic issues do not reopen a cycle.

---

## 6. Serial Integration & Delivery

Integration combines verified lane commits into a single integrated candidate:

1. **Rebase** onto current baseline.
2. **Run repository checks** (generation, validation, formatting).
3. **Verify** exact integrated HEAD.
4. **Deliver** as authorized by the mission brief (e.g. draft PR handed back unmerged, or authorized merge to main). General delivery follows actual mission authority and branch protections; draft/unmerged holds apply only when specified.

---

## 7. Cleanup & Handback

- Clean up only **owned, completed, clean** resources.
- Archive evidence before removing worktrees (`git worktree remove`) or closing tabs. Do not force-delete dirty worktrees without authorization.
- Final Handback: Publish final immutable YAML report to the run root with exact HEAD, check results, unresolved effects.

---

## Canonical References

| Reference | When to Read | Topics |
|---|---|---|
| [references/report-contract.md](references/report-contract.md) | Authoring, publishing, validating, or consuming reports. | YAML schema, atomic publication pipeline, notice format, consumption semantics, digest checks, reviewer Q/A. |
| [references/event-monitoring.md](references/event-monitoring.md) | Supervising terminals, reading Alt-Screen, delivering prompts, diagnosing unknown states. | Screen inspection buffers, bracketed paste, no-wait constraints, Tab input, modal bridge, degraded mode, model verification. |
| [references/stopped-agent-recovery.md](references/stopped-agent-recovery.md) | Unblocking stalled, modal-blocked, hung, or crashed sessions. | Diagnosis matrix, modal resolution, targeted `esc`/`ctrl+c`, Git lock reconciliation, safe TUI restart, quota recovery (§4.6). |
| [references/mission-briefs.md](references/mission-briefs.md) | Dispatching tasks or receiving assignments. | Common authority block, role additions (implementer/reviewer/integrator), coordinate discovery, callback mandate. |
| [references/parallel-capacity.md](references/parallel-capacity.md) | Planning concurrency waves or managing worktrees. | Disjoint parallelism, early coherent candidate path, review invalidation, finite review bounds, delivery authority. |
