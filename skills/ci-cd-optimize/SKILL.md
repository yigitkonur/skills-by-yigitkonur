---
name: ci-cd-optimize
description: Use skill if you are diagnosing or optimizing slow, flaky, queued, expensive, or cache-inefficient CI/CD pipelines, or waiting on remote runs, while preserving required checks, security gates, and exact-commit verification.
metadata:
  author: yigitkonur
---

# CI/CD Optimize

Diagnose slow CI/CD from evidence, optimize the critical path, close the
feedback loop on the exact commit, and prove the pipeline remains effective.
Never make a pipeline faster by deleting the checks that make it useful.

## When to use — and when not to

Use for: slow median or p95 feedback; long runner queues; repeated setup or
dependency restore; cache misses and expensive cache transfers; excessive
test time or flakiness; duplicate/stale/irrelevant runs; runner sizing and
pool contention; CI cost; watching a pushed commit to a terminal verdict;
deployment pipeline convergence and artifact identity.

Not for:

- A one-line YAML syntax or typo fix with no performance question — just fix it.
- Application runtime performance (slow endpoints, page loads) — that is app
  profiling, not pipeline work.
- Executing a deployment when optimization is not the task — use the
  deployment workflow/skill for the target platform.
- Reviewing code or hunting product bugs — use the review workflow.
- Any request to delete or bypass required tests or security gates to "go
  faster" — decline and offer scope/parallelism/cache alternatives.

## Analysis is not authorization

Reading configuration and history, computing baselines, drafting
recommendations, editing local files on request, and running validators are
normal work — proceed. The following change shared or external state and
require explicit authorization every time, no matter how confident the
analysis is:

- pushing or merging beyond what was asked,
- cancelling or re-running other people's CI runs,
- deleting caches, changing CI/org/repository settings or firewall rules,
- SSH into live runners,
- deployments, promotions, rollbacks, production migrations,
- weakening, skipping, or un-requiring any gate.

## Operating loop

Follow the full engagement sequence in
`references/optimization-workflow.md` — read it before touching any
workflow YAML. The compressed shape:

1. **Frame** — exact pipeline, event/branch, current median/p95, failure
   rate, required gates. Separate queue / setup / execution / transfer /
   finalization time; they have different fixes.
2. **Measure** — comparable runs, same commit, median and p95, cache
   hit/miss, per-job timing and DAG. Protocol in `references/measurement.md`.
3. **Locate the critical path** — job DAG from real dependencies. Big
   CPU-time savings off the critical path buy zero wall-clock. Order of
   attack: don't start it → cancel stale work → reuse verified work →
   shorten the path → move fewer bytes → only then add compute.
4. **Choose one bounded experiment** — smallest reversible change; state
   evidence, expected wall-clock impact, effectiveness risk, cost, rollback.
5. **Verify remotely on the exact SHA** — push, then watch to a terminal
   verdict with `references/feedback-loops.md` and `scripts/ci-watch.py`.
   Compare matched before/after runs; report the evidence rung reached.
6. **Stop** — when the bottleneck is no longer material, when two repairs
   fail the same way, or when only gate-weakening ideas remain.

## Routing: what is dominant?

1. Duplicate, stale, draft-only, or unrelated work starting? →
   `references/github-actions.md`, `references/change-based-ci.md`.
2. Queue time dominates p95, or jobs multiply past the concurrency
   ceiling? → `references/capacity-and-contention.md`, then
   `references/runners-and-autoscaling.md`.
3. Setup or dependency restore dominates? →
   `references/typescript-toolchain.md`, `references/caching.md`.
4. Checkout, cache transfer, Docker context, or artifacts dominate? →
   `references/network-and-artifacts.md`.
5. Work unrelated to the change runs anyway? →
   `references/change-based-ci.md`, `references/monorepos.md`.
6. Tests dominate or flake? → `references/testing-and-flakiness.md`,
   `references/integration-environments.md`.
