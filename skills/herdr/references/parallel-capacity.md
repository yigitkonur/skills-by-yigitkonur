# Parallel capacity and PR integration

Use for issue implementation, many worktrees or a multi-PR merge wave. Keep the
main skill's single task table. [event-monitoring.md](event-monitoring.md) owns
WAIT and PR discovery; this file owns readiness, resource allocation and delivery.

## Establish scope and capacity

Inventory issues, existing PRs/worktrees/agents, dirty work and current
base/head SHAs. Classify accepted implementation, bounded research, unresolved
product decisions and parent epics separately. Labels are leads, not proof of
readiness. Reuse existing candidates; do not dispatch duplicate implementations.

Resolve repository, target branch, environment and current delivery authority.
If the user asked to approve a strategy first, present it before launching that
wave. Already granted authority persists; do not resurrect retired owner-name
gates. An explicit user reservation of merging remains in force until changed.
For release work, record deployment checks, required inputs and rollback;
merged code and a verified release are different outcomes.

Budget these separately in the existing ledger:

| Resource | Ownership and limit |
|---|---|
| Worktrees | Include active and retained unmerged checkouts in the inventory. |
| Model workers | Ready independent writing/research lanes, within host/provider limits. |
| Reviewers | Read-only work on a frozen candidate; a separate checkout is often unnecessary. |
| Compiler/test jobs | Measured CPU, memory and disk capacity; one owner per build lane. |
| Install/UI jobs | Exclusive ownership of shared installs, launched apps and mutable UI/TCC state. |
| Integration | One writer advancing the destination branch at a time. |

A ceiling such as 20 worktrees is capacity, not a quota. Use ready independent
outcomes up to the approved limit; do not bypass actual host limits with
external runners. Worker count does not automatically raise compiler count.
Date capacity observations and distinguish RAM, memory pressure and disk
headroom; stale measurements must not become permanent blockers. On a
constrained host, begin with one compiler and one installer, then adjust from
measurements. No universal per-agent RAM estimate is reliable.

## Map contracts before dispatch

Worktrees isolate file edits, not shared behavior. Assign a producer/owner for
composition roots, settings keys/defaults, schemas/migrations, shared models,
public interfaces, generated files, lockfiles and project configuration.
Consumers may build independent internals against an agreed contract; they
must not invent a conflicting copy while the producer is unfinished.

For each lane record: accepted outcome and issue URLs, exclusions, base,
checkout/branch, exclusive writer scope, prerequisites, contract owner, checks,
resource needs and handback destination. Use dependency edges only for actual
prerequisites. Group work that must ship together; a parent epic is an index,
not a reason for one giant branch. A lane may deliver several small PRs.

One writer owns each checkout and mutable contract. Preserve the user's primary
dirty tree; integration uses a dedicated clean checkout. When depending on an
unmerged producer, record the stacked PR base and prerequisite explicitly.
Do not copy producer commits into multiple supposedly independent candidates.

At the start of a large unfamiliar campaign, use the first few end-to-end
handoffs to calibrate writer, review and integration throughput. Other ready
independent work can proceed; this is not a new approval or artificial wave
barrier. When drafts awaiting checks/review accumulate faster than they clear,
shift capacity to verification/integration before launching more writers.
Count delivered behavior, not active panes or opened PRs.

## Write mission prompts that can finish

Use [mission-briefs.md](mission-briefs.md) for the standalone prompt contract.
Follow an applicable installed `dispatch` skill and local mission protocol
when supplied; their absence must not block a single-skill installation. Keep
parent-only prompt-authoring instructions out of worker briefs. Write English
briefs when the user requests them. Relevant skills go first, with when to use
each; avoid a generic catalog that buries the mission.

Put task-specific decisions before reusable process detail:

1. **Outcome:** issue URLs, user problem, accepted behavior, exclusions and
   observable finish line. Mark observation, proposal and user decision
   separately; research suggestions are not approved product choices.
