# Capacity Ceilings and Contention

Use this file when parallelism stops paying off, when queue time dominates p95, or before recommending "split this job" / "fan out these jobs". It also covers the measurement confound that makes contended and uncontended runs incomparable.

Everything else in this skill assumes that adding a parallel job buys wall-clock. That assumption is false above a concurrency ceiling. Check the ceiling before reshaping a DAG, or you will ship a change that moves waiting rather than removing it.

## The failure mode

A pipeline has N independent jobs and a platform ceiling of C concurrent jobs. While N ≤ C, splitting work shortens the critical path. Once N > C, the surplus jobs queue, and total wall-clock converges on:

```text
wall-clock ≈ queue + ceil(N / C) × (per-job setup + execution)
```

Splitting further *increases* total time, because every extra job re-pays setup (checkout, toolchain, dependency restore) while waiting for the same C slots. The DAG looks more parallel and runs no faster.

## Decide with queue share before touching topology

Compute this first. It is the gate for whether workflow-shape work is worth doing at all:

```text
queue share = Σ queue time / (Σ queue time + Σ execution time)
```

Measured across all jobs in a representative window, not one run.

| Queue share | Bottleneck | Correct action |
|---|---|---|
| < 15 % | Work inside jobs | Normal optimization: caching, sharding, DAG shape. |
| 15–35 % | Mixed | Optimize execution, but stop adding jobs. |
| > 35 % | **Capacity** | Reduce job *count* or raise the ceiling. Topology changes are near-futile. |

Above ~35 %, the honest recommendation is usually "raise the limit" or "merge these jobs", not a YAML refactor. Say so plainly rather than shipping a reshuffle that tests as neutral.

## Detect the ceiling empirically

Do not assume the documented plan limit is the effective one; quotas, org-wide contention from other repos, and per-runner-type caps all bite first.

1. Trigger a run with more independent jobs than you believe the ceiling to be.
2. Record `created_at` and `started_at` per job.
3. Count how many jobs are simultaneously in the started-but-not-completed state.

The peak simultaneous count is the effective ceiling. A reliable signature: jobs created at the same timestamp whose `started_at` values fall into distinct clusters separated by roughly one job duration.

```text
job A  created 10:00:00  started 10:00:11   ← slot 1
job B  created 10:00:00  started 10:00:12   ← slot 2
job C  created 10:00:00  started 10:02:41   ← waited for a slot to free
```

Three jobs, two slots. No workflow change makes C start sooner.

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

1. **Reduce job count.** Merge jobs that share setup — two 40 s jobs each paying 20 s of checkout and install become one 60 s job. Fewer slots, less duplicated setup, shorter wall-clock.
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

When capacity is the binding constraint, say it in the headline rather than burying it. A report claiming "2× faster" while queue is 48 % of wall-clock is describing a machine that is idle-waiting half the time. State the execution improvement and the capacity constraint as two separate numbers, and name raising the ceiling as the remaining lever.

## Sources

- GitHub Actions limits (concurrent job limits by plan, macOS sharing, support-ticket raise path): https://docs.github.com/en/actions/reference/limits (accessed 2026-07-28)
- GitHub Actions concurrency groups: https://docs.github.com/en/actions/using-jobs/using-concurrency (accessed 2026-07-28)
- GitLab Runner advanced configuration (`concurrent`, `limit`, `request_concurrency`): https://docs.gitlab.com/runner/configuration/advanced-configuration/ (accessed 2026-07-28)
- OpenTelemetry CI/CD metrics (queue vs execution split): https://opentelemetry.io/docs/specs/semconv/cicd/cicd-metrics/ (accessed 2026-07-28)
