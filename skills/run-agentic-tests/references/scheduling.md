# Scheduling, resources, and bounded retries

The orchestrator owns this policy. The CLI checks mechanical eligibility and
records reservations; the host provides actual worker lifecycle controls.

## Capacity, model sizing, and independence

- **Concurrency**: Use `min(campaign max_active, actual host capacity)` active role workers. Default to realistic local concurrency (2–4 workers) to prevent OOM and port collisions.
- **Model Economy**: Configure workers per provider to balance speed, cost, and accuracy. Anthropic: mandate `claude-3-7-sonnet` or `claude-3-5-sonnet` with low or medium reasoning `budget_tokens: 1,024–2,048` (disable or set to 1024 for routine steps); strictly ban `claude-3-opus` to eliminate 5x cost penalties and multi-turn tool latency bottlenecks. OpenAI / Codex: `gpt-6-luna` with `reasoning_effort: "low"` for simple ops; `gpt-6.1-sol` with `reasoning_effort: "medium"` for evidence checks (ban `high`/`xhigh`). Gemini: `gemini-3.8-flash` with `low` reasoning for simple ops, `medium` for verification, reserving `high` for root-cause diagnosis and DAG planning.
- **Independence**: Enforce author != executor, executor != verifier, distinct blind verifiers, and implementer != independent retest executor/verifier. Workers do not dispatch other workers.

Sequence each launch: `task create` -> `task dispatch` -> host launch -> `task bind`.
Close only after accepted outputs and confirmed host termination.

## Dependencies are a DAG & parallel execution

Record prerequisites as explicit task/case dependencies. Reject cycles, missing
nodes, unsupported target references, and contradictory coverage before plan
acceptance. A conceptual wave groups ready work for communication; it is never
a global wait-for-everyone barrier.

- **True DAG Parallelism**: As soon as a prerequisite resolves, all newly unblocked branches must be dispatched concurrently up to available worker capacity. Independent public tests do not wait for an unrelated registration branch.
- **Dynamic Sibling Scaling**: Sibling test cases sharing identical read fixtures scale concurrently up to host capacity. Do not artificially throttle independent cases into small sequential batches when capacity is available.
- **Streamlined Fast-Path**: For smoke tests, single journeys, or pre-authored suites, bypass exploratory roles and execute directly: `Wave 0 Readiness → Parallel Execution → Verification`.

Use the controller's ordered ready list consistently: expectation priority
`P0` through `P3`, number of dependent jobs unlocked, verification/repair work,
oldest creation time, then numeric task ID. `ready_details` explains the order.

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

## Critical review dispatch: Concurrent dual verification

Use the manifest's predeclared `review_count` for each expectation. When two
reviews are required (`review_count: 2`), create distinct verifier tasks and
**dispatch them concurrently in parallel**.

To prevent LLM completion identicality and avoid duplicate output from provider prompt-cache hits:
- **Prompt Variance**: Assign distinct evaluation lenses in their respective handoffs:
  - **Verifier A (Specification Conformance)**: Evaluates strict adherence to declared Given/When/Then steps and positive proof.
  - **Verifier B (Adversarial & Boundary Scrutiny)**: Evaluates edge conditions, negative assertions, subtle side effects, and potential capture gaps.
- **Seed / Sampling Variance**: Pass distinct seed identities (`seed: sha256(campaign_id + task_id + "slot_a")` vs `"slot_b"`) and non-zero temperature to eliminate prompt-cache identicality and guarantee mathematically independent completion trajectories.

Both verifiers read only the original execution evidence allowlist, without either
peer's result, verdict, notebook excerpt, or discussion. Running them concurrently
cuts verification turnaround time in half while preserving total independence.
Conflicting verdicts remain `INCONCLUSIVE`.

## Shared attempts and adaptive retries

An unresolved root finding has an adaptive intervention budget:
- **1–2 attempts** for deterministic defects (syntax errors, missing elements, wrong responses).
- **Up to 3 attempts** for verified timing or network flakiness.
- Do not run an automatic 5-attempt retry cycle on static assertion failures.

An intervention identifies a baseline, an integration, or a changed execution approach.
The controller allocates its `attempt_id`; workers do not invent IDs or infer equality
from similar prose. All cases/variants evaluating the same intervention share that attempt.
Twenty cases failing for one baseline defect do not consume twenty repair attempts.

Count an attempt only when a member actually executes (`COMPLETED` or `PARTIAL`).
`NOT_RUN`, rejected YAML, reviewer replacement, and recovery of a runtime for the
same correction do not consume another attempt. A new corrective approach cannot
reuse an earlier attempt just by retaining its target or changing its name.
The final sweep tests the selected correction; it is not an automatic additional
attempt and cannot be repeatedly used to bypass limits.

After an integrated retest runs but its capture is inconclusive, describe the
changed capture procedure in a fresh corrective request's `prior_context`.
The controller allocates a new execution approach for that change. Linking findings
preserves their history. Never discard excess history to manufacture remaining attempts.
At the limit, keep `ATTEMPT_LIMIT` and advance independent work.

Diagnosticians, implementers, and corrective executors read this history. Blind
verifiers receive the original-input allowlist instead; repair conclusions and
peer judgments must not influence their independent evidence assessment.
