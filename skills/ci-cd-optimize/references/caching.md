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

## Time the uncached path before adding any cache

"Installs are slow" is an assumption until measured. On a runner colocated with a package
registry proxy, installs already resolve from local storage, so a cache layer on top can add a
save step and a correctness risk while saving nothing.

One observed A/B on a fixed commit: install took ~5s both with and without a full `node_modules`
cache, the cached variant paying an extra save step. That single pair does not prove the proxy
caused it — the generalizable reading is narrower and more useful: **when the uncached step is
already seconds, no cache layer can help.** Time it first, then decide.

If you do keep a full dependency-tree cache, key it on the manifest **and** the lockfile. Keyed on
the lockfile alone it can hit after a manifest-only change and silently test a stale tree, which
is the failure the key-completeness rules above exist to prevent.

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
