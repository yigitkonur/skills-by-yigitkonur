# GitLab CI

Use this file when the measured bottleneck lives in `.gitlab-ci.yml` or GitLab runner behavior.

## High-value levers

| Bottleneck | GitLab lever | Guardrail |
|---|---|---|
| Stage barriers serialize work | `needs` DAG | Artifact access follows `needs`; avoid cycles. |
| Repeated dependency work | cache keyed by lockfile | Cache dependencies, artifact outputs. |
| Superseded commits waste time | `interruptible` + workflow auto-cancel | Keep deploys non-interruptible. |
| Deployment races | `resource_group` | Prefer `newest_ready_first` for idempotent deploys. |
| Monorepo fan-out | dynamic child pipelines | Bound nesting and make parent wait with `strategy: depend`. |
| Unrelated jobs | `rules:changes` | Set a correct `compare_to`; fall back to full run. |
| Slow tests | `parallel` / `parallel:matrix` | Split once; merge JUnit/coverage; cap setup duplication. |
| Queue time | autoscaled runners | Keep runner manager persistent; warm capacity for critical paths. |

## Cache versus artifacts

Use cache for reusable dependency state:

```yaml
cache:
  key:
    files:
      - pnpm-lock.yaml
  paths:
    - .pnpm-store
  policy: pull-push
```

Use artifacts for outputs another job needs:

```yaml
artifacts:
  paths:
    - dist/
  expire_in: 1 day
```

Keep protected and unprotected cache scopes separate. Use `policy: pull` for jobs that should consume but not update a cache.

## DAG example

```yaml
build:
  script: corepack pnpm run build
  artifacts:
    paths: [dist/]

typecheck:
  needs: []
  script: corepack pnpm exec tsc -b --pretty false

test:
  needs: [build]
  script: corepack pnpm test -- --run
```

`needs: []` starts immediately; `needs: [build]` starts as soon as build finishes. Do not mix legacy `dependencies` with `needs` casually.

## Interruptible and deployments

```yaml
workflow:
  auto_cancel:
    on_new_commit: interruptible

default:
  interruptible: true

deploy-production:
  interruptible: false
  resource_group: production
  environment:
    name: production
  script: ./deploy.sh production
```

Avoid parent/child resource deadlocks: do not hold a resource in a parent trigger and reacquire the same group in the child.

## Change rules

```yaml
test:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        paths:
          - src/**/*.ts
          - packages/**/*.ts
          - pnpm-lock.yaml
        compare_to: refs/heads/main
  script: corepack pnpm test -- --run
```

For branch pipelines, verify the comparison reference explicitly. Unknown or missing history means full validation.

## Sources

- GitLab CI YAML: https://docs.gitlab.com/ci/yaml/ (accessed 2026-07-28)
- Caching: https://docs.gitlab.com/ci/caching/ (accessed 2026-07-28)
- Downstream pipelines: https://docs.gitlab.com/ci/pipelines/downstream_pipelines/ (accessed 2026-07-28)
- Resource groups: https://docs.gitlab.com/ci/resource_groups/ (accessed 2026-07-28)
- Job rules: https://docs.gitlab.com/ci/jobs/job_rules/ (accessed 2026-07-28)
- Runner autoscaling: https://docs.gitlab.com/runner/runner_autoscale/ (accessed 2026-07-28)
