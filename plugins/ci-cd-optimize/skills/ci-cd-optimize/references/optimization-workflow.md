# The Optimization Workflow — How to Think Before Touching YAML

Use this file when starting a CI/CD optimization pass. It sequences the rest of the reference set so the agent investigates in the right order.

## Phase 0 — Read before measuring

1. Inventory the workflows: triggers, path filters, `needs:` chains, runner labels, caches, artifacts, deploy path.
2. Identify what a merge to the default branch actually does.
3. Read the repo's own rules (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`).
4. Note what does **not** exist — a missing pipeline is a bigger finding than a small speedup.

## Phase 1 — Pull history, not vibes

Baseline from real run history before forming any hypothesis.

- Aggregate first: per-workflow run count, failure/flake rate, median and p95.
- Then drill down: run → job → step timings; failed-run views; recurring log patterns.
- Split every job into **queue / setup / execution / transfer**.
- Compute **aggregate queue share** as a saturation signal, then check whether queued jobs delayed the critical path and run-level wall-clock. Do not infer the bottleneck from summed per-job time alone.
- Check cache reality, not cache config: hit counts, restore time, save time, and entry size.

## Phase 2 — Generate candidates in cost order

Walk the performance order:

1. Do not start it
2. Cancel stale work
3. Reuse previous work
4. Shorten the critical path
5. Move fewer bytes
6. Only then add compute

Write down every candidate with expected impact, risk, rollback, and whether it touches the critical path.

## Phase 3 — One bounded experiment

Take the top candidate and test it with:

- the same commit if possible
- comparable runner class
- measured before/after data
- a SHA-pinned watcher if you must wait on CI

Interleave A/B arms when contention exists so pool drift does not align with the variable under test.

## Phase 4 — Verify and decide whether to stop

Report:

- median and p95 wall-clock
- queue and execution separately
- cache behavior
- first-time pass rate
- cost
- what stayed intentionally unchanged

Stop when fixed cost dominates. A tiny job that is mostly checkout + setup is already at its floor.

## Cross-links

- `references/measurement.md` — metric definitions and evidence rungs
- `references/capacity-and-contention.md` — when parallelism inverts above a ceiling
- `references/caching.md` — break-even discipline
- `references/feedback-loops.md` — how to wait for CI without stalling the session
