# Parallel Capacity, Resource Allocation & Streaming Reviews

This reference defines capacity management, concurrency bounds, resource locking, model fidelity, internal subagent accounting, early coherent candidate composition, and streaming review mechanics in Herdr.

---

## 1. Disjoint Parallelism vs. Small Coupled Work

1. **Small Coupled Work (Default)**:
   - For interdependent files, refactors within a single skill or module, or coupled architectural changes: assign **ONE whole-change writer** and **ONE independent reviewer**.
   - Do NOT artificially fragment cohesive code changes across multiple workers merely because multiple files are touched. Fragmenting coupled work creates unresolvable merge races and semantic drift.
2. **Genuine Independence**:
   - Concurrency is warranted ONLY when tasks produce disjoint verifiable deliverables, maintain stable contract interfaces, and touch strictly disjoint writable file surfaces.
   - Refill worker capacity dynamically as active workers publish completed handbacks.

---

## 2. Capacity Bounds, Model Fidelity & Internal Subagents

1. **Model & Effort Fidelity**:
   - Model and effort selections **strictly follow user instructions**.
   - Never invent speculative tier names or enforce mandatory downgrades to "flash".
   - Never silently downgrade reasoning models without explicit user authorization.
2. **Native Internal Subagent Accounting**:
   - When workers spawn native internal subagents (where the runtime supports them), those subagents consume active host resources and API rate limits.
   - **Count internal subagents in total capacity**: Schedulers must account for internal worker subagents within host concurrency limits so that overall host load remains bounded.
3. **Rate Limits & 429 Quota Throttling**:
   - If an agent encounters API rate limiting (`RESOURCE_EXHAUSTED` / 429), **immediately pause new lane dispatch**.
   - Bounded retries apply (max 2 equivalent failures stop retries). Sequence runs until rate limits reset.

---

## 3. Early Coherent Candidate Composition

To avoid unnecessary approval bottlenecks during multi-part tasks:
- **Local Scoped Composition**: A single designated writer with whole-change ownership may sequentially prepare, implement, generate/package, and execute authorized repository checks locally to produce a single integrated candidate for whole-candidate verification.
- **Composition is NOT Release Approval**: Composing a candidate locally bypasses redundant per-file lane gates, but does NOT waive final candidate verification gates.
- **Clean Independent Review**: Independent review remains strictly separate from writing. The candidate undergoes fresh technical review by an independent reviewer at its exact commit SHA.

---

## 4. Resource Allocation: Reservation vs. Delivered Grant

When managing scarce host resources (e.g. exclusive compiler instances, database ports, GPU slots, or native build locks):

- **Reservation is NOT a Grant**: A resource reservation in a planning document or manager state does NOT equal a delivered grant.
- **One Exclusive Owner**: Only one agent may hold an exclusive lock or heavy resource at a time.
- **Verification Gate**: Supervisors must verify that a previous owner has fully released a resource (and child processes have terminated) before granting access to a dependent worker.

---

## 5. The Streaming Reviews Law (No Whole-Fleet Wait)

> [!CAUTION]
> **The Whole-Fleet Wait Trap**:
> Orchestrators must NEVER execute an unbounded blocking wait for every worker in a wave to finish before initiating reviews.
> Waiting for the entire fleet stalls delivery, starves reviewer capacity, and creates massive serial integration backlogs.

### Streaming Review Protocol:
1. **Decoupled Per-Lane Transitions**:
   - Reviews stream dynamically. The instant *any* worker reports `DONE` or submits candidate code, immediately split that task's pane right (`herdr pane split --direction right --no-focus`) and prompt its reviewer.
   - Finished tasks never sit idle waiting for slower tasks in the same wave.
2. **Non-Blocking Supervisor Monitoring**:
   - Supervisors monitor active lanes using short, bounded timeouts (`herdr agent wait <lane> --timeout 5000`) or periodic inspection sweeps.
   - When a review passes, it enters the serial integration queue immediately.

---

## 6. Finite Review Bounds & Failure Budgets

To prevent endless automated review-and-fix ping-pong:

1. **Two-Round Failure Budget**:
   - If two consecutive correction rounds between implementer and reviewer fail to achieve candidate approval or resolve check errors, **stop automated retries immediately**.
   - Escalate the concrete technical blocker, conflicting requirements, and trade-offs to the supervisor or user.
2. **No Artificial Budget Resets**:
   - Read-only tool movements, changing error message IDs, rephrasing prompts, or switching model tiers do NOT reset the failure budget. Real progress requires resolving the underlying failure.
3. **No Material Waivers**:
   - Material defects (failing tests, broken contracts, security issues) cannot be downgraded to "advisory" or waived to force an approval.
4. **Cosmetic Invariant**:
   - Non-functional or purely stylistic suggestions do not trigger an extra correction round once functional requirements pass.