2. **Baseline:** verified branch/base, exact checkout, source files and evidence
   to read. State what is already complete and must not be redone.
3. **Ownership/dependencies:** allowed writes, contract producers, agreed API/data
   shape and prerequisite PRs. Name unresolved inputs instead of guessing them.
4. **Checks/resources:** repository-approved commands, required evidence and
   actual build/install grants. Identify how a pending grant will be obtained.
5. **Delivery:** current commit/push/PR authority, draft versus ready criteria,
   report path, exact base/head, acceptance coverage and remaining gaps.
6. **Failure handoff:** bounded recovery, exact blocker and next action. The
   controller owns topology; workers report failed child work rather than
   launching duplicate writers or independent orchestration scripts.

Launch workers in the main skill's interactive terminal mode. A machine-readable
report is a handback artifact, not a reason to hide their progress in print mode.

Read the applicable `implement` companion when installed. If red-before-code is required,
allocate the test capability before the behavioral implementation starts.
Never demand TDD while indefinitely denying all test execution. Queue that
lane's code phase, grant a focused test slot, or seek an explicit exception
when required by the project; workers can research meanwhile. Parse/lint-only
checks must be reported as such, not as application tests or builds.

Use pointers for long specs, not accumulated conversation dumps. Include enough
context for a cold agent to distinguish done from blocked. After a material
follow-up, record acknowledgment or observed compliance; queued text is not
proof that the worker changed course. Retain mission/report files while
handoff depends on them. Sanitize and attach lasting evidence to the PR or
approved durable project location; an untracked local report is not a portable
handoff or backup.

## Run build and delivery queues together

Dispatch ready lanes in parallel within the measured envelope. Process finished
handbacks while other writers run; unrelated changes do not wait for every
worker to finish. Reserve capacity for review and integration throughout.

Grant compiler/install resources explicitly and record release. One reusable
build directory per active build lane and unique result-bundle paths avoid
cache races. Keep logs/results tied to candidate SHAs. Reclaim only known
inactive disposable caches after checking disk; never let ENOSPC become the
scheduler. A released resource goes to its next ready owner promptly.

Before transferring a build/install grant, READ the prior worker and confirm
its background process finished. A visible prompt can coexist with active
jobs. Never grant two users of the same shared app install or mutable UI state.
Repository-specific restrictions, including targeted-only tests, remain in force.

PR arrivals and worker settlement are separate observations. Use the finite
PR snapshot/delta commands in [event-monitoring.md](event-monitoring.md).
Inspect short terminal tails at WAIT settlement and full evidence in report
files. Do not repeatedly reread every pane to discover a new PR.

## Own draft → ready → accepted

Unless draft-only delivery was requested, the implementer's finish line is a
ready-for-review PR with accepted scope implemented and required checks
recorded. A draft is useful intermediate work, not completed implementation.
Use closing issue references only for delivered scope; research PRs identify
research outcomes and do not claim the feature works.

| Delivery state | Required next action |
|---|---|
| Draft / implementation pending | Name missing behavior and its writer; continue implementation. |
| Draft / verification pending | Name missing evidence, verifier and required resource grant. |
| Ready / review pending | Inspect current candidate and author evidence; perform proportionate review. |
| Changes requested | Assign material corrections as a set; review the resulting delta. |
| Accepted / merge pending | Record reviewed head, dependencies and authorized integration owner. |
| Merged / acceptance reconciled | Confirm target and complete issue coverage; close only delivered issues. |

Readiness follows evidence, not the flag. A draft may already meet readiness:
inspect its current candidate/checks, then use the supported promotion command
and read back state (GitHub: `gh pr ready <number> --repo <owner/repo>`). A
non-draft can still lack required evidence; record the gap and return it to
draft when appropriate. Promoting never manufactures missing checks.

