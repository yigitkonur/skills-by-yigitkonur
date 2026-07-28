# Caching

Use this file for dependency, build, compiler, Docker, and remote-cache
decisions. The goal is saved wall-clock time with correct invalidation — not a
high hit-rate vanity metric.

If the cache debate starts from “installs are slow”, read
`measurement.md` first and time the uncached path before adding anything.

## Cache design checklist

A cache entry is safe only when its key includes every input that changes its
output:

- source content and relevant config,
- lockfile or resolved dependency graph,
- OS and CPU architecture,
- runtime/compiler and package-manager versions,
- environment variables that affect output,
- generator/schema versions for generated code,
- cache namespace/version so you can intentionally invalidate it.

If any input is missing, a hit can be silently wrong. If any irrelevant input is
included, hits collapse.

## Trust boundaries

- Untrusted PRs must not write cache entries that protected branches later
  consume as trusted.
- Prefer read-only PR cache access or isolated PR namespaces with protected-branch
  promotion.
- Sign or verify artifacts where the backend supports integrity checks; signatures
  do not replace authorization.
- Do not put secrets in cache keys or cached files.

Read `effectiveness-contract.md` before recommending a shared namespace or a
trusted-branch restore key.

## Time the uncached path first

“Installs are slow” is an assumption until measured. On some fleets the package
registry is already proxied locally, so adding a dependency-store cache on top of
it buys nothing and may add a save step.

The safe generalization is narrow but useful:

- when the uncached step is already seconds, measure it before caching;
- when the cold path is materially slower than the warm path, the cache may be earning its keep;
- when restore + post-hit work exceeds a clean run, delete the cache.

This is why the headline metric is **cache saved time**, not hit rate. A 100% hit
rate on a cache that saves nothing is wasted bytes.

## TypeScript and package-manager caches

Cache the package-manager store/cache, not blindly `node_modules`:

| Manager | CI command | Cache target |
|---|---|---|
| npm | `npm ci` | npm cache (`~/.npm` or setup action cache) |
| pnpm | `pnpm install --frozen-lockfile` | pnpm store |
| Yarn modern | `yarn install --immutable` | Yarn global cache or committed Zero-Install cache |
| Bun | `bun ci` | Bun install cache |

Key by:

- lockfile,
- runtime version,
- package-manager version,
- OS,
- architecture,
- and for monorepos, any manifest/config whose drift changes the dependency tree.

### Default-branch cold starts are normal

Branch-scoped caches cannot seed the default branch. After a cache-key change (a
schema bump, adding OS/arch/toolchain identity, changing restore paths), the
first default-branch run is legitimately cold even though the branch runs that
validated the change were warm. Verify with the run's own log lines before
calling it a regression.

## Restore-key discipline

Use narrow restore keys from most-specific to less-specific:

```yaml
key: linux-x64-node24-pnpm10-${{ hashFiles('pnpm-lock.yaml', 'package.json') }}
restore-keys: |
  linux-x64-node24-pnpm10-
```

Avoid keys that rotate every run (`epoch`, build number) and broad fallbacks that
restore a different runtime, branch dependency set, or architecture.

Keying a dependency cache on the lockfile **alone** can still be stale after a
manifest-only change if the manifest influences the resolved tree without a lock
rewrite. Manifest + lockfile is the safer default.

## Build, compiler, and remote caches

- TypeScript `.tsbuildinfo` and emitted outputs must be keyed with TypeScript
  version, lockfile, and every relevant `tsconfig`.
- Generated code must hash schemas, generator version, and config.
- Xcode DerivedData requires exact project/toolchain keys and timestamp-safe
  restoration.
- BuildKit layer caches require external backends on ephemeral runners; cache
  mounts do not automatically persist across runners.
- Remote task caches (Nx, Turborepo, Bazel) must prove their input graph is
  complete; otherwise a hit can be wrong, not merely stale. Cross-link:
  `change-based-ci.md`, `bazel-and-remote-execution.md`, and `monorepos.md`.

## Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Passes on miss, fails on hit | Missing output or undeclared input | Complete inputs/outputs; invalidate namespace. |
| Zero exact hits | Key rotates every run | Remove build IDs/timestamps from the key. |
| Slow despite hit | Transfer exceeds recomputation | Cache a smaller store, use a nearer backend, or stop caching. |
| Cross-branch stale behavior | Fallback too broad or shared trust scope | Narrow the key; separate protected/untrusted scopes. |
| Poisoned shared cache | Untrusted writes accepted | Read-only PR access or isolated namespace. |
| First default-branch run unexpectedly cold | Branch caches cannot seed default branch | Expect one cold run after a key change; verify from log lines. |

## Cross-links

- `measurement.md` — how to tell whether the cache saved real wall-clock time.
- `change-based-ci.md` — when a partial run plus remote cache can mask skipped work.
- `network-and-artifacts.md` — when transfer cost, not invalidation, is the problem.
- `containers.md` — Docker layer cache and BuildKit specifics.
- `effectiveness-contract.md` — before sharing a cache across trust boundaries.
- `monorepos.md` and `bazel-and-remote-execution.md` — when cache correctness depends on graph completeness.

## Sources

- GitHub dependency caching: https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching (accessed 2026-07-28)
- pnpm CI: https://pnpm.io/continuous-integration (accessed 2026-07-28)
- Turborepo caching: https://turbo.build/repo/docs/crafting-your-repository/caching (accessed 2026-07-28)
- Nx cache security: https://nx.dev/docs/kb/cache-security (accessed 2026-07-28)
- Bazel remote caching: https://bazel.build/remote/caching (accessed 2026-07-28)
