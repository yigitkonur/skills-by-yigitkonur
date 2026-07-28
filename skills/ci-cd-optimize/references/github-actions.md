# GitHub Actions

Use this file when the measured bottleneck lives in a GitHub Actions workflow.

## High-value levers

| Bottleneck | First checks | Typical fix |
|---|---|---|
| Duplicate runs | `push` plus `pull_request` triggers | PR validation on PR events; main/release validation on push. |
| Noisy event activity | PR edit/label/assignee triggers | Restrict `types` to code-changing/review-ready activity. |
| Draft PR cost | expensive jobs on draft PRs | Keep a cheap planner; gate heavy jobs until `ready_for_review`. |
| Repeated setup | setup-node cache, install duration, cache hit output | Cache package-manager store by lockfile/runtime. |
| Stale PR runs | concurrency settings | Cancel superseded PR runs; never cancel deployments. |
| Unrelated work | workflow/job conditions | Always-running change detection plus job-level conditions. |
| Artificial serial DAG | `needs` between independent jobs | Start independent lint/typecheck/build together. |
| Long test job | per-file/test timings, CPU | Matrix shards by timing; split once, merge reports. |
| Checkout cost | duration, repo size, history need | No checkout if unused; shallow/partial/sparse by job need. |
| Artifact transfer | upload/download duration, sizes | Current artifact actions, targeted paths, correct compression. |
| Queue p95 | run wait time, runner class | Right-size or scale only after queue/utilization evidence. |
| Required check pending | branch protection + skipped workflow | Replace workflow-level path skip with job conditions. |
| Docs edits still build | `paths-ignore` uses `*.md` | `*.md` matches ROOT level only — add `docs/**` and `**/*.md`. |
| Merge queue wrong/no run | triggers | Add `merge_group`; verify affected semantics. |

## Path filter globbing

GitHub's `paths`/`paths-ignore` patterns are not shell globs and not fully gitignore
semantics. The trap that costs the most: **`*.md` matches root-level files only.** A repo
that ignores `*.md` still runs the full pipeline for `docs/guide.md`.

```yaml
paths-ignore:
  - '*.md'          # root README.md only
  - '**/*.md'       # every markdown file, any depth   <- what you meant
  - 'docs/**'       # whole directory regardless of extension
```

Verify rather than assume — push a docs-only commit and check that zero runs registered:

```bash
gh run list --commit "$(git rev-parse HEAD)" --json databaseId --jq 'length'   # expect 0
```

Observed cost of getting this wrong: a markdown-only commit triggered a full CI **and a
production deploy** because the new guide lived at `docs/CI-CD.md` while the filter said
`*.md`. Keep `paths-ignore` identical across `push` and `pull_request`, or the two events
disagree about what is worth building.

## Security defaults

- Set top-level `permissions: contents: read` or `{}` and elevate per job.
- Pin third-party actions to a reviewed commit SHA with a version comment; verify the current SHA when authoring.
- Do not expose secrets to untrusted fork jobs; use OIDC instead of long-lived cloud credentials.
- Do not use persistent self-hosted runners for untrusted public PR code.
- Keep `cancel-in-progress: false` for deployment concurrency groups.

## TypeScript-oriented shape

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
    branches: [main]
  push:
    branches: [main, 'release/**']
  merge_group:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

permissions:
  contents: read

jobs:
  verify:
    if: github.event_name != 'pull_request' || github.event.pull_request.draft == false
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

This avoids the common `push` + `pull_request` duplicate: feature work validates through the PR; main and release branches validate after merge.

## Job graph and matrix guidance

- Use job-level `if` to avoid runner allocation; step-level `if` still pays checkout/setup before skipping.
- Remove artificial `needs` edges. Lint, typecheck, and independent builds can start together; keep a cheap high-signal gate before genuinely expensive suites only when failed-run waste matters.
- Generate matrices from a change plan instead of running a full Cartesian matrix per PR. Use PR/main/nightly/release coverage tiers.
- Use `fail-fast: false` when every shard's result is diagnostically valuable.
- Use `fail-fast: true` when early feedback or failed-run cost matters more than full matrix signal.
- Cap `max-parallel` when registry, artifact, database, or runner capacity is saturated.
- Do not multiply runners until test time is split; otherwise every shard repeats setup and full tests.
- Put tiny planner/status jobs on lightweight runners where the provider offers them; keep build/test jobs on build runners.

## Same-job parallelism (verify before use)

GitHub's 2026-06-25 changelog announced same-job step concurrency with `background: true` and related `parallel`/`wait`/`wait-all`/`cancel` keywords, but the stable workflow-syntax page fetched on 2026-07-28 still says steps execute in order and does not document those keys. Treat this as provider-version-gated: verify the current official syntax docs before emitting it. Prefer job-level parallelism for CPU-bound work and same-job concurrency only for I/O-bound tasks that share setup.

## Checkout guidance

- Omit checkout for jobs that only call an API, promote a digest, or download artifacts.
- Keep `fetch-depth: 1` unless history is required.
- Use `fetch-tags: true` for tag-dependent versioning without full history.
- Use `filter: blob:none` for metadata-heavy analysis; it overrides `sparse-checkout`.
- Use `sparse-checkout` for a package slice; disable LFS/submodules unless required.

## Cache notes

- `actions/setup-node` caches package-manager caches, not `node_modules`.
- Manual caches must include OS, architecture, runtime, package-manager version, and lockfile.
- Use exact `cache-hit` and restore/save timings to calculate break-even; `lookup-only: true` checks existence without download when a branch decision needs it.
- Let one canonical successful job save a shared cache family; make matrix consumers restore-only to avoid upload stampedes.
- Cache scope and eviction behavior change over time; verify current limits when they are load-bearing.

## Sources

- Dependency caching: https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching (accessed 2026-07-28)
- Concurrency: https://docs.github.com/enterprise-cloud@latest/actions/using-jobs/using-concurrency (accessed 2026-07-28)
- Larger runners: https://docs.github.com/actions/using-github-hosted-runners/about-larger-runners/about-larger-runners (accessed 2026-07-28)
- actions/checkout: https://github.com/actions/checkout (accessed 2026-07-28)
- actions/cache: https://github.com/actions/cache (accessed 2026-07-28)
- actions/upload-artifact: https://github.com/actions/upload-artifact (accessed 2026-07-28)
- actions/download-artifact: https://github.com/actions/download-artifact (accessed 2026-07-28)
- Same-job step concurrency announcement: https://github.blog/changelog/2026-06-25-actions-steps-can-now-be-run-in-parallel/ (accessed 2026-07-28; stable syntax verification required)
- Merge queue: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue (accessed 2026-07-28)
- Secure use: https://docs.github.com/en/actions/reference/security/secure-use (accessed 2026-07-28)
