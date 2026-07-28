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

## Package proxy versus store cache

A fast install does not prove the local package-manager store is helping. On
runner platforms with a colocated registry proxy, a "cold" install can still be
LAN-fast because the proxy, not the local store, is doing the work.

Use this break-even test before keeping a large dependency-store cache:

1. Compare a true cold run against a warm run on the same lockfile.
2. Measure **install time**, not just cache hit counts.
3. Compare that with the restore/save/archive cost of the store cache itself.

If the install time is essentially unchanged cold and warm, the local store
archive may only be moving bytes around. Remove it and keep the proxy.

## Manifest-only changes are not safe on lockfile keys alone

For package-tree caches, key on the manifest **and** the lockfile. A
manifest-only change can still change what should be installed or tested even
when the lockfile stays constant. A cache keyed only on the lockfile can then
restore a stale dependency tree and make the run look green for the wrong input
set.

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
