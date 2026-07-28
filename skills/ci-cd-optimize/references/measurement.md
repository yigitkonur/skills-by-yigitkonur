# Measurement and Verification

Use this file when building a baseline, proving a bottleneck, or validating that an optimization helped without weakening delivery outcomes.

## Metrics that matter

| Metric | Formula | Interpretation |
|---|---|---|
| Queue time | execution start - trigger time | Capacity, scheduling, concurrency, runner topology. |
| Setup time | first real task - runner start | Checkout, runtime, dependency install, environment boot. |
| Execution time | finish - execution start | Workload inside jobs. |
| Critical-path duration | longest dependency chain through the DAG | The only sequence that directly governs wall-clock feedback. |
| Cache exact-hit rate | exact key hits / cache attempts | Cache-key precision, not necessarily saved time. |
| Cache saved time | clean path time - (restore + post-hit work) | Whether a cache is worth keeping. |
| First-time pass rate | runs green without retry / all runs | Flakiness and reliability. |
| Cost per successful change | compute + storage / successful changes | Speed improvements that increase total cost may not be wins. |
| Change failure/rework rate | failed or unplanned recovery deployments / deployments | The effectiveness guardrail after optimization. |

Use median and p95. CI duration is right-skewed; averages hide cold caches, runner saturation, flaky retries, and dependency changes.

## Baseline protocol

1. Pin the exact commit, workflow, event, runner class, and environment.
2. Run at least three comparable runs when variance is material.
3. Record queue, setup, execution, transfer, finalization, and per-job duration.
4. Record exact cache hit/miss, retry count, artifact names/digests, and run head SHA.
5. Reject baselines from stale branches, empty diffs, disabled jobs, or different runners.

If a queue-time baseline is unavailable, start with provider run timestamps and job logs. Do not invent missing precision.

## Do not measure inside your own burst

Validation runs fired back-to-back contend for the same runner pool and inflate each other's queue time. Wall-clock measured under self-inflicted contention is not a regression signal, and reporting it as one is a false finding.

A worked case: a change set measured 163s against a 100s baseline and looked like a clear regression. Splitting the job records showed **execution was flat** (warm verify 13s → 14s; secret scan 7s → 8s) while **queue rose from 10s to 32–115s** because four validation runs had been dispatched in immediate succession. A single run taken once the pool drained returned 48s. The change had no effect on speed in either direction.

Practical rules:

- Always decompose before concluding: `queue = started_at − created_at`, `execution = completed_at − started_at`. A wall-clock delta with flat execution is a scheduling story, not a build story.
- Space validation runs, or take timing samples from ordinary pushes rather than from your own test batch.
- Report the sample size. Two runs per side is an observation; it is not a median, and it is certainly not a p95.
- When a change is genuinely neutral on speed, say so. "No speedup; the work was correctness" is a valid, honest result — inflating queue noise into a win or a loss destroys the credibility of every other number in the report.

When queue time is a large share of wall-clock, the confound is structural, not just noise: see `capacity-and-contention.md` for the queue-share gate, the concurrency-ceiling test, and interleaved A/B arms for comparing configurations under contention.

## Critical-path analysis

Build a DAG from declared dependencies. For every job, compute:

- duration,
- exclusive time (time it blocks the critical path),
- critical-path rate (how often it determines total duration),
- setup/execute/transfer breakdown.

Prioritize `critical-path rate × exclusive time`. A job consuming CPU in parallel with a longer job is not the current bottleneck.

Where the platform records per-job start offsets, derive the DAG shape empirically instead of trusting declared dependencies: a gap between a job's `start + duration` and its dependents' start is scheduling and per-job setup overhead, which no amount of in-job optimization removes. On Avrea, `references/avrea/cli-evidence.md` shows how to extract these offsets.

## Experiment verification

Before changing config, write down:

```text
Baseline: p50 14.2m / p95 18.7m on commit abc123
Bottleneck: test job, 9.8m execution, 82% critical-path rate
Change: shard Playwright by historical timing into 4 lanes
Expected: test critical path under 4m; no test-count loss
Risk: uneven shard due to one long spec; rollback is remove matrix
```

After the change:

1. Re-run the same commit if possible.
2. Confirm the run's head SHA contains the change and the expected jobs ran.
3. Compare p50/p95 wall-clock, queue time, cost, cache behavior, and first-time pass rate.
4. Confirm no tests/gates disappeared from the merged result.
5. Repeat on a normal representative commit.

## Claim only the rung reached

| Evidence | You may say |
|---|---|
| Config inspected | "The bottleneck hypothesis is plausible." |
| Syntax/schema validated | "The config is valid; runtime not exercised." |
| One exact-commit run | "One measured run improved; variance not established." |
| Three+ comparable runs | "The measured median/p95 improved on these runs." |
| Production/trend evidence | "The optimization held in normal operation." |

## Sources

- OpenTelemetry CI/CD semantic conventions: https://opentelemetry.io/docs/specs/semconv/registry/attributes/cicd/ (accessed 2026-07-28)
- OpenTelemetry CI/CD metrics: https://opentelemetry.io/docs/specs/semconv/cicd/cicd-metrics/ (accessed 2026-07-28)
- DORA metrics: https://dora.dev/guides/dora-metrics/ (accessed 2026-07-28)
- CircleCI Insights glossary: https://circleci.com/docs/guides/insights/insights-glossary/ (accessed 2026-07-28)
- GitLab CI/CD observability: https://docs.gitlab.com/operations/observability/ci_cd/ (accessed 2026-07-28)
