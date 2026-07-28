---
name: ci-cd-optimize
description: Use if diagnosing or optimizing slow CI/CD, or if an agent must wait on CI without stalling, while preserving required checks.
metadata:
  author: yigitkonur
  version: 1.1.0
  category: devops
  tags: [ci-cd, github-actions, gitlab-ci, buildkite, circleci, monorepo, docker, swift, xcode, pipeline-performance, ci-monitoring]
---

# CI/CD Optimize

Diagnose slow CI/CD from evidence, choose the smallest reversible improvement,
and prove the pipeline is still effective afterward. Treat the **feedback loop**
(the way a human or agent learns the result) as part of the pipeline, not as
something outside it. A 90-second pipeline is not fast if the caller waits 20
minutes to notice the red check.

## What this skill is for

Use this skill to optimize any delivery pipeline that has a real correctness or
cost surface: GitHub Actions, GitLab CI, CircleCI, Buildkite, monorepo task
runners, Docker/OCI build pipelines, test matrices, Swift/Xcode CI, or a deploy
pipeline whose run time dominates development or release flow.

It is workflow-first, not YAML-first. Start from **what is slow, what is risky,
and what proof is needed**, then route to the narrowest reference that answers
that question.

## Operating loop

### 1. Frame the target and the verification surface

Start by naming exactly what is being optimized:

- workflow / pipeline name
- trigger (`push`, `pull_request`, merge queue, schedule, deploy, release)
- branch or commit under study
- what the caller actually cares about: first failure, first green, deploy live,
  artifact published, release signed, etc.
- required gates that must not weaken
- whether CI is the **only** trusted verification surface

If CI is the only trusted verification surface, the feedback loop is mandatory
work, not polish. An agent that pushes and then waits badly is blind to the
result even if the pipeline itself is well-designed.

### 2. Read history before touching config

Read previous runs first. Do not start with a config rewrite.

Build the baseline from the platform's own history when it exists, then verify
sample size, time window, runner class, and commit identity. Separate these
components before proposing anything:

- **Queue time** — trigger to runner start
- **Setup time** — checkout, runtime install, dependency restore, env boot
- **Execution time** — tests, build, scans, package, deploy
- **Transfer time** — caches, artifacts, Docker layers, registries, LFS
- **Finalization** — reports, deploy health, cleanup, status aggregation

Read `references/measurement.md` first whenever the bottleneck is not already
obvious. If the repository runs on Avrea and the `avr` CLI is available and
authenticated, `references/avrea/cli-evidence.md` gives the direct evidence path
for medians, p95s, per-job start offsets, queue time, flake counts, and cache
hits.

### 3. Find the true bottleneck, not the loudest one

Build the job DAG from actual dependencies, not stage labels. Optimize the work
that dominates the **critical path**.

A large CPU-time reduction on parallel non-critical work can move wall-clock by
zero. Likewise, a larger runner can make execution faster and wall-clock slower
if queue time dominates.

Apply the optimization order in this sequence:

1. **Do not start the work** — duplicates, draft PR work, irrelevant events,
   unrelated packages, redundant matrices.
2. **Retire stale work** — superseded runs, obsolete deploys, hung tail jobs when
   safe.
3. **Reuse correct previous work** — caches, immutable artifacts, remote task
   caches, prebuilt toolchains.
4. **Shorten the critical path** — remove artificial dependencies, fix topology,
   shard only when setup is amortized.
5. **Move fewer bytes** — sparse checkout, smaller cache/artifact payloads,
   tighter Docker context, local registry/proxy.
6. **Only then add compute or capacity** — more workers, larger runners, more
   slots, a different fleet.

### 4. Route by measured symptom

Ask these in order and read only the matching references:

1. Is duplicate, stale, draft-only, or unrelated work running? Read
   `references/change-based-ci.md` and the provider reference.
2. Is queue p95 a large part of total wall-clock, or is job count already at the
   platform's concurrency ceiling? Read `references/capacity-and-contention.md`
   before touching parallelism.
3. Is setup or dependency restore dominant? Read `references/caching.md` and the
   language/toolchain reference (`references/typescript-toolchain.md`,
   `references/swift-xcode.md`, etc.).
4. Is checkout, cache transfer, Docker context, or artifact motion dominant?
   Read `references/network-and-artifacts.md` and `references/containers.md`.
5. Is the pipeline running work unrelated to this change? Read
   `references/change-based-ci.md` and, for monorepos, `references/monorepos.md`.
6. Are tests dominant or flaky? Read `references/testing-and-flakiness.md` and
   `references/integration-environments.md`.
7. Is Docker/OCI build work dominant? Read `references/containers.md`.
8. Are security scans dominant? Read `references/security-gates.md`.
9. Is deployment or rollout the long pole? Read `references/deployment.md`.
10. Is runner class or autoscaling the suspected cause? Read
    `references/runners-and-autoscaling.md`.
11. Is the build graph/cache correctness itself suspect? Read
    `references/bazel-and-remote-execution.md`.
