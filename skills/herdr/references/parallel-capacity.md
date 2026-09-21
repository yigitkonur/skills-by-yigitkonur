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

## 4. Finite Review Bounds & Failure Budget Rules

To prevent infinite review-and-fix loops and ensure integrity of findings:
- **Two-Failure / Two-Round Limit**: If two consecutive correction rounds or review attempts fail to resolve a blocker or achieve candidate approval, **stop blind automated retries**. A third attempt without an architectural change or explicit management unblock is prohibited.
- **No Reset of Failure Budget**: Read-only tool movement, changing error IDs, switching model tiers, or receiving new user prompt iterations **do not reset** equivalent-failure budgets. Meaningful progress must advance the deliverable or resolve its blocker.
- **Material Findings Cannot Be Waived**: Material findings cannot be reclassified as advisory or waived merely to reach an approval. An approval requires all mandatory criteria to be satisfied. Hitting the two-round boundary mandates a concrete escalation with options, not an artificial approval.
- **Cosmetic Invariant**: Minor non-functional or cosmetic comments do not reopen a correction cycle once functional criteria and check gates are satisfied.

## 5. Retrospective Lifecycle & Teardown Gates

Resource lifecycle follows two explicit, separate cleanup gates:

### 5a. Prompt Terminal & Pane Retirement (EM Control)
- **Prompt Retirement**: Once an owned worker's handback report is received, evidence is verified durable on disk, ownership is reconciled, and no assigned work or uncertain operations remain, the EM **promptly closes the owned worker pane** (`herdr pane close <PANE_ID>`). If using the side-by-side review split pattern, the implementer pane is retained until the reviewer completes verification and PR approval.
- **Session Retention Rule**: Retaining a session (e.g. for follow-up debugging) requires recording an explicit retention reason and release trigger in `state.yaml`. Conversation resume identity and artifacts must be preserved outside the process before closing.
- **Closure Invariants**: Verify live identity, foreground process, and owned effects before closing. **Never** close leadership panes (CTO/EM), user-owned panes, or active sibling panes. Close a whole tab (`herdr tab close <TAB_ID>`) only if every contained pane is owned, completed, and eligible for closure.
- **Disappearance & State Checkpoint**: Verify pane disappearance (`herdr pane process-info` returns not found) and update compact resource entries in `state.yaml`.
- **Late/Duplicate Notices**: Late or duplicate notices from a retired worker do not respawn the terminal, repeat dispatch, or trigger Git actions.

### 5b. Worktree Removal Gate (Integration Authority)
- Worktree cleanup is a separate engineering gate; terminal closure does NOT authorize deleting checkouts.
- Removal gate: verify checkout is owned, `git status --porcelain` is strictly clean, references/evidence/reports are retained outside the checkout, and zero unresolved operations exist (`git worktree remove <PATH>`).
- Dirty, modified, or ambiguous checkouts are **retained with a recorded reason**; no default force removal (`git worktree remove --force` is prohibited without explicit authorization).

## 6. Serial Integration & Delivery Lifecycle

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
