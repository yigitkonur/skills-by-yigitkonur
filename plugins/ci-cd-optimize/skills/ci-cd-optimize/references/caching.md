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

Where the platform already runs a pull-through registry proxy on the runner network, a store cache can be redundant: packages come from colocated storage either way, so the cache pays restore and save to avoid a fetch that was never slow. Test directly — compare the install step on a cache-miss run against a warm one; roughly equal means the proxy is doing the work. Do not infer from hit counts alone: a cache can report a high hit rate while saving nothing. Report the numbers when removing a cache, because "we deleted the cache" reads as a regression to anyone who has not seen the break-even. If a full dependency-tree cache is kept anyway, key it on the manifest **and** the lockfile — keyed on the lockfile alone it can hit after a manifest-only change and silently test a stale tree.

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
