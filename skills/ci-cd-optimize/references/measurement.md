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

## Queue versus execution — never collapse them

A workflow duration can worsen while the work itself stays flat. Split them
before naming a bottleneck:

- **Queue** = `started_at - created_at`
- **Execution** = `completed_at - started_at`

This is not bookkeeping trivia. On a measured repository, six comparable runs
showed execution holding in a narrow band while queue ranged from seconds to
minutes. Quoting a multiplier from total wall-clock alone would have reported
both "2.6× slower" and "1.7× faster" for the same configuration, depending on
which queue sample you chose.

For reusable workflows and `needs`-gated jobs, note the subtlety: `created_at`
may be set only after dependencies finish. That means a multi-stage DAG pays its
queue/setup tax once per stage. When the platform exposes per-job start offsets,
use them to reconstruct the real critical path rather than trusting stage names.

## Sampling traps

Before trusting a comparison, actively rule out the three easiest false claims:

1. **Re-read, not re-run.** Confirm the attempt counter actually changed. Three
   identical durations to the tenth of a second are usually the same run read
   three times.
2. **Mixed populations.** Do not compare `push`, `pull_request`, and
   `workflow_dispatch` together; those often carry different runners, queues,
   and job sets.
3. **Self-inflicted contention.** Bursting several experiments at once can move
   the queue more than the optimization moved execution. Interleave A/B arms, or
   compare execution when pool state is clearly different.

Averages hide the variance that makes CI painful: cold caches, runner
saturation, flaky retries, and dependency changes. Report the median for the
typical path and p95 for the tail instead of treating one mean as representative.
A robust p95 needs a real sample. Roughly 20+ comparable runs is arithmetic,
not evidence by itself; below that, say you have a small cohort rather than a
stable tail.

1. Pin the exact commit, workflow, event, runner class, and environment.
2. Run at least three comparable runs when variance is material.
3. Record queue, setup, execution, transfer, finalization, and per-job duration.
4. Record exact cache hit/miss, retry count, artifact names/digests, and run head SHA.
5. Reject baselines from stale branches, empty diffs, disabled jobs, or different runners.

If a queue-time baseline is unavailable, start with provider run timestamps and job logs. Do not invent missing precision.

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
