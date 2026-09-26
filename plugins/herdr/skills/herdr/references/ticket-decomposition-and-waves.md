# Ticket Decomposition & Multi-Wave Orchestration

This reference details the mechanics of decomposing complex requirements, discussions, or bug reports into structured work tickets and scheduling them across dynamic dependency waves.

---

## 1. Vertical Tracer-Bullet Slicing

When preparing tasks for execution:

1. **Vertical End-to-End Slices**:
   - Each ticket cuts vertically through all required layers of the stack (data schema $\to$ business logic $\to$ service/API $\to$ UI/caller $\to$ tests).
   - Avoid horizontal slicing (e.g. do not create an "all schemas" ticket followed by an "all endpoints" ticket). Horizontal slicing creates un-testable partial states.
2. **Context-Bounded Sizing**:
   - Size each slice so that its specifications, modified code, test suite, and diff comfortably fit within a single agent's context window.
3. **Explicit Blocking Edges**:
   - Every ticket explicitly declares its blocking dependencies (`Blocked by: None` or `Blocked by: #101, #102`).
4. **Expand-Contract for Wide Refactors**:
   - When executing cross-cutting mechanical refactors across multiple callers:
     - **Phase 1 (Expand)**: Introduce the new interface or schema alongside the legacy version.
     - **Phase 2 (Migrate)**: Migrate call sites across disjoint, parallel worker lanes.
     - **Phase 3 (Contract)**: Deprecate and remove the legacy version once all call sites are verified.

---

## 2. Multi-Wave Parallelism Graph (DAG)

Organize tickets into a directed acyclic graph (DAG) to maximize concurrency across waves:

```
[ All Project Tickets ]
           │
           ▼
[ Wave 1: Disjoint Frontier ] ──────► Launch parallel worktrees (Max Parallelism)
           │ (all Wave 1 PRs merged)
           ▼
[ Wave 2: Direct Dependents ] ──────► Launch parallel lanes unblocked by Wave 1
           │ (all Wave 2 PRs merged)
           ▼
[ Wave 3+: Successive Waves ] ──────► Continue dynamically until DAG converges
```

### Wave Scheduling Rules:
- **Wave 1 (Frontier)**: All tickets with `Blocked by: None` that touch strictly disjoint writable surfaces are assigned to Wave 1 and launched immediately.
- **Wave 2**: Tickets gated directly on Wave 1 deliverables (e.g. consuming a newly created API schema or service).
- **Wave 3+**: Successive dependent waves. Dynamic scheduling continues until all dependency edges are satisfied and the DAG fully converges (no arbitrary 5-wave ceiling).
- **Wave Barriers Are For True Prerequisites Only**: Never introduce an artificial wave barrier based on incidental completion ordering. If Ticket B does not semantically depend on Ticket A, do not hold Ticket B back.

---

## 3. Continuous Feedback Loop & Wave Transitions

To ensure continuous progress without supervisor polling deadlock:

1. **Worker Handback Callback**:
   When an implementer completes its work and opens a candidate PR, it writes back to the supervisor without `--wait`:
   ```text
   REPORT: task_id=<ID> pr_url=<URL> head_sha=<SHA> status=DONE
   ```
2. **Immediate Review Dispatch**:
   The supervisor does NOT wait for other lanes in the wave to finish. As soon as Lane $i$ reports `DONE`, the supervisor immediately splits the task's tab right and prompts the reviewer.
3. **Reviewer Handback Callback**:
   When the reviewer completes verification and approves the candidate:
   ```text
   APPROVED: task_id=<ID> pr_url=<URL> head_sha=<SHA>
   ```
4. **Serial Integration & Wave Advancement**:
   - Approved PRs in the current wave are serially rebased and merged into the mission-authorized branch (see [serial-merge-and-conflicts.md](serial-merge-and-conflicts.md)).
   - Once all tickets in Wave $k$ are verified and merged, the supervisor unblocks and dispatches **Wave $k+1$**.
   - Announce wave completion via Herdr desktop toast:
     ```bash
     herdr notification show "Wave ${CURRENT_WAVE} Complete" \
       --body "All candidate PRs merged. Dispatching Wave $((CURRENT_WAVE + 1))." \
       --sound done
     ```
