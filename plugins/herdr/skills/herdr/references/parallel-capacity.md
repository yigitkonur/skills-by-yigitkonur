# Parallel Capacity & Integration

## 1. Disjoint Parallelism
True parallelism requires independent results.
- **Independent Verifiable Outcomes**: Each lane produces a self-contained, testable deliverable.
- **Disjoint Writable Surfaces**: No two concurrent lanes may own or write to the same files.

Dispatch all ready disjoint work in the same wave. Refill capacity as workers publish handbacks. Do not artificially spawn multiple workers for interdependent files.

## 2. Independent Review
When a worker finishes and publishes its handback report, immediately spawn a fresh reviewer in a dedicated pane to audit the candidate. **Never pause remaining writers to wait for a review.** Drafting and technical review proceed in parallel.

**Exact-SHA Invalidation**: Technical review binds strictly to an exact commit SHA. Any subsequent commit, rebase, or fix pushes the branch HEAD to a new SHA. When branch HEAD advances, any prior approval is automatically **stale and invalidated**.

## 3. Serial Integration & Delivery
Integration combines verified lane commits into a single candidate, serially.

1. **Rebase** onto current baseline.
2. **Run repository checks**: Execute the target repository's generic build, generation, and test checks.
3. **Deliver**: Push to the requested target (e.g. unmerged draft PR) as authorized.

### Merge Conflict Ownership
Treat conflict resolution as standard engineering execution:
1. **Rebase in the Isolated Worktree**.
2. **Resolve Conflict Markers with Integrity**.
3. **Re-Verify with Tests** (do not assume success just because markers cleared).
4. **Force-Push with Lease**.
