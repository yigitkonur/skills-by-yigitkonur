# Parallel Capacity, Candidate Composition & Finite Review

## 1. Disjoint Parallelism vs. Small Coupled Work

- **Small Coupled Work (Default)**: For interdependent files or coupled refactors within a skill or module, assign **one whole-change AGY writer** and **one independent reviewer**. Do not artificially fragment cohesive work into multiple lanes or spawn superfluous bootstrap/recovery agents merely because files differ.
- **Genuine Independence**: Where tasks produce separate verifiable outcomes, have stable interfaces, and touch disjoint writable surfaces, dispatch lanes concurrently in the same wave. Refill capacity as workers publish handbacks.

## 2. Early Coherent Local Candidate Path

To avoid unnecessary approval bottlenecks during multi-part tasks:
- **Local Scoped Composition**: A single designated AGY writer with whole-change ownership may sequentially prepare, implement, generate/package, and execute authorized repository/PR mechanics to produce a single integrated candidate for whole-candidate verification.
- **Composition is NOT Release Approval**: Composing a candidate locally bypasses redundant per-file lane gates, but does not waive final candidate evidence gates.
- **Clean Independent Review**: Independent review remains strictly separate from writing. The candidate undergoes fresh technical review by an independent reviewer.

## 3. Review Invalidation & Delta Decisions

- **Exact-SHA Review**: Technical review binds strictly to an exact commit SHA. Any subsequent commit, rebase, or fix pushes the branch HEAD to a new SHA ($SHA_2 \neq SHA_1$), automatically invalidating prior approvals.
- **New-HEAD Delta Decision**: When an implementer corrects a candidate and produces a new SHA, the same independent reviewer may evaluate the new HEAD via a focused delta and impact check on the changed diff, issuing an explicit decision for the new SHA. Automatic approval on commit advance is prohibited, but a full reset to an unfamiliar reviewer is not required.

## 4. Finite Review & Escalation Bounds

To prevent infinite review-and-fix loops:
- **Two-Failure / Two-Round Limit**: If two consecutive correction rounds or review attempts fail to resolve a blocker or achieve candidate approval, **stop blind automated retries**. A third attempt without an architectural change or explicit management unblock is prohibited.
- **No Automatic Approval**: Hitting the two-round boundary never implies automatic approval; it mandates a concrete escalation or changed approach.
- **Cosmetic Invariant**: Minor non-functional or cosmetic comments do not reopen a correction cycle once functional criteria and check gates are satisfied.

## 5. Serial Integration & Delivery Lifecycle

1. **Rebase**: Serially rebase verified candidate commits onto current baseline.
2. **Repository Checks**: Run complete project generator, validation, and test suites.
3. **Verification**: Verify exact rebased HEAD with passing check exits.
4. **Authorized Delivery**: Execute delivery actions authorized by the mission brief (e.g. unmerged draft PR hold, or authorized merge to main). General delivery follows actual mission authority and branch protections; draft/unmerged holds apply only when specified by the brief.

### Merge Conflict Ownership
Treat conflict resolution as standard engineering execution:
1. Rebase in the isolated worktree cleanly onto target baseline.
2. Resolve conflict markers with integrity, preserving upstream intent.
3. Re-verify with full test and validation suites.
4. Force-push with lease (`git push --force-with-lease`).
