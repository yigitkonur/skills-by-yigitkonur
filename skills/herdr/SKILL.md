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
> **Runtime Is Not Role**: Execution engine (`codex`, `agy`) does not define role.

---

## 2. Discover, Register, Verify

### Leadership Topology (CTO → EM)
The leadership hierarchy resides in **exactly two panes within ONE shared tab**: CTO (LEFT) and EM (RIGHT). Workers and reviewers are allocated to separate, per-task tabs.

CTO starts Codex EM on the right. EM registers with CTO. EM then dispatches workers/reviewers as needed.

### Live Coordinates (All Panes)
Always use live native records via `herdr pane current`. Do NOT trust static startup environment variables (e.g., `HERDR_TAB_ID`) for topology decisions, as panes may move.

```bash
SELF_PANE_ID="$(herdr pane current | jq -r .result.pane.pane_id)"
SELF_TAB_ID="$(herdr pane current | jq -r .result.pane.tab_id)"
SELF_TERM_ID="$(herdr pane current | jq -r .result.pane.terminal_id)"
SELF_CWD="$(herdr pane current | jq -r .result.pane.cwd)"
```

### Registration & Acknowledgment
Verify requested vs observed model before accepting assignment. Register confirmed identity with the manager's return address without `--wait`.
- **Preflight match** (identity, model, and role all verified as authorized): May proceed without waiting for explicit ACK.
- **Preflight mismatch, unclear authority, or restart/relaunch context**: Preserve explicit acknowledgment before proceeding.

---

## 3. Bound, Decompose, Assign (EM)

The EM runs a continuous loop: **report intake** → **strict identity/evidence decision** → **next ready dispatch or escalation** → **checkpoint**.

- **Small Work Default**: Default to 1 writer and 1 independent reviewer for a cohesive unit of work.
- **Parallel Capacity**: Dispatch all ready disjoint work in the same wave. Refill capacity as workers publish handbacks. True parallelism requires independent results; do not artificially spawn multiple workers for interdependent files.
- **Checkpointing**: Maintain `state.yaml` with active state and pending effects. Do not copy historical transcripts. Read past reports from disk when needed.

---

## 4. Execute (AGY Implementers)

- **Implementation**: Make minimal changes to satisfy the spec. If the task is code, use red/green TDD. If the task is documentation, TDD is not required. Commit locally.
- **Handback**: Publish an immutable YAML report and send a notice to the manager (no `--wait`).
- **Communication**: Enter is the default. Tab is optional and requires exclusive composer ownership. See [references/event-monitoring.md](references/event-monitoring.md).

---

## 5. Independent Review (Fresh Context)

- **Exact-SHA Review**: Reviews are explicitly bound to an exact commit SHA. EM dispatches a fresh reviewer to audit the candidate. Unconditional `git checkout` is unsafe in a shared read-only worktree; allocate a separate exact-SHA checkout only if tests mutate state or the author must continue working simultaneously.
- **Delta Review**: If the implementer modifies the branch and produces a new SHA, the old review is invalidated. The same independent reviewer can perform a delta review on the new HEAD, checking only the changed diff and impacted rules. The reviewer explicitly issues a new decision for the new HEAD.

---

## 6. Serial Integration & Delivery

Integration combines verified lane commits into a single integrated candidate.

1. **Rebase** onto current baseline.
2. **Run repository checks** (generation, validation, formatting).
3. **Verify** exact integrated HEAD.
4. **Deliver** as authorized (e.g., unmerged draft PR). Never push to `main` directly.

---

## 7. Cleanup & Handback

- Clean up only **owned, completed, clean** resources.
- Archive evidence before removing worktrees (`git worktree remove`) or closing tabs. Do not force-delete dirty worktrees without authorization.
- Final Handback: Publish final YAML report to the run root with exact HEAD, check results, unresolved effects.

---

## Canonical References

| Reference | Use |
|---|---|
| [report-contract.md](references/report-contract.md) | Authoring, publishing, consuming immutable reports. |
| [event-monitoring.md](references/event-monitoring.md) | Terminal supervision, prompt delivery, degraded AGY mode. |
| [stopped-agent-recovery.md](references/stopped-agent-recovery.md) | Targeted recovery, quota limits, session resume. |
| [mission-briefs.md](references/mission-briefs.md) | Dispatch templates, role acceptance criteria. |
| [parallel-capacity.md](references/parallel-capacity.md) | Planning concurrency waves, exact-SHA invalidation. |
