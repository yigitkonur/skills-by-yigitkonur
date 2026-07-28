# Avrea CLI as an Evidence Source

Optional. Read only when the repository runs on Avrea (`runs-on:` labels start with `avrea-`) and the `avr` CLI is available. Everything here is a faster way to satisfy `references/measurement.md`; it does not replace the measurement rules.

Verify availability before relying on any command below:

```bash
command -v avr && avr --version && avr auth status && avr health
```

If `avr` is absent or unauthenticated, fall back to provider-native measurement. Do not assume the platform.

## Why this matters for optimization

Most CI platforms make you reconstruct percentiles and the job DAG by hand. Avrea's API already aggregates them, so the baseline step becomes a query instead of a scraping exercise. The risk is the opposite of the usual one: numbers arrive so easily that they get quoted without checking sample size, window, or whether the change is even in the measured runs.

## Scoping and machine-readable output

Every read command shares the same conventions (verified against `avr` 0.1.6):

- `--repo org/name` or `--repo rep-xxx`; auto-detected from the git remote inside a checkout.
- `--org` falls back to the configured default (`avr config set org`).
- `--since` accepts `24h`, `7d`, `30d`, and (for workflow commands) `all`.
- `--json '?'` lists the available fields, `--json '*'` returns all, or pass a comma-separated subset.
- `-q/--jq` filters the JSON without an external `jq` binary.
- Non-TTY stdout switches lists to tab-separated output and `watch` to NDJSON.

Discover fields rather than guessing them:

```bash
avr run list --json '?'
avr workflow view ci.yml --json '?'
```

## Step 1 — orient before measuring

```bash
avr status --since 7d
```

Panels map directly onto the operating loop: `SLOWEST WORKFLOWS` and `SLOWEST JOBS` propose bottleneck candidates; `WORKFLOWS SLOWING DOWN` and `JOBS SLOWING DOWN` surface regressions a single run would hide. Treat all four as *hypotheses to confirm*, never as the finding itself — the panels rank by median without regard to how often a job sits on the critical path.

## Step 2 — baseline percentiles

`avr workflow view` is the only command that returns `p95_duration_seconds`, so it is the fastest path to the median/p95 pair the skill requires:

```bash
avr workflow view "Check-only" --repo org/app --since 30d \
  --json name,runs,completed_runs,failure_count,flaked_count,median_duration_seconds,p95_duration_seconds
```

Observed on a real repository (2026-07-28): 708 runs, median 128s, p95 324.6s, 193 failures. A p95 that is ~2.5× the median means the tail — not the typical run — is what developers actually feel; optimizing the median here would miss the complaint.

`flaked_count` is Avrea's own flake signal, defined in the docs as jobs that failed where the same step succeeded in other runs. A high `failure_count` with `flaked_count: 0` points at real failures or a misconfigured gate, not instability — route to `references/testing-and-flakiness.md` only once flake is actually demonstrated.

## Step 3 — critical path from start offsets

The per-job breakdown in `avr workflow view --json '*'` carries fields absent from the documentation but present in the API. The decisive ones are `success_run_median_offset_seconds` (when a job starts, relative to run start) and `success_median_duration_seconds`. Offset plus duration reconstructs the DAG shape empirically, which is exactly what `references/measurement.md` asks for:

```bash
avr workflow view "Check-only" --repo org/app --since 30d --json '*' \
  -q '[.jobs[] | {job: .job.name,
                  start_p50: .success_run_median_offset_seconds,
                  dur_p50: .success_median_duration_seconds,
                  dur_p95: .success_p95_duration_seconds,
                  total: .total_duration_seconds,
                  runs: .count}] | sort_by(-.total)'
```

Read it as: a gap between one job's `start + duration` and its dependents' `start` is per-job setup and scheduling overhead, not your build. In the measured repository a change-detection job finished near 19s while its dependents started at ~43s — roughly 24s of unavoidable-looking overhead that is actually the cost of splitting work into separate jobs. That is direct evidence for the "tiny jobs with heavy setup" pitfall, and it argues for collocating short jobs rather than adding runners.

Sort by `total_duration_seconds` to find cost, but by `start_p50 + dur_p50` to find the critical path. They are frequently different jobs, and only the second one governs wall-clock feedback.

## Step 4 — A/B against the previous provider

Avrea can run jobs while GitHub-hosted runners "shadow" the same work. `--on-avrea / --shadowing` turns that into a controlled comparison — a rare chance to measure a runner change without re-running anything:

```bash
avr job list --repo org/app --since 30d -L 500 --on-avrea \
  --json job_name,duration_seconds \
  -q 'group_by(.job_name) | map({job: .[0].job_name, n: length,
        med: (map(.duration_seconds) | map(select(. != null)) | sort | .[length/2|floor])})
      | sort_by(-.n)'
```

Repeat with `--shadowing`. Measured on a real repository: a backend job ran 47s on Avrea versus 160s shadowing, while a lint job ran 8s versus 9s. The lesson generalizes beyond Avrea — faster hardware pays off on CPU-bound work and does nothing for short I/O-bound jobs. Use this to decide *which* jobs deserve a larger runner instead of upgrading the whole matrix.

Sample sizes differ between the two sets (15 vs 75 above); say so when reporting, and do not present a 2-run comparison as an established median.

## Step 5 — queue time

No field reports queue time directly. Derive it from `created_at` → `started_at` on jobs:

```bash
avr job list --repo org/app --since 7d -L 200 \
  --json job_name,created_at,started_at,duration_seconds,labels,running_on_avrea
```

