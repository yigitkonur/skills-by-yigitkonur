# Avrea CLI core reference (`avr` 0.1.6)

Read this when you need exact syntax, flags, JSON fields, output behavior, or
mutation classification for the released Avrea CLI. This file is pinned to:

- package: `avr-cli`
- executable: `avr`
- released version: `0.1.6`
- release tag: `v0.1.6`
- source SHA: `d1c368547a8ca31fad2ec0513c6a2cfc33e3cb80`

Start every session with:

```bash
command -v avr && avr --version
```

If the reported version is not `0.1.6`, treat this file as a historical pin,
not as the live truth, and re-check the current release before executing any
version-sensitive command.

## Global behavior

### Global options

| Flag | Purpose | CI use |
|---|---|---|
| `-V`, `--version` | Print CLI version | Pin evidence to a known surface |
| `--no-color` | Disable ANSI color | Stable captured logs |
| `-v`, `--verbose` | Print HTTP method/URL/status | Diagnose API failures; may expose URLs/query args in logs |
| `--links`, `--no-links` | Enable/disable OSC 8 links | Disable terminal control sequences in automation |
| `-h`, `--help` | Show help | Authoritative local command discovery |

Aliases verified in 0.1.6:

- `jobs` → `job`
- `repos` → `repo`
- `orgs` → `org`
- `logs` → `log`
- `workflows` → `workflow`
- hidden compatibility aliases also exist for `login` and `logout`

### JSON and output conventions

- `--json '?'` lists available fields.
- `--json '*'` returns the full documented projection.
- `--json a,b,c` projects named fields.
- `-q/--jq` filters JSON using the system `jq`; it is invalid without
  `--json`.
- Commands that support both `--json` and `--web` treat them as mutually
  exclusive.
- Single-record commands emit an object; list commands emit an array.
- Missing nested values become `null`.
- On a non-TTY, list commands switch to tab-separated output and watch
  commands switch to NDJSON.
- Long logs page only on a TTY; `--no-pager` or empty `AVR_PAGER`/`PAGER`
  disables paging.

### Exit codes

| Exit | Meaning |
|---:|---|
| `0` | Success |
| `1` | General/API/validation failure |
| `2` | Usage error |
| `4` | Authentication required or token rejected |

## Read-only CI and evidence commands

### `avr status`

```bash
avr status [--org ORG] [--repo REPO] [--since WINDOW] [--json]
```

Purpose: recent runs, slow workflows/jobs, regressions, and cache health.
Good first orientation before drilling into a workflow or job.

Mutation class: **read-only**.

### `avr health`

```bash
avr health [--json] [--jq EXPR]
```

Purpose: provider health check before blaming a repository change.

Mutation class: **read-only**.

### `avr run list`

```bash
avr run list \
  [--org ORG] [--repo REPO]... [--status STATUS]... [--branch BRANCH]... \
  [-w WORKFLOW]... [--since WINDOW | --from ISO --to ISO] \
  [-L LIMIT] [--cursor CURSOR] [--order created_at.desc|created_at.asc] \
  [--json FIELDS] [-q EXPR] [--web]
```

Important notes:

- `--since` cannot be combined with explicit `--from/--to` bounds.
- `-L/--limit` is 1–1000, default 20.
- Use it to build a comparable run population and verify `head_sha` before
  trusting a green run.

Mutation class: **read-only** (`--web` only opens a browser).

### `avr run view [RUN_ID]`

Flags:

- `--steps`
- `--log`
- `--log-failed`
- `--job TEXT`
- `--json`, `--jq`, `--web`, `--no-pager`

Use to inspect one run, its jobs, and failing steps; without a run ID it shows
recent runs.

Mutation class: **read-only**.

### `avr run logs RUN_ID`

Flags:

- `--job TEXT`
- `-f, --follow`
- `--failed`
- `--all-levels`
- `--no-pager`

Constraint: `--follow` and `--failed` cannot be combined.

Mutation class: **read-only**.

### `avr run watch [RUN_ID]`

Flags:

- `--repo`, `--org`
- `--exit-status`
- `--interval` (default 3s)
- `--ndjson`

Use for a one-shot terminal result. It can auto-select the latest in-progress
run for a repository, but that is **not** sufficient evidence for an exact
commit. Confirm the watched run's `head_sha` afterward or pass a known run ID.

Mutation class: **read-only polling**.

### `avr job list`

Key flags:

- `--repo`, `--org`
- `--name TEXT` (repeatable)
- `--status STATUS` (repeatable)
- `--on-avrea` / `--shadowing`
- `-w/--workflow`
- `--since`
- `-L/--limit` (1–1000, default 20)
- `--cursor`, `--order`, `--json`, `--jq`

Use for per-job timing populations, queue-time derivation, runner-label
breakdown, and Avrea-vs-shadow comparisons.

Mutation class: **read-only**.

### `avr job view JOB_ID`

Flags:

- `--log`
- `--log-failed`
- `--json`, `--jq`, `--web`, `--no-pager`

Mutation class: **read-only**.

### `avr job logs JOB_ID`

Flags:

- `--failed`
- `--step TEXT`
- `--level debug|info|notice|warning|error`
- `-f/--follow`
- `--all-levels`
- `--no-pager`