7. Docker/OCI builds dominate? → `references/containers.md`.
8. Security scans dominate? → `references/security-gates.md`.
9. Deployment is slow, repeated, or unverifiable? →
   `references/deployment.md`.
10. Swift/Xcode pipeline? → `references/swift-xcode.md`.
11. Provider mechanics themselves? → `references/github-actions.md`,
    `references/gitlab-ci.md`, `references/circleci.md`,
    `references/buildkite.md`.
12. Build-graph correctness or remote execution? →
    `references/bazel-and-remote-execution.md`.
13. Waiting on a pushed commit, reacting to red, or wiring a watcher? →
    `references/feedback-loops.md`; run `scripts/ci-watch.py` (do not read
    its source — `--help` documents the contract).
14. About to weaken validation, trust boundaries, or artifact identity? →
    `references/effectiveness-contract.md` first.
15. Load-bearing vendor claim unverified or stale? →
    `references/evidence-and-sources.md`.

## Common pitfalls

| Pitfall | Better move |
|---|---|
| Optimizing before measuring | Baseline queue/setup/execution/critical path first. |
| Duplicate `push` and PR runs | PR events for PRs; push only for main/release. |
| Draft PRs start expensive jobs | Cheap planner always; expensive jobs gated on ready-for-review. |
| Caching `node_modules` by default | Cache the package-manager store; measure restore vs install vs registry proxy. |
| Cache key from manifest only | Key on the lockfile too; manifest-only keys serve stale trees. |
| Workflow path filter blocks required checks | Cheap change-detection job conditions expensive jobs; checks always report. |
| Affected detection on shallow clone | Fetch needed history or use event SHAs; on any diff error, run everything. |
| Planner exempts itself | Planner/config/workflow changes route to full validation. |
| Artificial `needs` chains | Start independent lint/typecheck/build together. |
| More shards past the concurrency ceiling | Shards above the ceiling serialize and add setup; merge toward the ceiling. |
| More/bigger runners without queue evidence | Measure per-pool queue p95 and utilization first; bigger classes can queue longer. |
| Watching branch-latest instead of the SHA | Pin the full SHA; supersession is a distinct outcome from failure. |
| Retrying flakes forever | Bound retries, quarantine, assign ownership, track first-time pass rate. |
| Rebuilding deploy artifacts per environment | Build once; promote the same immutable digest. |
| Remote cache writable by untrusted PRs | Read-only PR cache or isolated namespace. |
| Large cache entries with zero hits | Check hit counts; cold entries burn quota and slow every save. |
| A/B timings under different pool load | Interleave experiment runs; record pool state with each sample. |

## Reference files