12. Is the provider workflow/config itself the issue? Route to the provider file:
    `references/github-actions.md`, `references/gitlab-ci.md`,
    `references/circleci.md`, `references/buildkite.md`.
13. Must a human or agent wait on the result without stalling? Read
    `references/feedback-loops.md` and, if a bundled watcher is appropriate,
    `scripts/ci-watch.py`.
14. Is the proposed speedup near a trust boundary, required check, cache
    namespace, or artifact identity? Read `references/effectiveness-contract.md`
    before recommending it.
15. Is a vendor claim or cited example stale or load-bearing? Read
    `references/evidence-and-sources.md`.

### 5. Choose one bounded experiment

Select the smallest reversible change that attacks the measured bottleneck.

For every recommendation, state all six:

- evidence observed
- expected wall-clock effect
- effectiveness / correctness risk
- security / trust-boundary risk
- cost effect
- rollback or fallback

Prefer, in this order: prevent work → cancel stale work → reuse safe work → fix
cache correctness → remove artificial dependencies → parallelize/shard measured
work → reduce transferred bytes → change runner capacity → move heavy work off
PR path only with a full-run fallback → change provider architecture.

### 6. Treat the feedback loop as part of the optimization

Whoever waits on CI needs a mechanism that always terminates with a verdict.
Never block the session on a foreground `watch`, a TTY-oriented CLI, or a
success-only loop. Arm a bounded watcher pinned to the exact pushed SHA, then
keep working.

A good watcher must:

- terminate on success, failure, timeout, no-run, superseded, and probe-dead
- emit on failure, not just success
- emit only state changes plus heartbeats
- be pinned to the exact commit or build id
- have a registration deadline and an overall deadline
- wait a settle window before all-green success, so late follow-up workflows are
  observed

Read `references/feedback-loops.md` for the contract, anti-patterns,
provider-neutral wiring, and flake triage. `scripts/ci-watch.py` is the bundled
reference implementation.

### 7. Preserve effectiveness

Never claim an optimization if it does any of these:

- skips required tests, coverage, typing, security gates, or release checks
- lets untrusted code write a cache trusted branches consume
- accepts a green check on a stale or unrelated commit
- replaces immutable artifact promotion with rebuilds per environment
- hides failures behind retries, broad `continue-on-error`, or weakened
  assertions
- relies on an unverified merge base or partial graph

If the repo is CI-only, remember that the watcher itself is part of
preserving effectiveness: a hang, stale green, or never-registered run is a
broken verification path.

Use `references/effectiveness-contract.md` whenever a proposed change approaches
one of these lines.

### 8. Verify after the change

Re-run on the same commit first, then a normal representative commit. When the
change is in-job, compare arms under the **same contention state**; a run against
an idle pool and one against a saturated pool are not comparable even on the same
commit and runner class. Interleave arms when practical.

Report only the rung actually reached:

- config review
- syntax/schema validation
- one exact-commit CI run
- repeated comparable CI runs
- production/trend evidence

Always confirm the run's head SHA contains the change and that the expected
workflows/jobs actually ran. A green on the wrong workflow or wrong commit is a
false green.

## Minimal example — use as a shape, not a template

```yaml
name: ci
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
    branches: [main]
  push:
    branches: [main, 'release/**']
  merge_group:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  changes:
    if: github.event_name != 'pull_request' || github.event.pull_request.draft == false
    runs-on: ubuntu-slim
    outputs:
      source: ${{ steps.filter.outputs.source }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - id: filter
        run: |
          git diff --name-only "$BASE...$HEAD" \
            | grep -qE '^(src|packages|apps|package.json|pnpm-lock.yaml|tsconfig)' \
            && echo source=true >> "$GITHUB_OUTPUT" || echo source=false >> "$GITHUB_OUTPUT"

  verify:
    needs: changes
    if: needs.changes.outputs.source == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 24
          cache: pnpm
          cache-dependency-path: pnpm-lock.yaml
      - run: corepack pnpm install --frozen-lockfile
      - run: corepack pnpm exec tsc -b --pretty false
      - run: corepack pnpm test -- --run
```

## Common pitfalls

| Pitfall | Better move |
|---|---|
| Optimizing before measuring | Capture a baseline first. |
| Duplicate `push` and PR runs | Trigger PRs on PR events; trigger pushes only where they matter. |
| Draft PRs start expensive jobs | Gate expensive work until ready for review. |
| Caching `node_modules` by default | Cache the package-manager store and measure restore vs clean install. |
| Planner/CI config routes itself narrowly | Escalate planner and CI config changes to full validation. |
| Affected detection on shallow history | Fetch enough history or use provider SHAs; otherwise run all. |
| Adding a planner or aggregate job "for clarity" | Price the queue/setup hop against the work it does. |
| Splitting while already at the concurrency ceiling | Establish the ceiling first; when capped, merge work that shares setup. |
| Comparing contended and uncontended runs | Match contention state; compare execution time for in-job changes. |
| Blocking on a vendor `watch` command | Arm a bounded SHA-pinned watcher and keep working. |
| Reading a branch-tip green | Pin the pushed SHA and verify the run's head commit. |
| Treating `timeout` as pass or failure | It means no verdict yet; inspect the run and re-arm if needed. |
| Full suite duplicated in every shard | Split so each required test runs exactly once. |
| Tiny jobs with heavy setup | Collocate work until separate setup is amortized. |
| Coverage off PR path with no fallback | Keep a required full-run path. |
| Remote cache writable by untrusted PRs | Read-only PR cache or isolated namespace. |
| Flake "fixed" by retry/skip | Re-run the identical commit to prove a flake; do not weaken the test. |
| First default-branch run after a cache-key change called a regression | Branch caches cannot seed default branch; prove the expected cold-first pattern. |
| Larger runners chosen by intuition | Measure queue per class and utilization first; downsizing is common. |

