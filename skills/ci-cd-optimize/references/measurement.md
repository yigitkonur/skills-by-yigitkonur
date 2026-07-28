# Measurement and Verification

Use this file when building a baseline, proving a bottleneck, sizing an
experiment, or deciding whether a claimed speedup is real. The goal is to measure
what the change controls, not to quote the best-looking total from a noisy set of
runs.

If the question is *whether adding jobs will help or whether the pool is already
contended*, read `capacity-and-contention.md` next. If the question is *how the
result gets back to an agent without stalling*, read `feedback-loops.md`.

## Metrics that matter

| Metric | Formula | What it answers |
|---|---|---|
| Queue time | job `started_at - created_at` | Capacity, scheduling, runner scarcity, queue placement. |
| Setup time | first real task - runner start | Checkout, runtime install, dependency restore, environment boot. |
| Execution time | finish - execution start | The work the job itself performs. |
| Critical-path duration | longest dependency chain through the DAG | The only sequence that directly governs wall-clock feedback. |
| Cache exact-hit rate | exact key hits / cache attempts | Key precision, not necessarily saved time. |
| Cache saved time | clean path - (restore + post-hit work) | Whether a cache is worth keeping. |
| First-time pass rate | runs green without retry / all runs | Reliability, flakiness, and hidden rework. |
| Cost per successful change | compute + storage / successful changes | Whether a “speedup” just bought more cost. |
| Change failure / rework rate | failed or unplanned recovery deploys / deploys | Whether the faster path weakened effectiveness. |

Use **median and p95**. CI duration is right-skewed; averages hide cold caches,
runner saturation, flaky retries, and setup spikes.

## Baseline protocol

1. Pin the exact commit, workflow, event, runner class, and environment.
2. Use at least three comparable runs when variance is material.
3. Record queue, setup, execution, transfer, finalization, and per-job duration.
4. Record exact cache hit/miss, retry count, artifact names/digests, and run head SHA.
5. Reject baselines from stale branches, empty diffs, disabled jobs, or different runners.

If queue-time history is unavailable, start from provider timestamps and job logs.
Do not invent missing precision.

## Separate queue from execution before claiming anything

Total wall-clock mixes two different things:

```text
queue     = started_at - created_at
execution = completed_at - started_at
```

Queue is fleet behavior; execution is the part your in-job change usually
controls. If execution is stable and totals swing, say that explicitly and report
execution as the result.

### Compare arms under the same contention state

A run against an idle pool and a run against a saturated one are not comparable,
even on the same commit and runner class. Interleave arms when practical (`A, B,
A, B`) and compare execution time when the change is in-job. Treat any delta
smaller than the queue-time spread as noise.

A good summary looks like:

```text
Queue p50/p95: 18s / 97s   (noise floor)
Execution p50/p95: 62s / 66s
Change A -> B execution delta: -4s
Conclusion: within queue noise, not proven at wall-clock level
```

That is a valid result. Report disproved hypotheses too — silently dropping a
neutral experiment invites the next person to retry the same dead idea.

## Critical-path analysis

Build the DAG from actual dependencies, not stage labels. For each job, compute:

- duration,
- exclusive time (how long it blocks the critical path),
- critical-path rate (how often it determines total duration),
- queue/setup/execute/transfer breakdown.

Prioritize:

```text
critical-path rate × exclusive time
```

A job burning a lot of CPU in parallel with a longer job is not the current
bottleneck. Large total CPU-time savings on non-critical work can produce zero
wall-clock change.

Where the platform records per-job start offsets, derive the DAG shape
empirically instead of trusting declared dependencies. A gap between a job's end
and its dependents' start is scheduling and per-job setup overhead — work no
in-job optimization will remove.

## Job topology: price the hop before adding one

A new job pays its own queue, VM boot, checkout, and toolchain setup. That **hop
cost** belongs in the baseline before adding planner jobs, aggregate status jobs,
fan-out helpers, or tiny shards.

If the question is specifically *when splitting or sharding stops helping*, route
immediately to `capacity-and-contention.md`.

## Experiment definition

Before changing config, write down the experiment in plain language:

```text
Baseline: p50 14.2m / p95 18.7m on commit abc123
Bottleneck: test job, 9.8m execution, 82% critical-path rate
Change: shard Playwright by historical timing into 4 lanes
Expected: test critical path under 4m; no test-count loss
Risk: uneven shard due to one long spec; rollback is remove matrix
```

If the plan cannot name the bottleneck and expected wall-clock effect, it is not
ready to run.

## Verify after the change

1. Re-run the **same commit** first when possible.
2. Confirm the run's head SHA contains the change and the expected jobs ran.
3. Compare p50/p95 wall-clock, queue time, cost, cache behavior, and first-time
   pass rate.
4. Confirm no tests/gates/artifact identities disappeared from the merged result.
5. Repeat on a normal representative commit.

## Claim only the rung reached

| Evidence | Safe wording |
|---|---|
| Config inspected | “The bottleneck hypothesis is plausible.” |
| Syntax/schema validated | “The config is valid; runtime not exercised.” |
| One exact-commit run | “One measured run improved; variance not established.” |
| Three+ comparable runs | “The measured median/p95 improved on these runs.” |
| Production/trend evidence | “The optimization held in normal operation.” |

## Cross-links

- `capacity-and-contention.md` — when queue share is high or added parallelism measured neutral.
- `feedback-loops.md` — when the optimization includes how a person or agent waits on CI.
- `runners-and-autoscaling.md` — when the next experiment is runner class or slot count.
- `caching.md` — when setup/restore is the bottleneck and cache saved time is the question.
- `testing-and-flakiness.md` — when retries or reruns dominate the metric.
- `effectiveness-contract.md` — before weakening any gate, cache trust scope, or artifact identity.

## Sources

- OpenTelemetry CI/CD semantic conventions: https://opentelemetry.io/docs/specs/semconv/registry/attributes/cicd/ (accessed 2026-07-28)
- OpenTelemetry CI/CD metrics: https://opentelemetry.io/docs/specs/semconv/cicd/cicd-metrics/ (accessed 2026-07-28)
- DORA metrics: https://dora.dev/guides/dora-metrics/ (accessed 2026-07-28)
- CircleCI Insights glossary: https://circleci.com/docs/guides/insights/insights-glossary/ (accessed 2026-07-28)
- GitLab CI/CD observability: https://docs.gitlab.com/operations/observability/ci_cd/ (accessed 2026-07-28)
