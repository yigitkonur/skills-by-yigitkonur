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

## Retry accounting and handoff

The same unresolved finding lineage has a maximum of five E2E attempts: the
initial failing execution and at most four corrective attempts. Preserve its
lineage across additional affected cases, renamed scenarios, revised specs,
reopened issues, and the final integrated sweep.

Invalid YAML corrections are submission retries, not E2E attempts. A `NOT_RUN`
result caused by missing credentials did not exercise the application and does
not consume an E2E attempt. Do not rerun unchanged failing behavior merely to
spend the remaining allowance. Inspect the controller's current lineage state;
workers cannot reset counters by editing records.

Every retry task's `prior_context` supplies:

- Previous failure and exact record/artifact references.
- What changed in code, source target, environment, spec, or execution procedure.
- New hypothesis and the evidence making this attempt informative.
- What not to repeat, including invalidated assumptions.
- Remaining attempts, stable finding/lineage, and issue/PR references.

Use [task-retry.yaml](../assets/templates/task-retry.yaml) as the request shape;
replace its example history with actual records before task creation.

If there is no materially different next action, keep the finding blocked and
advance independent work. At the limit, record `ATTEMPT_LIMIT` and the unresolved
result. A final sweep can expose current status but grants no additional repairs.
