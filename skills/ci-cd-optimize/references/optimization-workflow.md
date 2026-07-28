# The Optimization Workflow — How to Think Before Touching YAML

Use this file when starting a CI/CD optimization engagement: what to read first, how to
find opportunities in run history, how to choose among candidate improvements, and when
to stop. It sequences the other references; they carry the depth.

## Phase 0 — Read before measuring

Fifteen minutes of reading prevents optimizing the wrong pipeline.

1. **Inventory the workflows.** Triggers, path filters, `needs:` chains, runner labels,
   concurrency groups, caches, artifact flows. Draw the DAG on paper; the declared shape
   rarely matches the mental model that produced it.
2. **Find the deploy path.** What does a merge to the default branch actually do? A
   pipeline that deploys is optimized differently from one that only gates.
3. **Read the repo's own rules** (`AGENTS.md`, `CONTRIBUTING.md`, CI comments). A gate
   that looks redundant may be a deliberate safety mirror; deleting it is not an
   optimization (`references/effectiveness-contract.md`).
4. **Note what does NOT exist.** Missing CI entirely, a service with no delivery
   pipeline, or a hand-pushed production artifact is a bigger finding than any speedup —
   creating a missing path outranks tuning an existing one.

## Phase 1 — Pull history, not vibes

Baseline from the platform's recorded runs before forming any hypothesis
(`references/measurement.md` for the protocol and metrics):

- **Aggregate first**: per-workflow run count, failure and flake rate, median and p95,
  trend. Sort by slowest and by widest p95-to-median gap — a wide gap usually means
  cold-vs-warm cache mixing or queue contention, not uniform slowness.
- **Drill down only where the aggregate points**: run → job → step timings; failed-run
  views; log search across runs when one failure repeats.
- **Split every job into queue / setup / execution / transfer.** Each segment has a
  different fix, and the split decides which references apply:

| Dominant segment | Route |
|---|---|
| Queue | `references/capacity-and-contention.md`, then `references/runners-and-autoscaling.md` |
| Setup (checkout, toolchain, deps) | `references/caching.md`, `references/network-and-artifacts.md`, `references/typescript-toolchain.md` |
| Execution | `references/testing-and-flakiness.md`, `references/containers.md`, language references |
| Transfer | `references/network-and-artifacts.md`, `references/caching.md` |

- **Compute queue share** (Σ queue / (Σ queue + Σ execution)). Above ~35 %, topology
  work is near-futile — capacity is the problem (`references/capacity-and-contention.md`).
- **Check cache reality, not cache config.** Hit counts, restore/save times, and entry
  ages from the platform's cache API. A cache that exists in YAML and never hits is the
  single most common silent defect — and a cache integration can *look* healthy (layers
  reported as cached) while routing to slow storage; only timings expose it.

## Phase 2 — Generate candidates in cost order

Walk the performance order from the operating loop (do not start it → cancel stale →
reuse → shorten path → move fewer bytes → add compute) and write down every candidate
with an estimate. Cheap sweeps that find most of the usual wins:

- Duplicate `push` + `pull_request` runs; draft PRs allocating runners; scheduled runs
  at :00 (`references/github-actions.md`, `references/change-based-ci.md`).
- Work unrelated to the diff: missing path filters or affected planners
  (`references/change-based-ci.md`, `references/monorepos.md`).
- Serial jobs with no real dependency; planner/aggregate hops priced above their work
  (`references/runners-and-autoscaling.md`).
- Single-threaded tools on multi-core runners; worker caps meant for a weak workstation
  travelling into CI (`references/testing-and-flakiness.md`).
- Suites whose cost is real sleeping — durations clustered at round numbers
  (`references/testing-and-flakiness.md`).
- Toolchain generations: a native-speed compiler, linker, or package manager can beat
  months of YAML tuning; verify current-version claims first
  (`references/evidence-and-sources.md`).
- Docker: dependency layers ordered after source copies, `mode=max` exports nothing
  reuses, missing platform cache endpoints (`references/containers.md`).
- Oversized runners: peak CPU/memory far below allocation with flat wall-clock across
  sizes is the downsizing signature (`references/runners-and-autoscaling.md`).

Rank by **time saved on the critical path ÷ effort**, and mark whether each is on the
critical path at all — off-path savings are worth much less. Include "reject" rows with
reasons; a disproved candidate documented is a candidate nobody retries.

## Phase 3 — One bounded experiment at a time

Take the top candidate and run it through the operating loop's experiment step: evidence
observed, expected impact, risks, rollback. One change, then re-measure the same metric
across ≥3 comparable runs — interleaved with any competing runs so pool contention does
not align with the variable under test (`references/capacity-and-contention.md`).

While validating, the wait itself must not stall the work: arm a SHA-pinned, terminating
watcher and continue (`references/feedback-loops.md`).

## Phase 4 — Verify, report, decide to continue or stop

- Verify at the level actually reached (`references/measurement.md`): a config review is
  not a run; one run is not a median.
- Report execution and queue as **separate numbers**; a wall-clock multiplier quoted
  while queue dominates describes scheduling, not your change.
- Report disproved hypotheses and no-change results explicitly. "No speedup; the work
  was correctness" is a valid outcome that protects every other number.
- Confirm nothing previously caught is now skipped: test counts, gates, health checks,
  rollback paths (`references/effectiveness-contract.md`).

**Stop when fixed cost dominates.** When a job is mostly runner boot + checkout + cache
restore and its work is seconds, further in-job optimization is noise. The remaining
levers are job count, capacity, and feedback latency — or stopping, which is the correct
recommendation for a pipeline already at its floor. State the floor with numbers.

## Recurring engagement shape

On a repository already optimized once, re-run Phase 1 and diff against the previous
baseline rather than restarting. Two things decay quietly: caches (evicted, key-drifted,
or bypassed by a dependency change) and path filters (new directories nobody routed).
Check both before believing a regression is code.
