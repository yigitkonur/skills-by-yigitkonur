# Capacity Ceilings and Contention

Use this file when queue time dominates p95, when fan-out stops paying off, or before recommending "split this job" / "add more shards" / "parallelize another suite".

Everything else in the skill assumes another parallel job buys wall-clock. Above a concurrency ceiling that assumption is false: extra jobs simply queue, each one re-paying setup and restore.

## The failure mode

A pipeline has **N** independent jobs and an effective ceiling of **C** concurrent slots. While `N ≤ C`, splitting shortens the critical path. Once `N > C`, the surplus jobs queue and total wall-clock converges on:

```text
wall-clock ≈ queue + ceil(N / C) × (per-job setup + execution)
```

Beyond the ceiling, splitting further **increases** total time because every extra job pays another checkout, setup, restore, and artifact phase while waiting for the same C slots.

## Decide with queue share before touching topology

Compute this first:

```text
queue share = Σ queue time / (Σ queue time + Σ execution time)
```

Measured across a representative window, not one run.

| Queue share | Bottleneck | Correct next move |
|---|---|---|
| < 15% | Work inside jobs | Normal optimization: caches, sharding, DAG shape. |
| 15–35% | Mixed | Optimize execution, but stop adding jobs blindly. |
| > 35% | **Capacity** | Reduce job count or raise the ceiling. DAG refactors alone will not help. |

Above roughly 35%, the honest recommendation is often "merge jobs that share setup" or "increase capacity" — not another layer of sharding.

## Detect the ceiling empirically

Do not assume the documented plan limit is the effective one; org-wide contention, runner-class scarcity, and time of day all bite first.

1. Trigger a run with more independent jobs than you believe the ceiling to be.
2. Record `created_at`, `started_at`, and `completed_at` per job.
3. Count how many jobs are simultaneously in `started_at <= t < completed_at`.

The peak simultaneous count is the effective ceiling. A common signature is jobs created at the same instant whose `started_at` values fall into distinct clusters separated by roughly one job duration.

## Queue time varies by runner class — measure it, do not assume

A larger instance class is not automatically faster end-to-end. Scarcity, fleet warmth, and time of day decide whether the bigger class is provisioned sooner or later than the small one.

Two real observations from the same provider are both true:

- One window: 16-vCPU jobs started immediately while smaller classes waited.
- Another window: the 16-vCPU class waited **~6–7×** longer than a 2-vCPU class, and a job that executed in ~60s spent nearly twice that waiting for a runner.

Neither generalizes. The method does:

- Compare runner classes under the **same contention state**.
- For in-job changes, compare **execution time** separately from queue time.
- If the difference you are testing is smaller than the queue-time spread, the sample is noise.

## When the platform already proxies the registry

Several providers run a pull-through package proxy on the runner network. When that exists, a large package-manager store cache can be redundant: restoring a 100–500 MB archive to avoid a fetch that was already local is pure transfer overhead.

Test it directly rather than reasoning from hit counts:

1. Find a run where the store cache missed.
2. Compare its install step with a warm-cache run.
3. If install time is roughly unchanged, the proxy is doing the work and the store cache is only buying its own restore/save cost.

This check is especially relevant on Avrea, where package caching and the registry proxy are separate layers.

## Merge jobs, but only when the separation is not buying something

When capped, merging jobs that already share setup is often the fastest move. Before doing it, check what the separation was buying:

- **Rerun granularity** — merged job means rerunning both halves.
- **Failure attribution** — keep step names distinct so the failing half is obvious.
- **Isolation** — the one that bites most often. Jobs that were safe in separate VMs may share a database, fixed port, temp path, or global config once merged.

A merge that trades 30s of queue for 40s of serial work is a regression. Verify it with the same before/after evidence as any other change.

## Signs that fan-out is no longer the lever

- Queue time exceeds execution time on the critical path.
- Total job work falls, wall-clock stays flat.
- `max queue time` rises as job count rises.
- Per-shard setup dominates the shard's useful work.

When those show up, stop adding jobs. Either pack work better or raise capacity.