Observed queue spreads ranged from 0s to ~167s on the same trigger, but the direction was not stable enough to generalize: in one window the larger `avrea-ubuntu-latest-16-vcpu` job started immediately, and in another it queued much longer than the 2-vCPU class. Treat these examples as proof that **runner-class queueing is fleet- and time-dependent**, not as advice to size up or down. Recompute medians and p95 per class on the repository you are optimizing, then route to `references/capacity-and-contention.md` and `references/runners-and-autoscaling.md` if queue time is genuinely a dominant p95 contributor.

## Step 6 — right-size from VM metrics

```bash
avr job metrics job-xxx --source cpu --source memory
avr job metrics job-xxx --source disk-io --source network --json
```

Sources: `cpu`, `memory`, `filesystem`, `load`, `disk-io`, `disk-ops`, `network`. The header prints the resolved VM size and runner label, so a job pinned to a 16-vCPU runner that never exceeds 2 vCPU of load is provable over-provisioning. Metrics may report `(no samples yet)` for very short or cancelled jobs — that is an absence of evidence, not evidence of idleness.

This is the correct order of operations for the skill's "only then add compute" rule: measure utilization first, resize second.

## Step 7 — logs and failure triage

```bash
avr run view run-xxx --steps                 # per-step timing
avr run view run-xxx --log-failed            # only failing steps
avr job logs job-xxx --step "Build" --level error
avr log search --repo org/app --query "OOM" --json content,timestamp,vm_id,step_name
avr run logs run-xxx --follow                # tail an in-progress job
```

`avr log search` is cross-run full-text search, which makes it the fastest way to test whether a suspected failure mode (OOM, ECONNRESET, timeout) is systemic or a one-off. Add `--no-pager` in non-interactive contexts.

## Step 8 — drive runs to a terminal state

The project rule "verify the green, never hang on it" has direct support:

```bash
avr run watch --repo org/app --exit-status   # non-zero if the run failed
avr workflow run ci.yml --ref my-branch --watch --exit-status
avr run watch run-xxx --ndjson | jq -c .     # event stream for scripting
```

`--exit-status` makes failure observable instead of silent. It does not add a watcher deadline, and there is a registration race worth knowing: without a `RUN_ID`, `avr run watch` auto-selects the *latest in-progress* run. Observed on a live repository (2026-07-28): pushing and immediately arming `avr run watch --ndjson --exit-status` printed `No in-progress workflow runs found for these repos.` and exited **0** — before the run had been indexed. An agent reads that as "no problem" and proceeds unverified. Wait for a run matching your exact SHA, then watch that id — or use the bounded watcher contract in `references/feedback-loops.md`, which handles registration, deadline, and supersession uniformly.

Always confirm `head_sha` matches the commit under test before accepting a green:

```bash
avr run view run-xxx --json head_sha,conclusion,status,run_attempt
```

A green run whose `head_sha` is not your commit is a false green, exactly as `references/measurement.md` states.

### Collapse re-run attempts before judging a verdict

`avr run list` returns **one record per attempt** sharing a `platform_run_id` (observed against `avr` 0.1.6, 2026-07-28; `gh run list` collapses attempts and does not need this). After `avr run rerun`, a query for the commit returns both `run_attempt: 1 (completed/failure)` and `run_attempt: 2 (in_progress)`. Reading them naively reports the stale failure; a watcher keyed on `platform_run_id` oscillates between the two. Keep the highest `run_attempt` per id:

```bash
avr run list --repo org/app --since 6h --limit 100 \
  --json platform_run_id,run_attempt,workflow,status,conclusion,head_sha \
  -q 'group_by(.platform_run_id)[] | max_by(.run_attempt)'
```

This is also the mechanical way to test a suspected flake: `avr run rerun <run-id> --yes` re-runs the *identical* commit, and a pass on attempt 2 with an unchanged tree demonstrates instability rather than a real defect (see `references/agent-feedback-loops.md`).

### Waiting on a run from an agent

`avr run watch --exit-status` is correct for a human at a terminal and for a foreground script. It is **not** a safe way for an autonomous agent to wait: it holds the foreground for the whole run and has no registration deadline, so a commit that triggers nothing (path filters) never returns. Off-TTY it emits NDJSON, which is scriptable — but the surrounding loop still needs its own deadline and a terminal verdict on every path. Use `scripts/ci-watch.py`, or wrap `avr run list` in an equivalent bounded loop.

`avr job ssh` is documented for live debugging, but in practice short jobs terminate before a session can attach — observed twice against `avr` 0.1.6 (2026-07-28) as `No running VM found for this job` on jobs lasting well under a minute. For jobs measured in seconds, prefer `avr job metrics <job-id>` and step timings; reserve SSH for long jobs you can catch mid-flight.

## Mutating commands — authorization required

`avr cache delete`, `avr run cancel`, `avr run rerun`, `avr settings set`, and `avr firewall *` change shared state. `cache delete --all` discards every cache entry for a repository and will slow the next runs for everyone. Confirm before running any of them, and never pass `--yes` to satisfy a prompt on someone else's behalf.

`avr job ssh` opens an interactive session on a live VM; it is a debugging tool, not a measurement one, and the VM is destroyed when the job ends.

## Sources

- Avrea CLI overview: https://docs.avrea.com/cli/ (accessed 2026-07-28)
- Avrea CLI reference: https://docs.avrea.com/cli/reference/ (accessed 2026-07-28)
- `avr run` / `job` / `workflow` / `cache` / `log` references under https://docs.avrea.com/cli/reference/ (accessed 2026-07-28)
- Avrea observability: https://docs.avrea.com/observability/ (accessed 2026-07-28)
- Avrea debugging and SSH: https://docs.avrea.com/debugging/ (accessed 2026-07-28)
- Local verification against `avr` 0.1.6 on a live organization (2026-07-28); per-job offset fields observed in API output are not currently documented.
