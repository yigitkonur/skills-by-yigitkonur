# Capacity Ceilings and Contention

Use this file when queue time dominates p95, when parallelism stops paying off, or before
recommending "split this job" / "fan out these jobs". It also covers the measurement
confound that makes contended and uncontended runs incomparable.

Everything else in this skill assumes a parallel job buys wall-clock. That assumption
fails above a concurrency ceiling: check the ceiling before reshaping a DAG, or the change
moves waiting around instead of removing it.

## The failure mode

With N independent jobs and a platform ceiling of C concurrent jobs, splitting work helps
while N ≤ C. Once N > C the surplus queues, and wall-clock converges on:

```text
wall-clock ≈ queue + ceil(N / C) × (per-job setup + execution)
```

Splitting further *increases* total time — every extra job re-pays setup (checkout,
toolchain, dependency restore) while waiting for the same C slots.

## Decide with queue share before touching topology

```text
queue share = Σ queue time / (Σ queue time + Σ execution time)
```

Measured across all jobs in a representative window, not one run.

| Queue share | Bottleneck | Correct action |
|---|---|---|
| < 15 % | Work inside jobs | Normal optimization: caching, sharding, DAG shape. |
| 15–35 % | Mixed | Optimize execution, but stop adding jobs. |
| > 35 % | **Capacity** | Reduce job *count* or raise the ceiling. Topology changes are near-futile. |

Above ~35 %, the honest recommendation is usually "raise the limit" or "merge these
jobs", not a YAML refactor. Say so plainly.

## Detect the ceiling empirically

Do not assume the documented plan limit is the effective one; quotas, org-wide contention
from other repositories, and per-runner-type caps bite first.

1. Trigger a run with more independent jobs than the believed ceiling.
2. Record `created_at` and `started_at` per job.
3. Count jobs simultaneously in the started-but-not-completed state.

The peak simultaneous count is the effective ceiling. The signature: jobs created at the
same timestamp whose `started_at` values fall into clusters separated by roughly one job
duration.

```text
job A  created 10:00:00  started 10:00:11   ← slot 1
job B  created 10:00:00  started 10:00:12   ← slot 2
job C  created 10:00:00  started 10:02:41   ← waited for a slot
```

## Contention is a measurement confound

Two runs of the same commit on the same runner class are not comparable if one ran
against an idle pool and the other did not — the delta can exceed the effect under test.
Firing several validation runs back-to-back creates this contention *yourself*: an
all-paths merge or a burst of dispatches inflates every arm's queue time, and the
"regression" is your own experiment design.

Before comparing A/B:

- Record queue time per job for both arms, not just totals.
- Compare **execution** time for in-job changes; compare totals only when pool state matches.
- Interleave arms (A, B, A, B) rather than running blocks, so drifting load does not
  align with the variable under test.
- Treat any delta smaller than the observed queue spread (p95 − p50 of queue) as noise,
  and re-run the losing arm at least once.

The full sampling protocol — attempt counters, event populations, minimum n — is in
`references/measurement.md`.

## What helps when capped

In order of effect:

1. **Reduce job count.** Merge jobs that share setup — two 40 s jobs each paying 20 s of
   checkout and install become one 60 s job. Before merging, check what the separation
   bought: rerun granularity, failure attribution (keep step names distinct), and
   isolation — two suites that each booted their own database may collide on one
   (`references/runners-and-autoscaling.md`).
2. **Shrink per-job setup**, now multiplied by `ceil(N / C)`: cache restores, shallow and
   sparse checkout (`references/network-and-artifacts.md`), prebuilt toolchain images.
3. **Cut work that need not run** — path filters, affected planners, draft gating
   (`references/change-based-ci.md`). This lowers N directly.
4. **Raise the ceiling** — a plan change or support ticket, a legitimate recommendation
   with a cost line attached.
5. **Only then** reshape the DAG.

Note (1) inverts the usual "split long jobs" advice; the ceiling decides which regime
applies. The same inversion applies to two steps of the skill's canonical order —
"parallelize independent work" and "shard slow work" both raise job count and both make a
capped pipeline slower.

## Provider ceilings (verify against current docs before relying on a number)

| Provider | Control | Notes |
|---|---|---|
| GitHub-hosted | Concurrent jobs by plan: Free 20, Pro 40, Team 60, Enterprise 500; larger runners 1000. macOS far lower and shared across runner classes. | Raisable by support ticket; larger runners also carry a per-runner-type limit set at creation. |
| GitLab Runner | `concurrent` in `config.toml` caps jobs across all registered runners; per-runner `limit` is subordinate. | `request_concurrency` throttles job *requests*, not execution. |
| Self-hosted / managed pools | Agent or VM count | Autoscaler warm-up appears as queue; a single-runner host serializes everything scheduled to it. |

Also budget for `concurrency:` groups you wrote: a deploy group with
`cancel-in-progress: false` is an intentional serialization point and shows up as queue
time — correct behavior, not a regression.

## Reporting rule

When capacity binds, put it in the headline. A report claiming "2× faster" while queue is
half of wall-clock describes a machine idle-waiting. State the execution improvement and
the capacity constraint as two separate numbers, and name raising the ceiling as the
remaining lever.

## Sources

- GitHub Actions limits: https://docs.github.com/en/actions/reference/limits (accessed 2026-07-28)
- GitHub Actions concurrency: https://docs.github.com/en/actions/using-jobs/using-concurrency (accessed 2026-07-28)
- GitLab Runner advanced configuration: https://docs.gitlab.com/runner/configuration/advanced-configuration/ (accessed 2026-07-28)
- OpenTelemetry CI/CD metrics (queue vs execution split): https://opentelemetry.io/docs/specs/semconv/cicd/cicd-metrics/ (accessed 2026-07-28)
