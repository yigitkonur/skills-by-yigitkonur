# CircleCI

Use this file when the measured bottleneck lives in CircleCI config.

## High-value levers

| Bottleneck | CircleCI lever | Guardrail |
|---|---|---|
| Dependency install | cache package-manager download store | Do not cache `node_modules` by default. |
| Tests | `circleci tests run --split-by=timings` | Requires reliable JUnit timing metadata. |
| Too many executors | tune `parallelism` | Stop when repeated setup exceeds split savings. |
| Job handoff | workspaces | Persist only targeted outputs such as `dist/`. |
| Unrelated workflow branches | dynamic config/continuation | One continuation; generator must fail visibly. |
| Docker builds | Docker layer caching | Use only for stable layers; it has a per-job cost. |
| Flaky reruns | rerun failed tests | Diagnostic relief, not flake ownership. |

## Cache pattern

```yaml
- restore_cache:
    keys:
      - v1-pnpm-{{ .Branch }}-{{ checksum "pnpm-lock.yaml" }}
      - v1-pnpm-{{ .Branch }}-
      - v1-pnpm-
- run: corepack pnpm install --frozen-lockfile
- save_cache:
    key: v1-pnpm-{{ .Branch }}-{{ checksum "pnpm-lock.yaml" }}
    paths:
      - ~/.local/share/pnpm/store
```

Avoid rotating keys (`epoch`, build number), broad runtime-crossing fallbacks, and multiple parallel jobs racing to write the same immutable cache. Have one producer write and consumers restore.

## Timing-based Jest split

```yaml
jobs:
  test:
    docker:
      - image: cimg/node:24.16.0
    parallelism: 4
    resource_class: large
    steps:
      - checkout
      - run: corepack pnpm install --frozen-lockfile
      - run:
          command: |
            npx jest --listTests | circleci tests run \
              --command="JEST_JUNIT_ADD_FILE_ATTRIBUTE=true xargs npx jest --runInBand --" \
              --split-by=timings
          environment:
            JEST_JUNIT_OUTPUT_DIR: ./reports
      - store_test_results:
          path: ./reports
```

Timing quality depends on uploaded JUnit files and correct file/class/name attributes. A rerun-failed-tests flow may lose timing data for tests that passed in the original run; preserve results so future splits rebalance.

## Workspaces

Workspaces transfer data within one workflow run. They are not cross-run caches.

```yaml
- persist_to_workspace:
    root: .
    paths:
      - dist/
```

Persisting the whole working directory creates expensive archive/upload/download cycles and can be slower than restoring a cache.

## Sources

- Caching: https://circleci.com/docs/guides/optimize/caching/ (accessed 2026-07-28)
- Parallelism and test splitting: https://circleci.com/docs/guides/optimize/parallelism-faster-jobs/ (accessed 2026-07-28)
- Workspaces: https://circleci.com/docs/guides/orchestrate/workspaces/ (accessed 2026-07-28)
- Rerun failed tests: https://circleci.com/docs/guides/test/rerun-failed-tests/ (accessed 2026-07-28)
- Dynamic configuration: https://circleci.com/docs/guides/orchestrate/using-dynamic-configuration/ (accessed 2026-07-28)
