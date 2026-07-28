# Capacity and Contention

Use this file when queue time is a material share of wall-clock, when adding jobs
stopped helping, before sharding or fanning out work, or when a supposedly faster
change measured neutral because the fleet was busy.

This is the reference for the failure mode a fast local benchmark misses: the job
itself got shorter, but the pipeline did not, because the platform had no free
slots to run the extra work. Read `references/measurement.md` first so queue and
execution are already separated.

## The inversion to watch for

Two otherwise-good optimizations **invert** above a platform concurrency ceiling:

- parallelize independent work
- shard a slow lane into more jobs

Both raise **job count**. Once job count exceeds available slots, the surplus
queues while re-paying per-job setup. The DAG looks more parallel and the wall
clock does not improve — sometimes it gets worse.

A neutral or negative result here is not evidence that sharding is bad in
principle; it is evidence that the platform was capacity-bound for that shape.

## Diagnose contention first

Use this checklist before splitting anything:

1. Separate **queue** from **execution** per job (`references/measurement.md`).
2. Count how many jobs are runnable at the peak fan-out point.
3. Compare that count with the provider's available slots for this repository,
   queue, label, or runner class.
4. Measure the per-job setup tax: queue + VM boot + checkout + toolchain restore.
5. Ask whether the proposed split reduces execution by more than it increases the
   number of queued/setup-paying jobs.

A quick heuristic:

- If queue is a small tail and execution dominates, sharding may help.
- If queue is a large share of p95, do **not** add jobs until capacity is
  measured and, if needed, fixed.
- If the lane is short and setup-heavy, merging jobs that share setup is usually
  better than splitting them.

## Price the hop

A new job is not free. It pays its own queue wait, VM provisioning, checkout, and
runtime setup before doing useful work. Call that the **hop cost**.

Price it with the median and p95 from real runs:

```text
hop_cost = queue + setup
work_saved = old_execution - new_execution
```

Only split when `work_saved` clearly beats the hop cost *in the same contention
state*.

Typical bad shapes:

| Shape | Why it loses |
|---|---|
| Planner job in front of the matrix | Adds one full queue/setup hop before any useful lane starts. |
| Aggregate status job at the end | Adds one more hop after all real work is already done. |
| Tiny shards on cold runners | Each shard re-pays setup; the serial tail moves from execution to orchestration. |
| More jobs on a scarce large runner class | Queue rises faster than execution falls. See `references/runners-and-autoscaling.md`. |

## Compare arms under the same load

A run against an idle pool and a run against a saturated one are not comparable,
even on the same commit and runner class. The difference can exceed the effect you
are testing.

For in-job changes, compare **execution time** first. For topology changes, either:

- interleave arms (`A, B, A, B`) and compare medians, or
- run both during the same fleet conditions and treat any delta smaller than the
  queue-time spread as noise.

A useful report shape:

```text
Queue p50/p95: 18s / 97s   (noise floor)
Execution p50/p95: 62s / 66s
Change A -> B execution delta: -4s
Conclusion: within queue noise, not proven at wall-clock level
```

That is a real result. Report neutral experiments instead of silently dropping
them and letting the next person re-run the same dead idea.

## What to do when capped

When the ceiling is the problem, the next move is usually **fewer jobs**, not
more hardware. Try, in order:

1. Merge jobs that share expensive setup.
2. Remove planner/aggregator hops that exist only for ergonomic reporting.
3. Collapse tiny shards until setup is amortized.
4. Move non-critical parallel work off the PR critical path with a full-run
   fallback (`references/change-based-ci.md`).
5. Only then add slots, resize runners, or change queue placement
   (`references/runners-and-autoscaling.md`).

Examples of "merge, don't split":

- lint + typecheck on the same checkout/runtime when each is short
- unit tests and small static analysis sharing the same dependency install
- one workflow with multiple short jobs that all queue behind the same scarce
  label

Examples where splitting still wins:

- genuinely long, independent test groups with modest setup
- jobs whose runtime dominates queue+setup by a wide margin
- sharding on a fleet with spare slots and stable startup latency

## Provider-specific ceilings

The ceiling is provider- and fleet-specific. It can be:

- a repository concurrency limit
- a queue label with few warm runners
- a scarce runner class (large x64, macOS, GPU, ARM)
- an autoscaler that reacts more slowly than the fan-out burst
- a self-hosted fleet sharing slots across several repositories

Do not infer the ceiling from docs alone. Infer it from queue share and from the
point where adding jobs stops reducing wall-clock. Then route to the provider file
or `references/runners-and-autoscaling.md` for the capacity-side fix.

## Connections to other references

- Read `references/measurement.md` first — this file assumes queue vs execution is
  already separated.
- Read `references/runners-and-autoscaling.md` when the fix is more slots, a
  different runner class, or a fleet change.
- Read `references/change-based-ci.md` when the best answer is to avoid starting
  unrelated work at all.
- Read `references/testing-and-flakiness.md` before sharding tests, especially
  when setup or report merging is non-trivial.
- Read `references/feedback-loops.md` when a topology change also alters how the
  result is consumed (aggregate jobs, follow-up workflows, late registration).

## Sources

- GitHub Actions limits: https://docs.github.com/en/actions/reference/limits (accessed 2026-07-28)
- GitLab runner autoscaling: https://docs.gitlab.com/runner/runner_autoscale/ (accessed 2026-07-28)
- CircleCI parallelism/resource classes: https://circleci.com/docs/guides/optimize/parallelism-faster-jobs/ (accessed 2026-07-28)
- Buildkite queue and concurrency docs: https://buildkite.com/docs/pipelines/configure/workflows/controlling-concurrency (accessed 2026-07-28)
