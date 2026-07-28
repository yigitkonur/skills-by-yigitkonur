---
name: ci-cd-optimize
description: Use if diagnosing or optimizing slow CI/CD while preserving required checks.
metadata:
  author: yigitkonur
  version: 1.0.0
  category: devops
  tags: [ci-cd, github-actions, gitlab-ci, buildkite, circleci, typescript, swift, xcode, pipeline-performance]
---

# CI/CD Optimize

Diagnose slow CI/CD from evidence, optimize the critical path, and prove the pipeline remains effective. Do not make pipelines faster by deleting the checks that make them useful.

## Operating loop

### 1. Frame the target and constraints

Identify the exact pipeline, branch/event, current median and p95 time-to-feedback, failure rate, and required gates. Separate these before recommending anything:

- **Queue time** — trigger to runner start: capacity, scheduling, concurrency, or runner topology.
- **Setup time** — checkout, runtime install, dependency restore, environment boot.
- **Execution time** — lint, typecheck, build, tests, package, scan, deploy.
- **Transfer time** — cache/artifact downloads and uploads, Docker layers, registries, LFS.
- **Finalization** — reporting, merge status, deployment health, cleanup.

Required gates are requirements, not bottlenecks. If a gate must stay, optimize its scope, parallelism, cache, or placement.

### 2. Measure the exact baseline

Use the same commit and comparable runner class. Prefer at least three runs when timings vary. Capture queue, setup, execution, transfer, per-job duration, dependency graph, cache hit/miss, retry count, and artifact identity.

Rules:

- Use median and p95; CI timings are right-skewed.
- A green run on a stale SHA, empty diff, or different workflow is not evidence.
- A cache hit is useful only if restore plus post-hit work beats a clean run.
- Flaky retry-pass is instability and cost, not proof of reliability.

Prefer the platform's own aggregated history over hand-collected timings when it exists, then verify sample size and window. If the repository runs on Avrea (`runs-on:` labels begin with `avrea-`) and `avr` is installed and authenticated, read `references/avrea/cli-evidence.md` — it returns median/p95, per-job start offsets, flake counts, and cache hit counts directly. Confirm availability with `command -v avr && avr auth status` before depending on it, and fall back to provider-native measurement otherwise.

For the metric definitions, baseline protocol, and the rule about claiming only the evidence rung you reached, read `references/measurement.md`.

### 3. Find the critical path

Build the job DAG from actual dependencies, not stage labels. Optimize jobs with high critical-path rate and high exclusive time. A large total CPU-time reduction on parallel non-critical work may produce zero wall-clock improvement.

Apply the performance order before adding compute:

1. **Do not start it** — duplicate triggers, draft-PR work, irrelevant events, unrelated packages, full checkout, redundant matrices.
2. **Cancel it when stale** — superseded PR runs, obsolete deployments only when safe, hung tail jobs.
3. **Reuse previous work** — correct caches, remote task cache, immutable build artifacts, prebuilt toolchains.
4. **Shorten the critical path** — DAG shape, split long jobs only when setup is amortized, historical test sharding.
5. **Move fewer bytes** — checkout scope, cache size, Docker context/layers, artifact paths/compression.
6. **Only then add compute** — larger runners, more workers, more capacity after queue and utilization evidence.

Ask in order:

1. Is the pipeline starting duplicate, stale, draft-only, or unrelated work? Read `references/github-actions.md` and `references/change-based-ci.md`.
2. Is queue time the dominant p95 contributor, or has job count already crossed a concurrency ceiling? Read `references/capacity-and-contention.md` first, then `references/runners-and-autoscaling.md`.
3. Is setup or dependency restore dominant? Read `references/typescript-toolchain.md` and `references/caching.md`.
4. Is checkout, cache, Docker context, or artifact transfer dominant? Read `references/network-and-artifacts.md`.
5. Is the pipeline running work unrelated to this change? Read `references/change-based-ci.md` and `references/monorepos.md`.
6. Are tests dominant? Read `references/testing-and-flakiness.md` and `references/integration-environments.md`.
7. Is Docker/OCI work dominant? Read `references/containers.md`.
8. Are security scans dominant? Read `references/security-gates.md`.
9. Is deployment slow or repeated? Read `references/deployment.md`.
10. Is it a Swift/Xcode pipeline? Read `references/swift-xcode.md`.
11. Is the provider config itself the issue? Route to `references/github-actions.md`, `references/gitlab-ci.md`, `references/circleci.md`, or `references/buildkite.md`.
12. Is the build graph/cache correctness itself suspect? Read `references/bazel-and-remote-execution.md`.
13. Is the consumer of these results an agent or unattended session that must not block on CI? Read `references/agent-feedback-loop.md`.
14. Does the repository already run on Avrea, or is runner hardware the measured bottleneck? Read `references/avrea/platform-and-runners.md` and `references/avrea/caching.md`; for building the baseline with the `avr` CLI, read `references/avrea/cli-evidence.md`.
15. Is the proposed speedup about to weaken a required check, a trust boundary, or artifact identity? Read `references/effectiveness-contract.md` before recommending it.
16. Is a load-bearing claim about vendor behavior unverified, or is a cited source stale? Read `references/evidence-and-sources.md`.

### 4. Choose one bounded experiment

Select the smallest reversible change that attacks the measured critical path. Every recommendation must state:

- evidence observed,
- expected wall-clock impact,
- effectiveness risk,
- security/trust-boundary risk,
- cost effect,
- rollback or fallback.

Prefer, in this order: prevent unneeded work → cancel stale work → reuse verified prior work → improve cache correctness → remove artificial dependencies → parallelize independent work → shard slow work by measured duration → reduce transferred bytes → improve runner capacity → move heavy work off the PR path only with a full-run fallback → change provider architecture.

### 5. Preserve effectiveness

Never claim an optimization if it does any of these:

- skips required tests, coverage, type checking, or security gates,
- lets untrusted code write to a cache trusted branches consume,
- accepts a green check on a stale or unrelated commit,
- replaces immutable artifact promotion with rebuilds per environment,
- hides failures behind retries, broad `continue-on-error`, or weakened assertions,
- makes change detection use an unverified merge base.

Use full validation as the safe fallback whenever changed files, merge base, cache correctness, dependency graph completeness, or security scope cannot be proven. When a proposed change is near any of these lines, check it against `references/effectiveness-contract.md` before recommending it.

### 5b. Wait for the result without blocking

When an agent triggers the run and consumes the verdict — the common case for autonomous work and CI-only verification — never block the session on it. Arm a bounded, commit-pinned watcher that emits state changes and always ends in a terminal verdict, then keep working. The bundled `scripts/ci-watch.sh` implements the contract for GitHub Actions; `references/agent-feedback-loop.md` gives the contract, the two patterns that fail (TTY-shaped `run watch`, success-only polling), and how to wire it to a streaming-notification facility such as the Monitor tool.

### 6. Verify after the change

Re-run on the same commit first, then a normal representative commit. Compare median and p95 wall-clock, queue time, cache behavior, first-time pass rate, cost, and failure/rework signals. Confirm the exact run head SHA contains the change and the deployed artifact digest or workflow run is the intended one.

Report only the level actually verified: config review, syntax validation, one CI run, repeated CI runs, or production evidence.

## Minimal TypeScript example

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
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0
      - id: filter
        run: |
          git diff --name-only "${{ github.event.pull_request.base.sha || 'HEAD~1' }}...${{ github.sha }}" \
            | grep -E '^(src|packages|apps|package.json|pnpm-lock.yaml|tsconfig)' \
            && echo "source=true" >> "$GITHUB_OUTPUT" || echo "source=false" >> "$GITHUB_OUTPUT"

  verify:
    needs: changes
    if: needs.changes.outputs.source == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-node@v6
        with:
          node-version: 24
          cache: pnpm
          cache-dependency-path: pnpm-lock.yaml
      - run: corepack pnpm install --frozen-lockfile
      - run: corepack pnpm exec tsc -b --pretty false
      - run: corepack pnpm test -- --run