Constraint: `--follow` and `--failed` cannot be combined.

Mutation class: **read-only**.

### `avr job metrics JOB_ID`

Flags:

- repeatable `--source`:
  `cpu`, `memory`, `filesystem`, `load`, `disk-io`, `disk-ops`, `network`
- `--start`, `--end` (Unix seconds)
- `-w/--watch`
- `--json`

Use to prove CPU, memory, disk, or network bottlenecks before changing runner
size.

Mutation class: **read-only**.

### `avr job watch`

Flags:

- `--repo`, `--org`
- `--name` (repeatable)
- `--interval` (default 5s)
- `--ndjson`

Use to observe active jobs and queue/start patterns over time.

Mutation class: **read-only polling**.

### `avr workflow list`

Flags:

- `--repo`, `--org`
- `--since` (default `30d`, supports `all`)
- `-L/--limit`
- `--json`, `--jq`

Use for workflow-level counts, median duration, failures, and flakes.

Mutation class: **read-only**.

### `avr workflow view WORKFLOW`

`WORKFLOW` may be:

- Avrea `wfl-...` ID
- GitHub numeric workflow ID
- filename `ci.yml`
- filename stem `ci`
- display name

Flags:

- `--repo`, `--org`
- `--since` (default 30 days)
- `--json`, `--jq`, `--web`

This is the primary aggregated baseline command. Current live API also exposes
useful per-job start-offset fields, but they are undocumented and must be
labeled `observed` if used.

Mutation class: **read-only**.

### `avr cache list`

Flags:

- `--repo`, `--org`
- `--type`
- `--key`
- `--ref`
- `-L/--limit` (default 100)
- `--offset`, `--order`, `--json`, `--jq`, `--web`

Useful fields:

- `cache_type`
- `created_at`
- `hit_count`
- `key`
- `last_accessed_at`
- `ref`
- `size_bytes`
- `version`

Use to find large, cold, or duplicate entries before proposing cache changes.

Mutation class: **read-only**.

### `avr cache usage`

Fields:

- `by_type`
- `over_quota`
- `quota_bytes`
- `total_size_bytes`

Use to understand quota pressure before adding or deleting caches.

Mutation class: **read-only**.

### `avr log search`

Flags:

- `--repo`, `--org`
- `--query`
- `--stream stdout|stderr`
- `--level debug|info|warning|error`
- `--vm-id`
- `-L/--limit`
- `--json`, `--jq`

Use for cross-run full-text diagnosis of recurring failure signatures such as
OOMs, timeouts, or dependency-download issues.

Mutation class: **read-only**.

### `avr repo list`

Flags:

- `--org`
- `-L/--limit`
- `--json`, `--jq`

Use to resolve canonical repository IDs and confirm that a repository is
connected to Avrea.

Mutation class: **read-only**.

## Safe examples

### Build a workflow baseline

```bash
avr workflow view ci.yml --repo org/repo --since 30d \
  --json name,runs,completed_runs,failure_count,flaked_count,median_duration_seconds,p95_duration_seconds
```

### Derive queue time from jobs

```bash
avr job list --repo org/repo --since 7d -L 500 \
  --json job_id,job_name,created_at,started_at,duration_seconds,labels,running_on_avrea
```

Compute queue delay as `started_at - created_at`; Avrea 0.1.6 does not expose
a direct queue-duration field.

### Compare Avrea and shadow jobs

```bash
avr job list --repo org/repo --since 30d --on-avrea \
  --json job_name,duration_seconds
avr job list --repo org/repo --since 30d --shadowing \
  --json job_name,duration_seconds
```

### Drive a run to a terminal state

```bash
avr run watch run-123 --exit-status --ndjson
avr run view run-123 --json head_sha,conclusion,status,run_attempt
```

Watch output is only useful after the exact run identity is confirmed.

## What is deliberately not here

These are **not** verified released 0.1.6 commands and must not appear in
runnable examples for this skill:

- `avr vm ...`
- `avr repo public-mirror ...`
- `avr org saml ...`
- `avr org email-domain claim|verify`
- firewall flows keyed by `--job` instead of the released `--vm`
- any artifact-download or per-run cost command

See `cli-evidence.md` for task-oriented baselines and `cli-admin-reference.md`
for mutating/admin commands.

## What is deliberately not here

The following capabilities are **not verified in released 0.1.6** and must not
appear in runnable examples for this skill:

- artifact list/download/delete
- per-run cost or runner-minute accounting
- direct queue_duration field
- `avr vm ...`
- `avr repo public-mirror ...`
- `avr org saml ...`
- `avr org email-domain claim`
- `avr org email-domain verify`
- `firewall flow-summaries --job` (released 0.1.6 still uses `--vm`)

Treat those as future or provider-native topics, not as current CLI surface.

## Sources

- Release docs index: https://docs.avrea.com/cli/reference/ (accessed 2026-07-28)
- GitHub release tag: https://github.com/avrea-com/cli/releases/tag/v0.1.6 (accessed 2026-07-28)
- Release source tag: https://github.com/avrea-com/cli/tree/v0.1.6 (accessed 2026-07-28)
- Verified locally against installed `avr` 0.1.6 (2026-07-28)