## Bundled script

| Script | Use when |
|---|---|
| `scripts/ci-watch.py` | Wait on the exact pushed SHA without stalling. GitHub Actions works out of the box; any other provider via `--cmd` printing `<name>: <state>` lines. Stdlib-only Python. |

## Reference files

| File | Read when |
|---|---|
| `references/measurement.md` | Building the baseline, critical-path analysis, percentiles, or proving a result. |
| `references/capacity-and-contention.md` | Queue share is high, parallelism stopped paying off, before sharding/splitting, or when comparing arms under different load. |
| `references/feedback-loops.md` | An agent or human must wait on CI without stalling: watcher contract, verdicts, settle windows, flake triage. |
| `references/effectiveness-contract.md` | Deciding whether a speedup weakens validation, security, or artifact identity. |
| `references/caching.md` | Dependency/build/compiler/remote cache design and invalidation. |
| `references/change-based-ci.md` | Path filters, affected commands, merge-base correctness, and full-run fallback rules. |
| `references/github-actions.md` | GitHub Actions workflows, concurrency, caches, artifacts, merge queue, required checks. |
| `references/gitlab-ci.md` | GitLab `needs`, child pipelines, caches/artifacts, interruptible jobs, resource groups. |
| `references/circleci.md` | CircleCI caching, workspaces, test splitting, dynamic config, resource classes. |
| `references/buildkite.md` | Buildkite dynamic pipelines, queues, autoscaling, concurrency groups, artifacts. |
| `references/monorepos.md` | Nx, Turborepo, affected graphs, task inputs, remote caches, distributed execution. |
| `references/bazel-and-remote-execution.md` | Bazel query, hermeticity, remote cache/execution, graph-native builds. |
| `references/typescript-toolchain.md` | npm/pnpm/Yarn/Bun, Corepack, TS project references, `tsbuildinfo`, bundlers, generated code. |
| `references/testing-and-flakiness.md` | Sharding, historical timing, flaky ownership, retries, coverage merging, Jest/Vitest/Playwright. |
| `references/integration-environments.md` | Testcontainers, service containers, fixture DBs, contract tests, preview DBs. |
| `references/containers.md` | BuildKit, multi-stage Dockerfiles, cache mounts/backends, provenance, image security. |
| `references/security-gates.md` | Fast but effective SAST, dependency, secret, container, SBOM, provenance, policy gates. |
| `references/runners-and-autoscaling.md` | Runner classes, queues, hosted vs self-hosted, spot capacity, ARM/x64/macOS, Kubernetes fleets. |
| `references/network-and-artifacts.md` | Checkout depth, sparse/partial clone, LFS, package proxies, artifact compression/uploads. |
| `references/deployment.md` | Build-once deploy-many, canary/blue-green, migrations, previews, rollback, exact-artifact verification. |
| `references/swift-xcode.md` | Swift/Xcode builds, test plans, simulator sharding, macOS runners, xcresult, DerivedData. |
| `references/evidence-and-sources.md` | Checking whether a CI/CD claim is current, resolving conflicts, and refreshing this skill. |
| `references/avrea/*.md` | Optional Avrea kit: CLI evidence, runner sizing, and cache behavior when the repo runs on Avrea. |

## Guardrails

- Do not recommend provider-specific commands from memory when the behavior is load-bearing; verify against current docs or provider source and record the check.
- Do not assume a CLI or platform exists; probe first (`command -v`, `--version`, auth check) and fall back to provider-native evidence if absent.
- Do not mutate shared CI state (cache deletion, run cancel/rerun, org settings, firewall rules) without authorization.
- Do not ask for approval before a reversible, measured optimization; ask before weakening a gate, changing production deployment behavior, or introducing a shared trust boundary.
- Do not add a large tool (Bazel, remote execution, self-hosted fleet, commercial TIA) unless the measured bottleneck and operating capacity justify it.
- Do not bundle generated pipeline templates blindly; produce the smallest change justified by evidence.
- Do not report "CI is faster" without the before/after evidence and the exact run identity.

## Done criteria

The work is complete only when the baseline, chosen bottleneck, changed files/config, measured result, effectiveness checks, remaining risks, and verification rung are all reported. If a provider branch or feedback-loop path was not exercised, say so explicitly rather than implying coverage.
