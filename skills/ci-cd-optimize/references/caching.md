# Caching

Use this file for dependency, build, compiler, Docker, and remote-cache decisions. The goal is saved wall-clock time with correct invalidation—not a high hit-rate vanity metric.

## Cache design checklist

A cache entry is safe only when its key includes every input that changes its output:

- source content and relevant config,
- lockfile or resolved dependency graph,
- OS and CPU architecture,
- runtime/compiler and package-manager versions,
- environment variables that affect output,
- generator/schema versions for generated code,
- cache namespace/version so you can intentionally invalidate it.

If any input is missing, a hit can be silently wrong. If any irrelevant input is included, hits collapse.

## Trust boundaries

- Untrusted PRs must not write cache entries that protected branches later consume as trusted.
- Prefer read-only PR cache access or isolated PR namespaces with protected-branch promotion.
- Sign or verify artifacts where the backend supports integrity checks; signatures do not replace authorization.
- Do not put secrets in cache keys or cached files.

## TypeScript package caches

Cache the package-manager store/cache, not blindly `node_modules`:

| Manager | CI command | Cache target |
|---|---|---|
| npm | `npm ci` | npm cache, usually via setup action or `~/.npm` |
| pnpm | `pnpm install --frozen-lockfile` | pnpm store |
| Yarn modern | `yarn install --immutable` | Yarn global cache or committed Zero-Install cache |
| Bun | `bun ci` | Bun install cache |

Key by lockfile, Node version, package-manager version, OS, and architecture. Compare restore time with a clean install; large stores can be slower than a registry fetch on a nearby network.

**Manifest-only keys are a correctness bug, not just a staleness bug.** A key built from `package.json` alone keeps serving the old dependency tree after the lockfile changes; CI can stay green on dependencies that no longer install locally. Any key covering a dependency tree includes the lockfile. The inverse bites only without frozen installs: a lockfile-only key can restore a tree that predates a manifest-only change, but `npm ci`/`--frozen-lockfile` fails loudly on a manifest/lockfile desync — so lockfile-only keys are safe under the frozen installs this file already mandates. If an install is not frozen, include the manifest too (`hashFiles('pnpm-lock.yaml', 'package.json')`).

## Prove the cache earns its keep

Measure three timings before keeping or adding a dependency cache:

1. **Cold**: clean run with no cache (delete/miss the entry deliberately once, in an authorized experiment).
2. **Warm**: restore + post-hit work (install against the restored store) + save/upload at the end.
3. **Proxy-only**: plain install when the CI platform fronts the registry with a local proxy/mirror — on such platforms a store cache is often redundant and pure overhead.

Keep the cache only if warm beats both alternatives on the critical path. Count the save step: a cache that restores in 40s, saves in 35s, and saves 60s of install is a net loss. Check entry hit counts and last-access where the platform exposes them (`avr cache list` on Avrea; provider UIs elsewhere): large entries with zero or near-zero hits burn quota, slow every save, and should be removed — removal is a shared-state mutation, so gate it.

**Write strategy**: let the default/protected branch produce cache entries and branches consume them (read-on-branch/write-on-default). This keeps untrusted writes out and stops N parallel PRs from racing to save N copies of the same store.

**Default-branch cold starts after a key change are normal.** Branch-scoped
caches cannot seed the default branch, so the first default-branch run
after a key change (schema bump, added OS/arch/toolchain identity, changed
restore paths) is legitimately cold even though the branch runs that
validated the change ran warm. Read that run's own restore-log sequence
(`Cache not found for input keys:` → `Cache saved`, then `Cache restored`
on the next run) before calling it a regression.

## Restore-key discipline

Use narrow restore keys from most-specific to less-specific:

```yaml
key: linux-x64-node24-pnpm10-${{ hashFiles('pnpm-lock.yaml') }}
restore-keys: |
  linux-x64-node24-pnpm10-
```

Avoid keys that rotate every run (`epoch`, build number) and broad fallbacks that restore a different runtime, branch dependency set, or architecture.

## Build/compiler caches

- TypeScript `.tsbuildinfo` and emitted outputs must be keyed with TypeScript version, lockfile, and every relevant `tsconfig`.
- Generated code must hash schemas, generator version, and config.
- Xcode DerivedData requires exact project/toolchain keys and timestamp restoration.
- BuildKit layer caches require external backends on ephemeral runners; cache mounts do not automatically persist across runners.

## Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Passes on miss, fails on hit | Missing output or undeclared input | Complete inputs/outputs; invalidate namespace. |
| Zero exact hits | Key rotates every run | Remove build IDs/timestamps from key. |
| Slow despite hit | Transfer exceeds recomputation | Cache smaller store, nearby backend, or stop caching. |
| Cross-branch stale behavior | Fallback too broad or shared trust scope | Narrow key; separate protected/untrusted scopes. |
| Poisoned shared cache | Untrusted writes accepted | Read-only PR access or isolated namespace. |

## Sources

- GitHub dependency caching: https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching (accessed 2026-07-28)
- pnpm CI: https://pnpm.io/continuous-integration (accessed 2026-07-28)
- Turborepo caching: https://turbo.build/repo/docs/crafting-your-repository/caching (accessed 2026-07-28)
- Nx cache security: https://nx.dev/docs/kb/cache-security (accessed 2026-07-28)
- Bazel remote caching: https://bazel.build/remote/caching (accessed 2026-07-28)
