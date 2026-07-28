# Capacity and Contention

Read this before recommending any parallelization change (more jobs, more shards, a fan-out planner), and whenever a measured speedup came out neutral or worse than predicted. Splitting work only helps while runners are available to pick it up; past the concurrency ceiling, more jobs make the pipeline *slower*, and contention quietly corrupts every timing you collect.

## The queue-share gate

Before touching topology, compute where wall-clock actually goes:

```
queue share = Σ queue time / (Σ queue time + Σ execution time)
```

Queue time per job is `started_at − created_at`; execution is `completed_at − started_at`. Both are in the provider's run/job API.

| Queue share | Regime | Action |
|---|---|---|
| `< 15 %` | Execution-bound | Optimize inside jobs (cache, critical path, test cost). Splitting helps. |
| `15–35 %` | Mixed | Stop *adding* jobs; balance the ones you have. |
| `> 35 %` | **Capacity-bound** | Topology changes are near-futile. Raise concurrency or reduce job count. |

This inverts the usual "split long jobs" advice in the capacity regime — both are correct, and the ceiling decides which applies.

## Why more jobs get slower

Wall-clock for N independent jobs against C concurrent runners is roughly:

```
wall-clock ≈ queue + ceil(N / C) × (per-job setup + execution)
```

Once `N > C`, jobs serialize into `ceil(N / C)` waves, and every job re-pays setup (checkout, toolchain, dependency restore). Fanning a suite into 8 shards on a 2-runner fleet runs four sequential waves plus eight setups — reliably worse than 2 shards. Fanning heavy work onto a single scarce large-runner label serializes your own pipeline against itself.

## Detect the ceiling empirically

Do not trust documented plan limits — org settings, other repos' concurrent runs, and reserved capacity all move the real number. Trigger more jobs than the suspected ceiling, then from the job API record `created_at` and `started_at` and count the peak number simultaneously *started but not completed*. That peak is C.

Worked shape: three independent jobs dispatched together; two start within a second of each other, the third starts only when one of the first two finishes. C = 2. No workflow change makes the third start sooner — only more capacity does.

## Contention is a measurement confound

Two runs of the same commit on the same runner class are **not comparable** if one ran against an idle pool and the other against a saturated one. This is the most common reason a "regression" or "win" evaporates on re-measurement.

- Never quote a multiplier when queue p95 exceeds execution p50 — the number is dominated by scheduling noise. (Worked case: six runs of one unchanged pipeline, execution stable at 56–68s, queue ranging 16s–416s; both "1.7× faster" and "2.6× slower" are derivable from the same data and both meaningless.)
- To compare two configurations under contention, interleave arms (A, B, A, B, …) rather than all-A-then-all-B, so a load swing hits both.
- Treat any delta smaller than the queue p95−p50 spread as noise.
- Do not benchmark inside your own burst of validation runs — back-to-back dispatches inflate each other's queue. Sample from ordinary pushes, and report the sample size (n≈5 is an observation, not a p95; ~20 is a floor for a credible tail).

## Ranked remediation when capacity-bound

1. **Reduce job count** — merge jobs that share setup; move short steps into a neighbor rather than paying a fresh runner for each. (Directly contradicts "split long jobs" — correct only in this regime.)
2. **Raise concurrency** — a larger hosted plan, more self-hosted replicas, or autoscaling keyed to queue depth. Justify it with the measured ceiling and queue share, not a hunch.
3. **Right-size, don't upsize the matrix** — move only the proven CPU-bound critical-path job to a bigger runner; a large label with a smaller fleet often queues *longer* (`runners-and-autoscaling.md`).
4. **Cut work that never needed to run** — path filters and change-based selection reduce N at the source (`change-based-ci.md`), which is strictly better than scheduling it faster.

## Provider ceilings

Concurrency limits are plan- and account-scoped and change often — verify against current docs before quoting a number, per `evidence-and-sources.md`. As orientation only: hosted GitHub Actions concurrency scales with plan tier; GitLab is governed by runner `concurrent` / per-project `limit` / `request_concurrency`; self-hosted fleets are bounded by replica count. The number that matters is the one you measured on this repo, this hour.

## Report disproved hypotheses

An experiment that measured neutral or worse is a result, not a dead end — record it. Silently dropping it invites the next person (or the next agent) to retry the same change. "Fan-out measured neutral (244s vs 245s) because the repo had 2 concurrent runners and queue was 47.7% of total CI time" is more valuable to the next reader than an omission, because it names the ceiling that made topology irrelevant. This honesty is part of the skill's done criteria, not optional color.