```

Treat this as a shape, not a universal template. Adapt cache, affected detection, and jobs from measured evidence.

## Common pitfalls

| Pitfall | Better move |
|---|---|
| Optimizing before measuring | Capture baseline queue/setup/execution/critical path first. |
| Duplicate `push` and PR runs | Trigger PRs on PR events; trigger main/release pushes only. |
| Draft PRs start expensive jobs | Keep planner cheap; gate expensive jobs until ready for review. |
| Caching `node_modules` by default | Cache the package-manager store; measure restore versus install. |
| Workflow path filter blocks required checks | Run a cheap change-detection job and condition expensive jobs. |
| Affected detection on shallow clone | Fetch required history or use event SHAs; otherwise run all. |
| Artificial `needs` chains | Start independent lint/typecheck/build work together. |
| More runners without queue evidence | Measure queue p95 and runner utilization before spending. |
| Full suite duplicated in every shard | Split tests by file/timing so each test runs once. |
| Tiny jobs with heavy setup | Collocate work until separate runner setup is amortized. |
| Coverage off PR path with no fallback | Keep a required scheduled/merge-queue full run. |
| Remote cache writable by untrusted PRs | Read-only PR cache or isolated cache namespace. |
| Retrying flakes forever | Bound retries, quarantine, assign ownership, track flake rate. |
| Rebuilding deploy artifacts per environment | Build once; promote the same immutable digest. |
| Agent blocks in the foreground waiting for CI | Arm a non-blocking watcher on the pinned SHA and keep working. |
| Watcher greps only for the success marker | A red run looks identical to a running one — emit every terminal state. |
| Piping a provider `watch` subcommand into a line consumer | Those redraw a TTY block on an interval; pipe it through `cat -A` once to confirm before adopting. |
| Treating a concurrency auto-cancel as failure | If the only non-green conclusions are `cancelled`, it is superseded/cancelled, never red. |
| Artifact upload on every success | Upload exact outputs; diagnostics on failure; summaries for small values. |
| Large cache entries with zero hits | Check hit counts; cold entries consume quota and slow every save. |
| Upgrading the whole matrix to bigger runners | Resize only CPU-bound critical-path jobs proven by VM utilization. |

## Reference files

| File | Read when |
|---|---|
| `references/measurement.md` | Building the baseline, percentiles, critical path, telemetry, or proving a result. |
| `references/effectiveness-contract.md` | Deciding whether a proposed speedup weakens validation, security, or artifact identity. |
| `references/agent-feedback-loop.md` | An agent or long-running session must learn a CI verdict without blocking, a watcher hangs or floods, or CI is the only verification surface. |
| `references/capacity-and-contention.md` | Queue share is high, parallelism stopped paying off, before splitting or fanning out jobs, or when A/B arms ran under different pool load. |
| `references/caching.md` | Any dependency/build cache design, restore-key, cache-hit, cache-poisoning, or transfer-cost question. |
| `references/change-based-ci.md` | Path filters, affected commands, merge queues, merge-base correctness, or full-run fallback rules. |
| `references/github-actions.md` | GitHub Actions workflows, caches, concurrency, artifacts, merge queues, required checks, or larger runners. |
| `references/gitlab-ci.md` | GitLab `needs`, child pipelines, cache/artifacts, interruptible jobs, resource groups, rules, or runners. |
| `references/circleci.md` | CircleCI caching, workspaces, test splitting, dynamic config, Docker layer caching, or resource classes. |
| `references/buildkite.md` | Buildkite dynamic pipelines, queues, autoscaling, concurrency groups, artifacts, or hosted agents. |
| `references/monorepos.md` | Nx, Turborepo, affected graphs, remote caches, distributed execution, or package/task inputs. |
| `references/bazel-and-remote-execution.md` | Bazel query, hermetic builds, remote cache/execution, or choosing graph-native builds. |
| `references/typescript-toolchain.md` | npm/pnpm/Yarn/Bun installs, Corepack, TypeScript project references, `tsbuildinfo`, bundlers, or generated code. |
| `references/testing-and-flakiness.md` | Sharding, historical timing, retries, flaky ownership, coverage merging, Jest/Vitest/Playwright. |
| `references/integration-environments.md` | Testcontainers, service containers, database templates, fixtures, contract tests, or preview databases. |
| `references/containers.md` | BuildKit, multi-stage Dockerfiles, cache mounts/backends, multi-platform builds, provenance, or image security. |
| `references/security-gates.md` | Fast but effective SAST, dependency, secret, container, SBOM, provenance, and policy gates. |
| `references/runners-and-autoscaling.md` | Hosted versus self-hosted, ephemeral runners, queues, spot capacity, ARM/x64/macOS, Kubernetes fleets. |
| `references/network-and-artifacts.md` | Checkout depth, sparse/partial clone, LFS, package proxies, artifact compression, uploads, or registry locality. |
| `references/deployment.md` | Immutable artifacts, build-once-deploy-many, canary/blue-green, migrations, previews, rollback, and exact-artifact verification. |
| `references/swift-xcode.md` | Swift/Xcode builds, SwiftPM, test plans, simulator sharding, macOS runners, xcresult, or DerivedData. |
| `references/evidence-and-sources.md` | Checking claims, dated source ledger, research method, or refreshing stale vendor behavior. |

### Optional: Avrea reference kit

Read only when the repository runs on Avrea (`runs-on:` labels start with `avrea-`) or Avrea is being evaluated as a runner change. The core loop above is provider-neutral and does not depend on these files.

| File | Read when |
|---|---|
| `references/avrea/cli-evidence.md` | Using the `avr` CLI to build a baseline: median/p95, per-job start offsets, queue time, VM metrics, flake counts, cache hit counts, or driving a run to a terminal state. |
| `references/avrea/platform-and-runners.md` | Runner labels and sizing, migration from GitHub-hosted runners, A/B shadowing, observability, OTel export, live SSH debugging, or the third-party trust boundary. |
| `references/avrea/caching.md` | Actions/build/package cache layers, Turborepo or Docker `url_v2` wiring, registry proxy caveats, quota and LRU eviction, or diagnosing cold cache entries. |

## Bundled script

`scripts/ci-watch.sh <pinned-sha> [branch] [deadline-min]` is a ready GitHub Actions watcher implementing every requirement in `references/agent-feedback-loop.md`: commit-pinned across all workflows, diff-gated, heartbeating under a typical prompt-cache TTL, and guaranteed to end in `CI-DONE <verdict>` (success, failure, timeout, no-run, superseded, probe-dead). Requires authenticated `gh` and `jq`; set `CI_WATCH_REPO=org/name` or run inside the repo. For another provider, keep the event contract and replace only the probe command.

## Guardrails

- Do not recommend vendor-specific flags from memory; verify mutable provider behavior against current official docs when it is load-bearing, and record the check per `references/evidence-and-sources.md`.
- Do not assume a CI platform or its CLI is present; probe first (`command -v`, `--version`, auth check) and fall back to provider-native evidence when it is not.
- Do not run a platform CLI's mutating commands without authorization — cache deletion, run cancel/rerun, org or repository settings, and firewall rules change shared state.
- Do not ask for approval before a reversible, measured optimization; ask before weakening a gate, changing production deployment behavior, or introducing a shared trust boundary.
- Do not add a large tool (Bazel, remote execution, self-hosted fleet, commercial TIA) unless the measured bottleneck and operating capacity justify it.
- Do not bundle generated pipeline templates blindly; produce the smallest config change justified by evidence.
- Do not report "CI is faster" without the before/after evidence and the exact run identity.

## Done criteria

The work is complete only when the baseline, chosen bottleneck, changed files/config, measured result, effectiveness checks, remaining risks, and verification level are all reported. If a provider branch was not exercised, say so explicitly rather than implying coverage.
