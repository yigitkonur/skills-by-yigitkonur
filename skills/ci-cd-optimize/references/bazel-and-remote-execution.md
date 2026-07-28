# Bazel and Remote Execution

Use this file when evaluating Bazel-style action graphs, remote cache, or remote execution. Bazel is an architecture decision, not a cache plugin.

## When Bazel is justified

Use Bazel when most gates are true:

- polyglot repo or generated code shared across languages,
- many fine-grained actions with high fan-out,
- team can declare all inputs, outputs, tools, and toolchains,
- sandboxed/hermetic enforcement is acceptable,
- someone owns Bazel upgrades, rulesets, cache policy, and worker fleets,
- warm-build p50/p95 beats the incumbent enough to pay migration cost.

A TypeScript-only small or medium monorepo usually gets most of the benefit from Nx/Turborepo with far less operational complexity.

## Core model

- Target graph: declared packages/targets and dependencies.
- Action graph: concrete commands, inputs, and outputs.
- Action cache: action hash to result metadata.
- Content-addressable store: output digest to bytes.
- Remote execution: trusted workers execute actions and can make shared cache entries more trustworthy.

Cache correctness depends on hermeticity. An action that reads an undeclared file can produce an incorrect cache hit that looks like a speedup.

## Security rules

- Sandbox actions; do not rely on conventions.
- Pin external archives and toolchains by integrity hash.
- Restrict writes to trusted action-cache entries; PRs should not upload local results to the protected cache.
- Treat remote workers and cache as powerful, not VM boundaries.
- Keep release artifact production on trusted runners and verify provenance/digests.

## TypeScript notes

- Use current Bzlmod-based `rules_js` and `rules_ts` guidance; do not copy WORKSPACE-era examples.
- Prefer `ts_project` with a fast transpiler for emit and `tsc` for type checking when appropriate.
- Avoid persistent-worker modes that current ruleset docs mark as correctness-risky.
- Generate BUILD files where possible; hand-maintained graphs drift.

## Decision experiment

Run a bounded spike on one subgraph:

1. Choose ~10 packages with representative dependencies.
2. Build with Bazel, sandboxing, and a remote cache.
3. Measure cold, warm, affected, and cache-hit p50/p95 against the incumbent on the same runner.
4. Include migration/ownership cost and failure modes.
5. Adopt only if warm CI improves materially and the team can enforce hermeticity.

## Sources

- Bazel glossary: https://bazel.build/reference/glossary (accessed 2026-07-28)
- Skyframe: https://bazel.build/reference/skyframe (accessed 2026-07-28)
- Hermeticity: https://bazel.build/basics/hermeticity (accessed 2026-07-28)
- Sandboxing: https://bazel.build/docs/sandboxing (accessed 2026-07-28)
- Remote caching: https://bazel.build/remote/caching (accessed 2026-07-28)
- Remote execution: https://bazel.build/remote/rbe (accessed 2026-07-28)
- Bazel build security: https://www.systemshardening.com/articles/cicd/bazel-build-security/ (accessed 2026-07-28)
