# Capacity Ceilings and Contention

Use this file when parallelism stops paying off, when queue time dominates p95, or before recommending "split this job" / "fan out these jobs". It also covers the measurement confound that makes contended and uncontended runs incomparable.

Everything else in this skill assumes that adding a parallel job buys wall-clock. That assumption is false above a concurrency ceiling. Check the ceiling before reshaping a DAG, or you will ship a change that moves waiting rather than removing it.

## The failure mode

A pipeline has N independent jobs and a platform ceiling of C concurrent jobs. While N ≤ C, splitting work shortens the critical path. Once N > C, the surplus jobs queue, and total wall-clock converges on:

```text
wall-clock ≈ queue + ceil(N / C) × (per-job setup + execution)
```

Splitting further *increases* total time, because every extra job re-pays setup (checkout, toolchain, dependency restore) while waiting for the same C slots. The DAG looks more parallel and runs no faster.

## Use aggregate queue share as a diagnostic

Compute this across a representative window:

```text
aggregate queue share = Σ queue time / (Σ queue time + Σ execution time)
```

A rising value is evidence of contention, but it is not wall-clock share or a universal topology gate. Summing job time counts parallel waits separately, including waits on jobs that never touch the critical path. Before changing job count or capacity, correlate it with:

- queue delay on jobs that frequently lie on the critical path,
- run-level median and p95 wall-clock as contention changes,
- repeated saturation in the relevant runner class or pool,
- the predicted critical path of the proposed DAG.

High aggregate queue share with no critical-path queue delay can coexist with a useful topology change. Conversely, even a modest aggregate share can hide a severe delay on the one job that gates completion. Use the metric to trigger investigation, then decide from critical-path and run-level evidence.

## Detect the ceiling empirically

Do not assume the documented plan limit is the effective one; quotas, org-wide contention from other repos, and per-runner-type caps all bite first.

1. Group jobs by the runner class or pool they are eligible to use; separate pools have separate limits.
2. For each pool, trigger repeated runs with more runnable independent jobs than the suspected limit.
3. Record `created_at`, `started_at`, and completion time per job.
4. Count how many eligible jobs are simultaneously in the started-but-not-completed state.

The peak simultaneous count in one run is only **observed concurrency**, a lower bound on available capacity. Treat it as a ceiling only when repeated saturated runs for the same pool plateau at that count while additional eligible jobs remain queued. A reliable saturation signature is jobs created together whose `started_at` values form clusters separated by roughly one job duration; first rule out DAG dependencies, concurrency groups, environment gates, and autoscaler warm-up.

```text
job A  created 10:00:00  started 10:00:11   ← slot 1
job B  created 10:00:00  started 10:00:12   ← slot 2
job C  created 10:00:00  started 10:02:41   ← waited for a slot to free
```

This run observed two simultaneous jobs in that pool and one eligible job waiting. Repeat under saturation before calling two the ceiling or changing topology.

## Contention is a measurement confound

Two runs of the same commit on the same runner class are still not comparable if one ran against an idle pool and the other did not. This produces confident, wrong conclusions — a topology change measured against an uncontended baseline can appear to win or lose by an entire job duration when nothing about the work changed.

Before comparing A/B:

- Record queue time per job for both, not just total duration.
- Compare **execution** time when testing an in-job change; compare total only when the pool state matches.
- Re-run the losing arm at least once when the delta is within the observed queue spread.
- Treat any delta smaller than p95-minus-p50 of queue time as noise.

A/B arms should be interleaved (A, B, A, B) rather than run in blocks, so drifting pool load does not align with the variable under test.

## What actually helps when you are capped

In order of effect:

1. **Reduce job count when the modeled critical path improves.** Merge jobs that share setup only if the saved setup and queue delay exceed lost parallelism. For example, two 40 s jobs each paying 20 s of checkout and install may become one 60 s job, but verify the merged job does not extend a different dependency chain.
2. **Shrink per-job setup**, since it is now multiplied by `ceil(N / C)`: cache restores, shallow/sparse checkout, prebuilt toolchain images.
3. **Cut work that need not run** — path filters, affected-package planners, draft gating. This lowers N directly.
4. **Raise the ceiling.** On most providers this is a plan change or a support request, and it is a legitimate recommendation with a cost line attached.
5. **Only then** reshape the DAG.

Note that (1) directly contradicts the usual "split long jobs" advice. Both are correct in their own regime; the ceiling decides which regime you are in.

## Provider ceilings (verify against current docs before relying on a number)

| Provider | Control | Notes |
|---|---|---|
| GitHub-hosted | Total concurrent jobs by plan: Free 20, Pro 40, Team 60, Enterprise 500; larger runners 1000 (Team/Enterprise). macOS capped at 5 (50 Enterprise) and **shared** across standard and larger runners. | Raisable by support ticket; larger runners also carry a per-runner-type concurrency limit set at creation. |
| GitLab Runner | `concurrent` in `config.toml` limits jobs across *all* registered runners; per-runner `limit` is subordinate to it. `0` for `concurrent` is forbidden. | `request_concurrency` (default 1) is a separate throttle on job requests, not execution. |
| Self-hosted / managed pools | Agent or VM count | The ceiling is whatever you provisioned; autoscaler warm-up time appears as queue. |

Also budget for `concurrency:` groups you wrote yourself. A deploy group with `cancel-in-progress: false` is an intentional serialization point and will show up as queue time — that is correct behavior, not a regression.

## Reporting rule

When capacity is the binding constraint, say it in the headline rather than burying it. Report aggregate queue share as summed job-time evidence, not as a percentage of wall-clock. State critical-path queue delay, run-level wall-clock impact, execution improvement, and the validated pool ceiling as separate numbers; name raising capacity as the remaining lever only when those measurements show it is binding.

## Sources

- GitHub Actions limits (concurrent job limits by plan, macOS sharing, support-ticket raise path): https://docs.github.com/en/actions/reference/limits (accessed 2026-07-28)
- GitHub Actions concurrency groups: https://docs.github.com/en/actions/using-jobs/using-concurrency (accessed 2026-07-28)
- GitLab Runner advanced configuration (`concurrent`, `limit`, `request_concurrency`): https://docs.gitlab.com/runner/configuration/advanced-configuration/ (accessed 2026-07-28)
- OpenTelemetry CI/CD metrics (queue vs execution split): https://opentelemetry.io/docs/specs/semconv/cicd/cicd-metrics/ (accessed 2026-07-28)