Every retained draft needs a specific gap, next owner and action or named
external blocker. Before closing a finished author terminal, record any
transfer to verification/review. If no transfer occurred, the implementation
assignment remains unfinished. An author's report that says "done" cannot
orphan the draft. The main skill's cleanup rule closes finished terminals
promptly while preserving needed branches/checkouts.

A transfer is concrete when the controller accepts the remaining criteria,
candidate SHA and evidence paths, and names the next verifier or explicitly
owns its queued dispatch with a resource/unblock condition. An active verifier
pane is not required before the author closes. An anonymous "verification
queue" is insufficient. Record the author handoff as finished, while the PR
stays verification pending; this does not relax the overall ready-PR outcome.

Review the full first candidate once: actual diff, accepted behavior and
existing evidence. Reuse evidence that still applies to that candidate. For
fixes, inspect the changed delta, prior findings and affected callers; expand
only for new changes, failures, missing requirements or concrete risks.

Block on reachable user failures, data loss, permissions/security defects,
violated accepted behavior and missing required evidence. Cosmetic preferences
and speculative unsupported permutations are advisories. Do not waive a real
defect merely because it was called advisory. A documentation-only change may
need diff/link checks; migrations or capture changes need evidence for their
consequential failure paths. Review verdicts are claims to validate, not votes.

## Integrate serially

`MERGEABLE` is only Git's conflict assessment. Empty CI/review fields do not
prove correctness. Preserve explicit user merge reservations; otherwise use
the current authorized delivery path without repeated approval questions.

For each candidate:

1. Freeze the reviewed head and record target base, dependencies, checks and
   issue coverage. Obtain branch writer handoff before updating that branch.
2. Inspect both text conflicts and semantic overlap: defaults, schema versions,
   API contracts, dependency locks, authorization and lifecycle behavior can
   disagree even when files merge cleanly.
3. Reconcile with the current target in an isolated checkout. Publish necessary
   resolution commits in the candidate or a linked integration PR; a local
   rehearsal is not remote delivery.
4. During an **actual merge/rebase conflict**, use the project's or installed
   `resolving-merge-conflicts` skill when available. Otherwise inspect conflict
   stages, both histories and original PR requirements, preserve both accepted
   intents, stage only resolved intended files and run affected checks. Record
   resolution decisions and finish the operation before integration advances.
   Do not activate conflict handling merely because future conflicts are possible.
5. Review the integration delta and required evidence on the candidate that will
   merge. Use the repository's permitted method with reviewed-head protection;
   never bypass checks or force-push the destination.
6. Read back merged state and target SHA; update issue coverage. Reconcile the
   next candidate against that new target. Failure blocks dependents, not
   unrelated ready lanes.

Merge producers before consumers. After squash/rebase integration, check stacked
consumer diffs for duplicated producer commits; retarget/rebase only with
writer ownership, then recheck the changed candidate. No merge method is
universally correct. A changed target requires checks relevant to the combined
behavior, not an automatic repetition of every historical audit.

At the wave/release boundary, run the repository's required integrated checks
and review interactions not already covered by the candidate evidence. For
release authority, verify the integrated artifact, then follow the normal
staging/deployment path. Record release revision/environment separately. Stop
dependent merges on a regression and prepare a bounded fix or revert; reverting
code may not reverse a migration.

Close an issue only when the accepted outcome is integrated and verified;
parent epics require all accepted children delivered or explicitly rescoped.
A research result, open draft or ready PR is not implementation closure.
Remove checkouts only under the main skill's preservation rule, and read back
PR/issue/worktree state after settlement.

## Durable handoff

Before compaction, refresh the existing ledger with authority, dependency order,
current candidate/target SHAs, evidence paths, resource owners, queued messages,
observer states and each next action. Rehydrate from live state on return.

Report drafts, ready candidates, accepted candidates and merged outcomes
separately. A completed wave has integrated and verified its approved outcomes.
A blocked handoff lists retained candidates, exact blockers and owners; it is
not reported as full completion. No orphaned draft or unconsumed observer may
be hidden behind a success count.
