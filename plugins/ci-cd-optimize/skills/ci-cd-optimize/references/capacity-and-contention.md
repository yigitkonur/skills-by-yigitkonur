# Capacity and contention: queues, ceilings, and honest A/B tests

Queue time is governed by capacity, not by the code being tested. This file
covers diagnosing queue-dominated pipelines, concurrency ceilings, and how
to run comparisons that pool contention does not silently invalidate.

## Contents

- [Queue share is a signal, not a gate](#queue-share-is-a-signal-not-a-gate)
- [Observed concurrency is a lower bound](#observed-concurrency-is-a-lower-bound)
- [The cost of a job hop](#the-cost-of-a-job-hop)
- [Merge, don't split, above the ceiling](#merge-dont-split-above-the-ceiling)
- [Per-pool analysis](#per-pool-analysis)
- [Contention-safe A/B comparisons](#contention-safe-ab-comparisons)
- [When to buy capacity](#when-to-buy-capacity)

## Queue share is a signal, not a gate

Queue share (queued seconds ÷ wall seconds) marks a pipeline as worth a
capacity investigation — nothing more. Two traps:

- **Summed per-job queue time double-counts.** Twenty jobs each queuing 30
  seconds *in parallel* may cost the wall clock almost nothing. Only queue
  delay on the critical path is wall-clock loss. Compute
  `critical-path queue delay = Σ (start_time − ready_time)` along the
  finishing chain, and compare *that* to wall time.
- **Fixed thresholds ("investigate above 15%") are triage heuristics**, not
  policy. Corroborate with run-level p95 and the per-pool distributions
  below before concluding capacity is the bottleneck.

Derive queue time per job as `started_at − created_at` (most providers,
including Avrea, expose these rather than a direct queue field). Exclude
jobs that never started; use median and tail, never one delayed job.

## Observed concurrency is a lower bound

The peak number of simultaneously running jobs you observe in a run is a
**lower bound** on the pool's capacity — never proof of a ceiling. The pool
may have been partly busy with other work, autoscaling mid-run, or
throttled by a different repo. To estimate the effective ceiling of a
runner class/pool:

1. Collect multiple runs that were clearly saturated (jobs continuously
   queued while others ran).
2. Per run, record peak concurrent started jobs for that class.
3. The ceiling estimate is the repeated maximum across saturated runs —
   with the caveat that plan limits, org limits, and pool autoscaling all
   move it. Check provider/plan documentation for declared limits, then
   trust the measured value where they disagree.

## The cost of a job hop

Every extra job is not free parallelism. Each hop adds: queue wait +
runner boot + checkout + toolchain setup + cache restore. A planner or
aggregator job that "only takes 40 seconds of compute" can add minutes of
wall clock when the pool is contended, because it serializes *two* queue
waits into the critical path (planner queues, then everything it gates
queues again). Price a hop at its measured queue+setup, not its compute.

## Merge, don't split, above the ceiling

Splitting work into N shards helps only while N ≤ effective ceiling and
per-shard setup stays amortized. Above the ceiling, shards serialize: each
excess shard pays full queue+setup and delivers no parallelism. Symptoms:
"we doubled shards and CI got slower"; many short jobs with long queue
tails. Fix: merge shards toward the ceiling using measured per-shard
durations (`references/testing-and-flakiness.md` for splitting mechanics),
or collocate small jobs (lint+typecheck) into one runner until setup is
amortized.

Before merging jobs, check what the separation was buying:

- **Rerun granularity** — a merged job reruns both halves on any failure.
- **Failure attribution** — keep distinct step names so the log still says
  which half broke.
- **Isolation** — jobs that were safe in separate VMs may collide once they
  share one: two suites against a single Postgres fail with
  "already exists", port and temp-path clashes, global config mutation.

## Per-pool analysis

Never average queue times across runner classes. Pools saturate
independently: `ubuntu-latest` may be instant while `macos-14` or a
self-hosted GPU label queues for 20 minutes; larger classes often have
*smaller* fleets, so upgrading a job to a bigger runner can regress its
end-to-end time via queueing even when compute gets faster. For each
runner label: distribution of queue delay (median/p95), utilization while
queued, and time-of-day pattern. Daily saturation windows (e.g. 15:00
merges) are a scheduling/capacity-shape problem, not a test problem.

Two attribution traps before blaming the pool:

- **Self-authored `concurrency:` groups show up as queue time.** A deploy
  group with `cancel-in-progress: false` is an intentional serialization
  point; its queue delay is correct behavior, not pool saturation.
- **Where the ceiling is configured differs by provider** (verify current
  docs): GitHub plan-level total-concurrency limits are raisable via
  support, larger runners carry a per-runner-type limit set at creation,
  and the macOS cap is small and shared across runner classes; GitLab
  Runner's `concurrent` in `config.toml` caps jobs across all registered
  runners, with per-runner `limit` subordinate to it.

## Contention-safe A/B comparisons

Pool load changes minute to minute, so sequential before/after timing runs
measure the pool as much as the change:

- **Interleave** A and B runs (A, B, A, B …) rather than all-A then all-B.
- Record with every sample: runner label, time, and whether other runs
  were queued (pool state).
- Use the same event type and comparable commits; do not mix PR runs with
  merge-queue runs in one sample.
- Your own validation bursts are contention: five back-to-back experiment
  runs saturate the pool and inflate every measurement, including the
  baseline re-runs. Space samples or use a quiet window, and say so in the
  report.
- Small samples stay small claims: two runs per arm compare anecdotes.
  State n; prefer medians; treat overlapping ranges as "no measured
  difference".

## When to buy capacity

Add runners, bigger classes, or more concurrency only after: critical-path
queue delay is a top contributor at p95; the pool shows repeated
saturation; and cheaper moves (fewer jobs started, stale-run cancellation,
merged shards, off-peak scheduling of non-PR work) are exhausted or
rejected with reasons. Then buy the *specific* saturated pool, re-measure
the same way, and report cost delta alongside wall-clock delta. Capacity
changes are shared-state changes — authorization gate.
