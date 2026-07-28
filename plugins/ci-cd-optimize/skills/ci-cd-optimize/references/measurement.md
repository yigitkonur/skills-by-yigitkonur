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

1. Pin the exact commit SHA, workflow, event population, runner class/pool, and environment.
2. Run at least three comparable runs when variance is material; otherwise say it is a one-run signal.
3. Record queue, setup, execution, transfer, finalization, and per-job duration.
4. Record exact cache hit/miss, retry count, artifact names/digests, run attempt, and run `head_sha`.
5. Reject baselines from stale branches, wrong SHAs, empty diffs, disabled jobs, different runner classes, or different event populations.
6. Keep prompt-level or run-level pairings visible; do not let a global mean erase a severe regression on one required job.

If a queue-time baseline is unavailable, start with provider run timestamps and job logs. Do not invent missing precision.

### Sample hygiene

- **A rerun is not a new sample.** Re-running the same commit measures cache warmth and pool state, not the change; count attempts separately and never mix attempts of one run into the sample as independent commits.
- **Separate event populations.** PR runs, push runs, merge-queue runs, and scheduled runs have different caches, filters, and concurrency; baseline and comparison must come from the same population.
- **Record pool state with every sample.** Runner label, time of day, and whether other runs were queued. Sequential before/after timings under different pool load compare the pool, not the change — interleave per `references/capacity-and-contention.md`.
- **Your own measurement bursts are contention.** Back-to-back validation runs inflate queue time for every sample including the baseline re-runs.

## Critical-path analysis

Build a DAG from declared dependencies. For every job, compute:

- duration,
- exclusive time (time it blocks the critical path),
- critical-path rate (how often it determines total duration),
- setup/execute/transfer breakdown.

Prioritize `critical-path rate × exclusive time`. A job consuming CPU in parallel with a longer job is not the current bottleneck.

Include **critical-path queue delay** in the path: the wall clock pays `queued + setup + execution` along the finishing chain. Summed queue seconds across parallel jobs overstate wall loss — only delay on the chain counts (`references/capacity-and-contention.md`).

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

1. Push and drive the run to a terminal verdict on the exact new SHA (`references/feedback-loops.md`); a superseded or timed-out watch is no verdict.
2. Confirm the run's head SHA contains the change and the expected jobs ran.
3. Compare p50/p95 wall-clock, queue time, cost, cache behavior, and first-time pass rate on matched, interleaved samples.
4. Confirm no tests/gates disappeared from the merged result.
5. Repeat on a normal representative commit.
6. Record disproved and neutral outcomes too — they are results.

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
