# Scheduling, resources, and bounded retries

The orchestrator owns this policy. The CLI checks mechanical eligibility and
records reservations; the host provides actual worker lifecycle controls.

## Capacity and independence

Use `min(20, campaign max_active, actual host capacity)` active role workers.
All worker roles count, including verifiers, ticket writers, and integrators.
Unlimited total workers may run sequentially. `DISPATCHED` reservations count
before binding, and a submission does not free its live worker slot.

Sequence each launch: `task create` -> `task dispatch` -> host launch ->
`task bind`. If launch/bind fails, inspect whether a worker was created before
interrupting the reservation. Close only after accepted outputs and confirmed
host termination. Never create a second worker against an ambiguous live handle.

Use a fresh actor/context for each task and round. Enforce author != executor,
executor != verifier, distinct blind verifiers, and implementer != independent
retest executor/verifier. Workers do not dispatch other workers. A harness that
cannot create actual isolated contexts is `AGENT_ISOLATION_UNAVAILABLE`, not
permission for one agent to impersonate the full team.

## Dependencies are a DAG

Record prerequisites as explicit task/case dependencies. Reject cycles, missing
nodes, unsupported target references, and contradictory coverage before plan
acceptance. A conceptual wave groups ready work for communication; it is never
a global wait-for-everyone barrier.

After every useful accepted output, reconcile and reconsider all ready branches.
A blocked registration prerequisite blocks its downstream authenticated journey;
an independent public search case can still run. Verified failures can enter
diagnosis/repair immediately while other execution branches continue.

Use the controller's ordered ready list consistently: expectation priority
`P0` through `P3`, number of dependent jobs unlocked, verification/repair work,
oldest creation time, then numeric task ID. `ready_details` explains the order.
Do not impose a separate wave barrier or pick from an unordered directory scan.

The controller reserves each case/spec/target before dispatch, including every
member of a grouped assignment. An interrupted but still-live executor keeps
its reservation. Review an accepted execution before requesting another run;
duplicate assignments are not a way to obtain more favorable evidence.

Group at most four sibling variants into one worker assignment only when they
share tools/setup, have independent results, have a reliable reset between them,
and none is a prerequisite of another. Preserve separate case observations,
artifacts, review assignments, and verdicts. A batch summary cannot stand in for
per-case evidence. Dependencies requiring fresh state/context stay separate.

## Resource claims are separate from worktrees

Name each shared resource and claim `read` or `write` in the task/plan. Concurrent
readers may coexist; a conflicting writer serializes access. Names must identify
the real shared object, not a convenient per-agent alias.

Examples: source worktree, runtime generation, test account, database namespace,
queue/topic, object-storage prefix, browser profile, remote single-page session,
native device, port, external webhook destination, and Git integration target.
The same database URL/account behind two worktrees is still one data resource.
Declare fixture reset as a write. Give each executor its own namespace/session
where supported; otherwise lease and serialize the shared resource.

Do not schedule source/config edits against a runtime generation under test.
An implementer edits a separate worktree. A runtime change creates a new target,
and new proof must bind that target. Runtime count/CPU/browser quota may justify
a tighter capacity than the host's agent count; record the real bottleneck.

## Critical review dispatch

Use the manifest's predeclared `review_count` for each expectation. When two
reviews are required, create distinct verifier tasks with the same original
inputs and without either peer's result. Do not include a first-verifier verdict
in the second handoff, notebook excerpt, message, or filename used as a cue.
Keep peer review files out of the assigned reading set.

## Shared attempts and current retry history

An unresolved root finding has at most five problem-solving interventions,
including its initial baseline. An intervention identifies a baseline, an
integration, or a changed execution approach. The controller allocates its
`attempt_id`; workers do not invent IDs or infer equality from similar prose.
Preserve the generated `intervention_origin` when present; it ties a local
execution-approach reference to the root that allocated it.
All cases/variants evaluating the same intervention share that attempt. Twenty
cases failing for one baseline defect do not consume twenty repair attempts.

Count an attempt only when a member actually executes (`COMPLETED` or `PARTIAL`).
`NOT_RUN`, rejected YAML, reviewer replacement, and recovery of a runtime for the
same correction do not consume another attempt. A new corrective approach cannot
reuse an earlier attempt just by retaining its target or changing its name.
The final sweep tests the selected correction; it is not an automatic sixth
attempt and cannot be repeatedly used to bypass the limit.

After an integrated retest runs but its capture is inconclusive, describe the
changed capture procedure in a fresh corrective request's `prior_context`.
The controller allocates a new execution approach for that change. It reuses an
intervention only for other members evaluating the same correction or the final
sweep. A local label such as `retry-1` in another root does not prove that the
two roots exercised the same correction.

Linking findings preserves their history. Combine a common baseline and proven
identical interventions, retain distinct corrections, and surface ambiguous
legacy mappings. Never discard excess history to manufacture remaining attempts.
At the limit, keep `ATTEMPT_LIMIT` and advance independent work.

Use [task-retry.yaml](../assets/templates/task-retry.yaml) for corrective requests.
The controller generates the latest failure **per assigned case**, previous
fixes/integrations/retests, issue/PR references, and remaining allowance. The
orchestrator supplies `prior_context.what_changed`, `hypothesis`, and
`do_not_repeat` to explain the next action. Generated history has a recorded
basis; if it changes before dispatch, refresh the task from current records.
`STALE_RETRY_CONTEXT` is a correction request, not permission to delete history.

Diagnosticians, implementers, and corrective executors read this history. Blind
verifiers receive the original-input allowlist instead; repair conclusions and
peer judgments must not influence their independent evidence assessment.
