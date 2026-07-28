# Change-Based CI

Use this file for path filters, affected commands, merge-base correctness, merge queues, and deciding when partial validation is safe.

## The correctness ladder

1. **Compute the changed set** from reliable event SHAs or complete history.
2. **Map changed files to owners/packages/tasks** using a dependency graph or explicit rules.
3. **Include transitive consumers** that can be affected by shared code, schema, lockfile, generated code, CI config, and build config.
4. **Prove the graph is complete** for the defect classes you are skipping.
5. **Run full validation defensively** on merge queue, schedule, release, or uncertainty.

If any step fails, run the full pipeline.

## Analyze before editing YAML

Treat selective CI as a correctness problem before a speed problem:

1. Read the current workflow triggers and branch protection / required checks.
2. Identify the planner/change-detection job, if one exists, and verify whether
   it can route changes to itself and to workflow/config files.
3. Decide which event populations are allowed to skip work at all (PR only,
   never merge queue / release / schedule by default).
4. Freeze the changed-set algorithm and fallback before proposing path-filter
   edits. If a single edge case is uncertain, the fallback is full validation.


## Merge-base rules

- Do not compute merge base from a shallow clone unless the needed history is present.
- Prefer provider event SHAs (`base.sha`, `head.sha`) over branch names when available.
- Rebased forks can move or remove the fork point; detect failure and fall back to full validation.
- Merge queues create a predictive branch; PR-only base/head assumptions may test the wrong change set.
- Lockfile, CI config, dependency graph, generated-code schema, and shared-global changes usually escalate to full validation.
- If the planner script, classifier config, or required-check aggregator changes, that change routes to full validation too.
- Renames need both old and new paths. A rename from `src/core/` to `src/kernel/` can otherwise make the planner think nothing relevant changed.
- On any diff failure (missing history, bad SHAs, provider glitch), fail open to full validation — never to skip.


## Path filters versus graph-aware affected

Path filters are acceptable for flat repos with no shared package consumers. They are dangerous when a shared library affects multiple apps.

Graph-aware affected commands (`nx affected`, Turborepo affected/filter, Bazel reverse dependencies) are better only when:

- package/task graph is complete,
- task inputs include external files that feed generation,
- base and head are correct,
- remote/local cache behavior does not mask skipped work.

Package-level affected detection can miss a file outside package roots that feeds a task. Enable task-input-aware filtering when supported; otherwise add explicit escalation paths.

Graph-aware tools still need a proving set:

- task inputs include generated code, schemas, root config, CI files, and lockfiles;
- planner outputs are fixture-tested against rename, delete, and workflow/config changes;
- a required-check-safe fallback exists when the graph cannot prove completeness;
- the merge queue and release paths still run a full or broader defensive suite.


## Required-check pattern

Do not skip an entire required workflow by a path filter and leave the check pending. Use an always-running change-detection job, then condition expensive jobs:

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      source: ${{ steps.detect.outputs.source }}
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0
      - id: detect
        env:
          BASE: ${{ github.event.pull_request.base.sha || github.event.before }}
          HEAD: ${{ github.sha }}
        run: |
          if ! files=$(git diff --name-only "$BASE...$HEAD"); then
            echo "diff failed; failing open to full validation" >&2
            echo source=true >> "$GITHUB_OUTPUT"
          elif grep -qE '^(src|packages|package.json|pnpm-lock.yaml)' <<<"$files"; then
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

The detector must define every variable it uses. A broken example such as:

```bash
git diff --name-only "$BASE...$HEAD"
```

without proving where `BASE` and `HEAD` come from can silently diff the
wrong range or nothing at all. Prefer explicit provider event SHAs, and on
any uncertainty run the full path.


## Full-run triggers

Always run the full suite when:

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
