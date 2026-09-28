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

## 2. Dynamic Dependency DAG & Wave Advancement

Organize tickets into a directed acyclic graph (DAG) to maximize concurrency across waves:

```
[ All Project Tickets ]
           │
           ▼
[ Frontier Lanes ] ────────► Launch parallel worktrees (Tickets with Blocked by: None)
           │
           ├──────────────────────────────┐
           │ (Ticket #1 integrated)       │ (Ticket #2 in progress)
           ▼                              ▼
[ Downstream Lane A ]          [ Downstream Lane B ]
(Unblocked by #1 immediately;  (Still waiting on #2;
 advances without waiting for  does not block Lane A)
 unrelated tickets)
```

### Wave Scheduling Rules:
- **Prerequisite-Driven Advancement**: A ready lane advances as soon as its actual prerequisite dependency edges are satisfied and execution capacity exists. Never introduce an artificial wave barrier based on incidental completion ordering. If Ticket B depends only on Ticket A, Ticket B launches as soon as Ticket A is integrated, even if other tickets in Ticket A's wave are still running.
- **Dynamic Convergence**: Successive dependent lanes launch dynamically until all dependency edges are satisfied and the DAG fully converges (no arbitrary 5-wave ceiling).
- **Optional Tracking Infrastructure**: Formal GitHub issues and pull requests are optional mechanisms used when authorized. Herdr operates equally on local Git branches (`branch_name=<BRANCH>`) without requiring GitHub CLI or remote issue trackers.

---

## 3. Continuous Feedback Loop & Streaming Integration

To ensure continuous progress without supervisor polling deadlock:

1. **Worker Handback Callback**:
   When an implementer completes its work, it writes back to the supervisor without `--wait`:
   ```text
   REPORT: task_id=<ID> head_sha=<SHA> branch_name=<BRANCH> [pr_url=<URL>] status=DONE
   ```
2. **Capacity-Aware Review Dispatch**:
   The supervisor does NOT wait for other lanes to finish. As soon as Lane $i$ reports `DONE`, the supervisor provisions reviewer capacity when available (splitting the task pane if width $\ge 161$ cols, or opening a review tab) and prompts the reviewer.
3. **Reviewer Handback Callback**:
   When the reviewer completes verification and approves the candidate:
   ```text
   APPROVED: task_id=<ID> head_sha=<SHA> branch_name=<BRANCH> [pr_url=<URL>]
   ```
4. **Serial Integration & Lane Dispatch**:
   - Approved candidates are serially rebased and merged into the mission-authorized target branch (see [serial-merge-and-conflicts.md](serial-merge-and-conflicts.md)).
   - As each candidate lands, the supervisor evaluates the DAG: any downstream tickets whose blocking dependencies are now cleared are unblocked and dispatched immediately.
   - Milestone notifications may be broadcast via Herdr desktop toast:
     ```bash
     herdr notification show "Task ${TASK_ID} Integrated" \
       --body "Candidate ${HEAD_SHA} merged. Unblocking dependent lanes." \
       --sound done
     ```