| File | Read when |
|---|---|
| `references/optimization-workflow.md` | Starting any engagement: the ordered inspect→measure→experiment→verify→report sequence and its stop rules. |
| `references/measurement.md` | Building the baseline, percentiles, critical path, queue vs execution split, or proving a result. |
| `references/effectiveness-contract.md` | Deciding whether a proposed speedup weakens validation, security, or artifact identity. |
| `references/feedback-loops.md` | Waiting on a CI run without blocking or false greens: exact-SHA watching, `scripts/ci-watch.py`, verdicts, reacting to red. |
| `references/capacity-and-contention.md` | Queue delays, concurrency ceilings, pool saturation, merge-vs-split decisions, contention-safe A/B tests. |
| `references/caching.md` | Dependency/build cache design, restore keys, hit-rate economics, poisoning, or transfer cost. |
| `references/change-based-ci.md` | Path filters, affected commands, merge-base correctness, planner safety, full-run fallback. |
| `references/github-actions.md` | GitHub Actions workflows, caches, concurrency, reusable workflows, merge queues, required checks. |
| `references/gitlab-ci.md` | GitLab `needs`, child pipelines, cache/artifacts, interruptible jobs, resource groups, runners. |
| `references/circleci.md` | CircleCI caching, workspaces, test splitting, dynamic config, Docker layer caching, resource classes. |
| `references/buildkite.md` | Buildkite dynamic pipelines, queues, autoscaling, concurrency groups, artifacts, hosted agents. |
| `references/monorepos.md` | Nx, Turborepo, affected graphs, remote caches, distributed execution, task inputs. |
| `references/bazel-and-remote-execution.md` | Bazel, hermetic builds, remote cache/execution, graph-native build adoption. |
| `references/typescript-toolchain.md` | npm/pnpm/Yarn/Bun installs, Corepack, TS project references, `tsbuildinfo`, bundlers. |
| `references/testing-and-flakiness.md` | Sharding, historical timing, retries, flake ownership, coverage merging, rerun interpretation. |
| `references/integration-environments.md` | Testcontainers, service containers, database templates, fixtures, contract tests. |
| `references/containers.md` | BuildKit, multi-stage Dockerfiles, cache mounts/backends, multi-platform, provenance. |
| `references/security-gates.md` | Fast but effective SAST, dependency, secret, container, SBOM, provenance gates. |
| `references/runners-and-autoscaling.md` | Hosted vs self-hosted, ephemeral runners, spot capacity, ARM/x64/macOS, Kubernetes fleets. |
| `references/network-and-artifacts.md` | Checkout depth, sparse/partial clone, LFS, package proxies, artifact compression, registry locality. |
| `references/deployment.md` | Immutable artifacts, build-once-deploy-many, rollout verification, migrations, rollback. |
| `references/swift-xcode.md` | Swift/Xcode builds, SwiftPM, test plans, simulator sharding, macOS runners, DerivedData. |
| `references/evidence-and-sources.md` | Verifying claims, dated source ledger, refreshing stale vendor behavior. |

### Optional: Avrea reference kit

Read only when the repository runs on Avrea (`runs-on:` labels start with
`avrea-`) or Avrea is being evaluated as a runner change. The core loop is
provider-neutral. Probe first: `command -v avr && avr --version &&
avr auth status`.

| File | Read when |
|---|---|
| `references/avrea/cli-evidence.md` | Building an Avrea-backed baseline with `avr`: median/p95, start offsets, queue time, VM metrics, flake and cache-hit counts. |
| `references/avrea/platform-and-runners.md` | Runner labels/sizing, migration, A/B shadowing, observability, SSH debugging, trust boundary. |
| `references/avrea/caching.md` | Avrea cache layers, Docker/Turborepo wiring, registry proxy caveats, quota/eviction, cold entries. |

## Guardrails

- Verify mutable vendor behavior against current official docs when it is
  load-bearing; record the check per `references/evidence-and-sources.md`.
  Version-sensitive pins in examples carry a verify-current note.
- Probe before depending on any platform CLI (`command -v`, `--version`,
  auth status); fall back to provider-native evidence when absent.
- Treat every mutating platform command as an authorization gate (see
  "Analysis is not authorization" above). Confirmation prompts and `--yes`
  flags are mechanics, not permission.
- A green check is evidence only for its exact `head_sha` and artifact
  digest. Stale-SHA greens, wrong-branch greens, and retried-into-green
  flakes are not proof.
- Full validation is the fallback whenever changed files, merge base, cache
  correctness, graph completeness, or security scope cannot be proven.
- Do not add heavy machinery (Bazel, remote execution, self-hosted fleets,
  commercial test selection) unless the measured bottleneck and operating
  capacity justify it.

## Report contract

Complete work reports, in order: baseline (window, sample size, median/p95,
queue vs execution split); the chosen bottleneck with critical-path
evidence; the exact change (files/config); before/after comparison on
matched runs with exact run IDs and `head_sha`; effectiveness checks
(gates, cache trust, artifact identity); cost effect; remaining risks and
rollback; the evidence rung actually reached (config review → syntax check
→ one run → repeated runs → production); disproved or neutral hypotheses;
and any provider branch not exercised. Missing evidence is stated, never
implied away.
