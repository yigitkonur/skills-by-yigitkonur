# Evidence and Sources

Use this file when checking whether a CI/CD claim is current, resolving conflicting guidance, or refreshing this skill.

## Source hierarchy

1. Current official vendor docs, release notes, API references, and source code.
2. Maintainer-authored issue/forum explanations and official engineering blogs.
3. Reproducible benchmarks with environment, workload, and methodology.
4. Named production case studies with before/after metrics.
5. Community anecdotes and marketing comparisons — leads only, never final evidence.

Record access date. CI providers change cache limits, runner images, action versions, pricing, and defaults frequently.

## Verification rules

- Verify mutable facts before making them load-bearing: action SHAs, runner image names, Xcode versions, cache limits, provider pricing, and beta flags.
- Do not quote a benchmark without workload, hardware, run count, and whether it was cold or warm.
- Separate confirmed facts from inference.
- If official sources conflict, prefer observed behavior from a controlled run.
- If the repo's current config contradicts generic best practice, measure the repo's critical path before changing it.

## Research method used for this skill

Twenty independent research tracks covered: measurement, GitHub Actions, GitLab CI, CircleCI, Buildkite, Bazel, Nx, Turborepo, TypeScript/Node, testing, containers, security gates, Xcode builds, iOS tests, runners, network/artifacts, deployment, integration environments, observability, and change-based orchestration. The comparison corpus also reviewed five existing CI/CD-related skills for structure and anti-patterns.

## Core source map

| Domain | Primary starting points |
|---|---|
| Metrics | OpenTelemetry CI/CD semconv; DORA; provider pipeline analytics |
| GitHub Actions | GitHub Docs caching, concurrency, larger runners, merge queue, secure use |
| GitLab | GitLab CI YAML, caching, downstream pipelines, resource groups, runner autoscaling |
| CircleCI | CircleCI caching, parallelism/test splitting, workspaces, rerun failed tests |
| Buildkite | Dynamic pipelines, queues, agent management, concurrency, queue metrics |
| Monorepo | Nx affected/cache security/DTE; Turborepo configuration/caching/CI |
| Bazel | Bazel hermeticity, sandboxing, remote caching/execution, Bzlmod docs |
| TypeScript | npm/pnpm/Yarn/Bun docs, Corepack, TypeScript project references |
| Tests | Playwright/Vitest/Jest docs; CircleCI timing split; Google/Meta/Uber engineering |
| Containers | Docker BuildKit cache, multi-stage, multi-platform, provenance, security |
| Security | SLSA, in-toto, CodeQL, push protection, Semgrep, Trivy |
| Runners | GitHub/GitLab/Buildkite runner and autoscaling docs; Kubernetes scheduling |
| Deployment | Argo Rollouts/CD, Kubernetes probes, immutable-artifact guidance |
| Swift/Xcode | Apple Xcode docs/release notes, Swift compiler performance, Swift library evolution |

## Refresh checklist

When updating this skill:

1. Re-check official docs for every provider-specific command or limit.
2. Replace stale examples with current stable syntax.
3. Preserve the effectiveness contract unless a control has formally changed.
4. Add new sources with access dates.
5. Re-run trigger and functional tests after edits.
