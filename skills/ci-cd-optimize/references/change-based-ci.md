# Change-Based CI

Use this file for path filters, affected commands, merge-base correctness, merge
queues, and deciding when partial validation is safe.

This file answers a stricter question than “can we skip work?” It answers “what
must be true before skipping work is still honest?” If any step below cannot be
proved, run the full pipeline.

## The correctness ladder

1. **Compute the changed set** from reliable event SHAs or complete history.
2. **Map changed files to owners/packages/tasks** using a dependency graph or explicit rules.
3. **Include transitive consumers** that can be affected by shared code, schema,
   lockfile, generated code, CI config, and build config.
4. **Prove the graph is complete** for the defect classes you are skipping.
5. **Escalate to a full run** on merge queue, release, schedule, uncertainty, or
   any change to the planner itself.

If any step fails, the correct answer is the full pipeline.

## Merge-base rules

- Do not compute merge base from a shallow clone unless the needed history is present.
- Prefer provider event SHAs (`base.sha`, `head.sha`) over branch names when available.
- Rebased forks can move or remove the fork point; detect failure and fall back to full validation.
- Merge queues create a predictive branch; PR-only base/head assumptions may test the wrong change set.
- Lockfile, CI config, dependency graph, generated-code schema, and shared-global changes usually escalate to full validation.

## The planner must not route itself narrowly

The component that decides what runs is part of the repository. If a change to
that logic routes only the lanes it already knows how to name, a routing bug can
ship having validated a fraction of the repo.

Two failures worth guarding against explicitly:

1. **Config fan-out gaps.** A rule mapping `.github/**` to “the main lanes” silently
   excludes specialized ones, so editing a specialized workflow never exercises it.
2. **Self-routing.** A planner change that maps only to its own directory's lane
   grades its own homework.

Guard both with unit fixtures over the classifier when possible — it is usually a
pure path-to-lane function and costs milliseconds to test.

## Path filters versus graph-aware affected

Path filters are acceptable for flat repos with no shared package consumers. They
are dangerous when a shared library affects multiple apps.

Graph-aware affected commands (`nx affected`, Turborepo filters, Bazel reverse
queries) are better only when:

- the package/task graph is complete,
- task inputs include external files that feed generation,
- base and head are correct,
- remote/local cache behavior does not mask skipped work.

Package-level affected detection can miss a file outside package roots that feeds
a task. Enable task-input-aware filtering when supported; otherwise add explicit
escalation paths.

## Rename and non-code edge cases

Two subtle misses recur in real repos:

- **Rename drift.** `git diff --name-only` prints only the destination path when
  rename detection is on. Moving `src/x.ts` to `docs/x.md` can therefore read as a
  docs-only change while executable source was removed. Use `--no-renames`, or
  parse `--name-status` and route both paths.
- **Generated inputs outside the package root.** A package-level planner may miss a
  schema, template, or CI helper outside its tree that still changes its build.

These are reasons to escalate, not special cases to wave through.

## Required-check pattern

Do not skip an entire required workflow by a path filter and leave the check
pending. Use an always-running change-detection job, then condition expensive
jobs:

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      source: ${{ steps.detect.outputs.source }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - id: detect
        run: |
          if git diff --name-only "$BASE...$HEAD" | grep -qE '^(src|packages|package.json|pnpm-lock.yaml)'; then
            echo source=true >> "$GITHUB_OUTPUT"
          else
            echo source=false >> "$GITHUB_OUTPUT"
          fi

  test:
    needs: changes
    if: needs.changes.outputs.source == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: corepack pnpm test -- --run
```

Ensure the provider reports skipped downstream jobs as successful/skipped in the
way branch protection expects.

## Full-run triggers

Always run the full suite when:

- merge base is missing or suspicious,
- lockfile or package-manager config changed,
- CI/workflow/task-graph config changed,
- generated-code schema or generator changed,
- shared global tsconfig/build config changed,
- release, merge queue, nightly, or scheduled defensive run,
- a previous partial run escaped a defect,
- the planner itself changed.

## Cross-links

- `measurement.md` — how to baseline a partial-vs-full comparison honestly.
- `caching.md` — when a remote cache can hide skipped work instead of saving it.
- `effectiveness-contract.md` — why uncertainty here always resolves to a full run.
- `feedback-loops.md` — the `no-run` verdict and how a watcher should report a path-filtered commit.
- `monorepos.md` — when the graph and the planner are the optimization surface.

## Sources

- Nx affected: https://nx.dev/docs/features/ci-features/affected (accessed 2026-07-28)
- Turborepo run/affected: https://turborepo.dev/docs/reference/run (accessed 2026-07-28)
- GitHub merge queue: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue (accessed 2026-07-28)
- Bazel query: https://bazel.build/query/language (accessed 2026-07-28)
- Shallow merge-base behavior: https://hoelz.ro/blog/the-case-of-the-moving-merge-base (accessed 2026-07-28)
