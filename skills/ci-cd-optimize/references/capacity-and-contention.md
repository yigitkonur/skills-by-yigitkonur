# Capacity and contention

Use this file when queue time is a large share of wall-clock, when adding more jobs failed to reduce latency, or when the same workflow is fast one hour and much slower the next with identical code.

## The inversion

Most CI advice says split work and add parallelism. That is correct **below** the capacity ceiling. Above it, the advice inverts:

```text
wall-clock ≈ queue + ceil(total_parallel_jobs / effective_capacity)
              × (per-job setup + execution)
```

Treat that as a heuristic, not an exact formula. The point is structural: once the queue is dominant, extra jobs repay setup while waiting for scarce slots, so the DAG looks more parallel and finishes no faster.

## Queue-share gate

Measure over a window, not one run:

```text
queue share = Σ queue / (Σ queue + Σ execution)
```

Interpret it conservatively:

| Queue share | Meaning | Default move |
|---|---|---|
| <15% | queue is noise | optimize execution first |
| 15–35% | queue is material | stop adding jobs until setup and critical-path work are justified |
| >35% | capacity is the bottleneck | topology changes are near-futile; fix contention or capacity first |

This number is easy to lie with. Sum per-job queue only across **comparable jobs in the same stage**. A `needs`-gated DAG pays queue once per stage; blindly summing every queued job overstates the problem.

## Detect the effective ceiling empirically

Do not trust the advertised concurrency limit. Org-wide contention, runner-class scarcity, and workflow-level caps usually bite first.

Method:

1. Trigger more independent jobs than you think the pool can run.
2. Record `created_at` and `started_at` per job.
3. Count the largest number of jobs that were started but not yet completed at the same time.
4. Compare it with the runner class and workflow topology.

Signature of a ceiling:
- `started_at` values arrive in clusters rather than smoothly.
- Later jobs wait roughly one earlier-job duration before starting.
- Queue p95 jumps while execution stays flat.

If a 25-second job waits 120 seconds for a slot, adding one more stage or fan-out cell makes the whole workflow slower even if the job itself is tiny.

## Contention is a measurement confound

Two runs of the same commit on the same runner class are **not** comparable if one ran against an idle pool and the other against a saturated one.

Rules:
- Compare execution separately from queue.
- Interleave experiment arms (`A, B, A, B`) rather than running all `A` then all `B`.
- Treat any delta smaller than `queue p95 - queue p50` as suspicious until proven otherwise.
- When execution is flat and queue moved, report that as a scheduling story, not a build story.

## The inversion ladder

When the ceiling is the bottleneck, fix in this order:

1. **Merge jobs that share setup.** A single checkout/install on one runner is often cheaper than N queue waits plus N setups.
2. **Shrink per-job setup.** The queue forces you to repay setup `ceil(N/C)` times, so checkout and install inflation hurts twice.
3. **Stop starting irrelevant work.** Path routing, affected selection, draft gating, and duplicate-trigger removal matter more than micro-optimizing a test command.
4. **Raise capacity.** Add or upsize only after you know queue is the bottleneck and the job is on the critical path.
5. **Only then reshape the DAG.** Splitting long jobs further is correct only once the queue no longer dominates.

This directly contradicts the usual "split long jobs" advice. Both are correct in their own regime; the ceiling decides which one applies.

## Pricing a queue hop

Every extra job pays a queue hop, VM boot, checkout, and toolchain setup. Before adding a planner job, aggregate-status job, or another matrix axis, price the hop:

```text
extra critical-path cost = queue_p50_or_p95 + setup_p50
```

If the proposed new job does 10 seconds of useful work but the hop costs 35 seconds, that job is a regression unless it removes a larger amount of downstream work.

## Distinguish critical-path value from total work

A repository can spend many compute-minutes in parallel and still be fast. A repository can also spend little compute and still feel slow because the critical path is queue-dominated.

Optimize in this order:
1. jobs with high critical-path rate,
2. jobs with large exclusive time,
3. only then total compute.

A dramatic reduction in parallel non-critical work can produce zero wall-clock improvement.

## What to report

Do not headline "2× faster" when half the difference is queue noise. Report two numbers:

- execution change on the bottlenecked job or stage,
- queue share (or queue p50/p95) that constrained the result.

An experiment that measured neutral or worse is still a result. Record it. Silently dropping a disproved idea guarantees the next person retries it.

## Related references

- `references/measurement.md` — how to separate queue, setup, execution, and critical path
- `references/runners-and-autoscaling.md` — how to choose hosted/self-hosted/ephemeral capacity once queue is proven dominant
- `references/change-based-ci.md` — ways to stop launching irrelevant work
- `references/network-and-artifacts.md` — shrinking per-job setup when a queue hop is unavoidable

## Sources

- GitHub Actions limits: https://docs.github.com/actions/reference/limits (accessed 2026-07-28)
- GitLab Runner advanced configuration (`concurrent`, per-runner `limit`, `request_concurrency`): https://docs.gitlab.com/runner/configuration/advanced-configuration/ (accessed 2026-07-28)
- OpenTelemetry CI/CD semantic conventions: https://opentelemetry.io/docs/specs/semconv/registry/attributes/cicd/ (accessed 2026-07-28)
