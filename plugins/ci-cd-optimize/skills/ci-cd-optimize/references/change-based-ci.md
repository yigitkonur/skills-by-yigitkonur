# Change-Based CI

Use this file for path filters, affected commands, merge-base correctness, merge queues, and deciding when partial validation is safe.

## The correctness ladder

1. **Compute the changed set** from reliable event SHAs or complete history.
2. **Map changed files to owners/packages/tasks** using a dependency graph or explicit rules.
3. **Include transitive consumers** that can be affected by shared code, schema, lockfile, generated code, CI config, and build config.
4. **Prove the graph is complete** for the defect classes you are skipping.
5. **Run full validation defensively** on merge queue, schedule, release, or uncertainty.

If any step fails, run the full pipeline.

## Merge-base rules

- Do not compute merge base from a shallow clone unless the needed history is present.
- Prefer provider event SHAs (`base.sha`, `head.sha`) over branch names when available.
- Rebased forks can move or remove the fork point; detect failure and fall back to full validation.
- Merge queues create a predictive branch; PR-only base/head assumptions may test the wrong change set.
- Lockfile, CI config, dependency graph, generated-code schema, and shared-global changes usually escalate to full validation.

## Path filters versus graph-aware affected

Path filters are acceptable for flat repos with no shared package consumers. They are dangerous when a shared library affects multiple apps.

Graph-aware affected commands (`nx affected`, Turborepo affected/filter, Bazel reverse dependencies) are better only when:

- package/task graph is complete,
- task inputs include external files that feed generation,
- base and head are correct,
- remote/local cache behavior does not mask skipped work.

Package-level affected detection can miss a file outside package roots that feeds a task. Enable task-input-aware filtering when supported; otherwise add explicit escalation paths.

## Required-check pattern

Do not skip an entire required workflow by a path filter and leave the check pending. Use an always-running change-detection job, then condition expensive jobs:

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      source: ${{ steps.detect.outputs.source }}
    steps:
      - uses: actions/checkout@v5
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

Ensure the provider reports skipped downstream jobs as successful/skipped in the way branch protection expects.

## Planner self-routing and rename traps

The component that decides what runs is part of the repository too. Treat it as
load-bearing code, not as harmless glue.

Two easy ways change-based CI lies to you:

1. **Self-routing planner.** A planner change that routes only to its own lane is
   grading its own homework. Changes to CI config, planner code, workflow files,
   or shared routing tables should usually escalate broadly rather than proving
   only themselves.
2. **Rename masking.** A move from `src/x.ts` to `docs/x.md` can look
   documentation-only if you only inspect the destination path. When the source
   path was executable code, the pipeline must still treat the change as code.
   Prefer `--name-status` or disable rename detection when classifying if your
   tool would otherwise hide the removal.

Keep tiny fixture-style tests for the classifier itself. A routing bug is one of
few CI defects that can silently ship without any red lane at all.

- merge base is missing or suspicious,
- lockfile or package-manager config changed,
- CI/workflow/task-graph config changed,
- generated-code schema or generator changed,
- shared global tsconfig/build config changed,
- release, merge queue, nightly, or scheduled defensive run,
- previous partial run escaped a defect.

## Sources

- Nx affected: https://nx.dev/docs/features/ci-features/affected (accessed 2026-07-28)
- Turborepo run/affected: https://turborepo.dev/docs/reference/run (accessed 2026-07-28)
- GitHub merge queue: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue (accessed 2026-07-28)
- Bazel query: https://bazel.build/query/language (accessed 2026-07-28)
- Shallow merge-base behavior: https://hoelz.ro/blog/the-case-of-the-moving-merge-base (accessed 2026-07-28)
