# Evidence and Sources

Use this file when checking whether a CI/CD claim is current, resolving
conflicting guidance, or refreshing this skill.

This skill is only as good as the evidence behind it. CI providers change cache
limits, runner images, CLI behavior, action versions, pricing, and defaults
frequently; a plausible stale claim is worse than silence when it becomes
load-bearing.

## Source hierarchy

1. Current official vendor docs, release notes, API references, and source code.
2. Maintainer-authored issue/forum explanations and official engineering blogs.
3. Reproducible benchmarks with environment, workload, and methodology.
4. Named production case studies with before/after metrics.
5. Community anecdotes and marketing comparisons — leads only, never final evidence.

Record access date.

## Verification rules

- Verify mutable facts before making them load-bearing: action SHAs, runner image
  names, Xcode versions, cache limits, provider pricing, CLI behavior, and beta
  flags.
- Do not quote a benchmark without workload, hardware, run count, and whether it
  was cold or warm.
- Separate confirmed facts from inference.
- If official sources conflict, prefer observed behavior from a controlled run.
- If the repo's current config contradicts generic best practice, measure the
  repo's critical path before changing it.

## Route claims by use case

| Claim type | Primary evidence |
|---|---|
| Runner speed / queue differences | provider timestamps + historical runs on the same class |
| Cache effectiveness | paired cold/warm timing on the same commit |
| Watcher behavior / CLI output shape | provider docs + CLI source code or repeated live probes |
| Flakiness | identical-commit re-run |
| Deployment correctness | exact artifact digest, rollout state, and health checks |
| Change-based safety | graph completeness proof + full-run fallback behavior |

## Refresh checklist

When updating this skill:

1. Re-check official docs for every provider-specific command or limit.
2. Replace stale examples with current stable syntax.
3. Preserve the effectiveness contract unless a control has formally changed.
4. Add new sources with access dates.
5. Re-run structural validation after edits (`scripts/validate-skills.py`).

## Cross-links

- `measurement.md` — for the baseline and evidence rung you can safely claim.
- `feedback-loops.md` — when the mutable fact is CLI watch behavior or run-state semantics.
- `testing-and-flakiness.md` — when the source question is whether a red check is real.
- `effectiveness-contract.md` — when a proposed change is tempting but weakens the proof surface.

## Core source map

| Domain | Primary starting points |
|---|---|
| Metrics | OpenTelemetry CI/CD semantic conventions; DORA; provider analytics |
| GitHub Actions | GitHub Docs on caching, concurrency, larger runners, merge queue, secure use |
| GitLab | GitLab CI YAML, caching, downstream pipelines, resource groups, runner autoscaling |
| CircleCI | CircleCI caching, parallelism/test splitting, workspaces, rerun failed tests |
| Buildkite | Dynamic pipelines, queues, agent management, concurrency, queue metrics |
| Monorepo | Nx affected/cache security/DTE; Turborepo configuration/caching/CI |
| Bazel | Bazel hermeticity, sandboxing, remote caching/execution, Bzlmod |
| TypeScript | npm/pnpm/Yarn/Bun docs, Corepack, TS project references |
| Tests | Playwright/Vitest/Jest docs; provider timing split; Google/Meta/Uber engineering |
| Containers | Docker BuildKit cache, multi-stage, multi-platform, provenance, security |
| Security | SLSA, in-toto, CodeQL, push protection, Semgrep, Trivy |
| Runners | GitHub/GitLab/Buildkite runner docs; Kubernetes scheduling |
| Deployment | Argo Rollouts/CD, Kubernetes probes, immutable-artifact guidance |
| Swift/Xcode | Apple Xcode docs/release notes, Swift compiler performance, Swift library evolution |

## Sources

- GitHub Actions docs: https://docs.github.com/en/actions (accessed 2026-07-28)
- GitLab CI/CD docs: https://docs.gitlab.com/ee/ci/ (accessed 2026-07-28)
- CircleCI docs: https://circleci.com/docs/ (accessed 2026-07-28)
- Buildkite docs: https://buildkite.com/docs (accessed 2026-07-28)
