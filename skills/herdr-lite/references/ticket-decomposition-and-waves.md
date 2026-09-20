# Ticket Decomposition & Multi-Wave Orchestration

This reference codifies the self-contained ticket extraction logic (derived from `/to-tickets`) and the multi-wave dependency scheduling system (up to 5 waves) for Herdr-Lite.

---

## 1. Automatic Ticket Intake & GitHub Issue Creation

When Herdr-Lite is invoked without pre-existing GitHub issues (e.g. from an architectural discussion, a debugging session, a Sentry triage, or a PRD spec), it automatically extracts structured tickets without requiring manual user intervention.

### A. Vertical Tracer-Bullet Rules
- **Vertical Slices**: Each ticket cuts a narrow but complete vertical path through the stack (database/schema $\to$ business logic $\to$ API/service $\to$ UI/caller $\to$ tests). Avoid horizontal slicing (e.g. do not create an "all database tables" ticket followed by an "all endpoints" ticket).
- **Single Context Window**: Each slice is sized to comfortably fit within a single agent's context window.
- **Explicit Blocking Edges**: Every ticket explicitly declares its `Blocked by:` dependencies. Tickets with no blockers are ready for immediate Wave 1 dispatch.
- **Wide Refactor Exception**: For cross-cutting mechanical refactors (e.g. renaming a core database column or retyping a monorepo shared interface), use **expand-contract**:
  1. Expand: Introduce the new form alongside the old.
  2. Migrate: Update call sites in disjoint batches.
  3. Contract: Remove the deprecated form once all call sites are migrated.

### B. Automated GitHub Issue Creation
The orchestrator publishes each ticket directly to GitHub using `gh issue create`:

```bash
gh issue create \
  --title "fix(core): isolate browser coordinator teardown (#181)" \
  --body "## What to build
Isolate browser resource allocation and add explicit cleanup guards during cancellation.

## Acceptance criteria
- [ ] Implement SIGINT/cancellation cleanup handler in coordinator
- [ ] Add behavioral vitest coverage verifying process termination
- [ ] Zero unhandled promise rejections on task abortion

## Blocked by
None (can start immediately)"
```

---

## 2. Multi-Wave Parallelism Graph (Waves 1 to 5)

Herdr-Lite arranges issues into a directed acyclic graph (DAG) to maximize parallelism across as few waves as possible. Most projects converge within 1 or 2 waves; up to 5 waves are supported:

```
[ All Created Issues ]
           │
           ▼
[ Wave 1: Disjoint Frontier ] ──────► Launch N parallel worktrees (Max Parallelism)
           │ (all Wave 1 PRs merged)
           ▼
[ Wave 2: Direct Dependents ] ──────► Launch parallel worktrees unblocked by Wave 1
           │ (all Wave 2 PRs merged)
           ▼
[ Wave 3: Integration / Polish ] ───► Final consumers and cleanup tasks
```

### Wave Classification Rules:
- **Wave 1 (Frontier)**: All tickets with `Blocked by: None` that touch disjoint writable surfaces are assigned to Wave 1 and launched immediately in parallel worktrees.
- **Wave 2**: Tickets that depend strictly on Wave 1 deliverables (e.g. consuming a newly added API endpoint or database table).
- **Waves 3–5**: Multi-stage follow-ups, contract deprecations, or final end-to-end telemetry sweeps.

---

## 3. "Write Back to Me" Continuous Feedback Loop

To ensure the multi-agent pipeline never stalls or deadlocks, every assigned implementer is instructed to send a structured completion report back to the orchestrator:

### The Implementer Callback Protocol:
When an implementer completes its code and opens a PR, it writes back to the orchestrator:
```text
REPORT: task_id=<ID> pr_url=<URL> head_sha=<SHA> status=DONE
```

### Continuous Streaming Transition:
1. **Immediate Tab 2 (Review) Spawn**:
   The orchestrator does not wait for other lanes in the wave to finish. As soon as Lane $i$ outputs `DONE`, the orchestrator immediately spawns **Tab 2 (`review`)** in Workspace $i$.
2. **Reviewer Callback**:
   When the reviewer completes review-and-fix and posts GitHub PR approval, it writes back:
   ```text
   APPROVED: task_id=<ID> pr_url=<URL> head_sha=<SHA>
   ```
3. **Wave Transition Gate**:
   - Approved PRs in the current wave are serially rebased and merged to `main` (see [serial-merge-and-conflicts.md](serial-merge-and-conflicts.md)).
   - Once all tickets in Wave $k$ are merged, the orchestrator automatically unblocks and launches **Wave $k+1$**.
   - A Herdr notification announces the wave transition:
     ```bash
     herdr notification show "Wave ${CURRENT_WAVE} Completed" \
       --body "All PRs merged. Dispatching Wave $((CURRENT_WAVE + 1))." \
       --sound done
     ```
