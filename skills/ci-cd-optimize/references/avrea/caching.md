# Avrea Caching

Optional. Read when a repository runs on Avrea and cache restore, install, or build-reuse time is the measured bottleneck. The correctness rules in `references/caching.md` — scope, poisoning, and whether a hit actually saves time — still apply; colocation changes the transfer cost, not the trust model.

## Three layers

| Layer | What it covers | Setup |
|---|---|---|
| GitHub Actions cache | Drop-in for `actions/cache@v4+` and setup-action caching | None |
| Build cache | Compiler/task output across jobs, branches, and runs | Env vars and config files pre-injected |
| Package cache | Pull-through proxy for registries | Registry URLs pre-configured |

All three run on the same infrastructure as the runners. The mechanism is locality: Actions cache calls are redirected to a local proxy instead of GitHub's remote blob storage, build tools point at a colocated remote cache, and package managers resolve through a local proxy. Restores are documented as up to 5× faster, scaling with cache size.

This changes the arithmetic in `references/caching.md` but not the rule. A cache is still only worth keeping if restore plus post-hit work beats the clean path — a cheap restore makes marginal caches *more* likely to pay off, not automatically worthwhile.

## GitHub Actions cache

Compatible with anything on GitHub's Cache v2 API: `actions/cache@v4+` including `save`/`restore`, setup actions with caching enabled (`setup-node`, `setup-go`, `setup-python`, `setup-java`), and Buildx `type=gha`. No workflow changes.

Scoping mirrors GitHub's model exactly, which is what preserves the trust boundary:

- Default branch reads and writes.
- Feature branches read from the default branch, write only to their own scope.
- PRs read from base and default branches.
- Sibling and child branches are isolated.
- Entries are keyed on `(key, version)` and are immutable once written.
- Repositories are isolated namespaces.

Because the semantics are unchanged, the cache-poisoning analysis in `references/caching.md` carries over without modification: an untrusted PR still must not be able to write a cache that trusted branches consume.

## Build cache

Auto-configured tools: Bazel (HTTP remote cache), ccache, Go (`GOCACHEPROG`, Go 1.24+), Gradle (`HttpBuildCache`), Maven (extension), Nix (binary substituter), Nx (self-hosted remote cache), sccache (WebDAV), Turborepo (remote cache API), Xcode (compilation cache, macOS only).

Turborepo, for a TypeScript monorepo, needs no `turbo.json` change. On Avrea runners the variables are already set:

```
TURBO_API="http://cache.avrea.com:8290"
TURBO_TOKEN="unused"
TURBO_TEAM="team_avrea"
```

Two things to note rather than gloss over: the endpoint is plain HTTP on an internal host, and the token is the literal string `unused` — authentication derives from running on Avrea infrastructure. The docs do not describe how namespaces separate between repositories for this layer. If a monorepo's task outputs are sensitive, raise that as an open question rather than assuming isolation; the `references/monorepos.md` remote-cache trust discussion applies.

Docker requires the one genuinely mandatory workflow edit in this section:

```yaml
- uses: docker/build-push-action@v6
  with:
    cache-from: type=gha,url_v2=https://cache.avrea.com/
    cache-to: type=gha,url_v2=https://cache.avrea.com/,mode=max
```

`url_v2` is required. Without it, BuildKit talks to GitHub's cache service: on Linux amd64 it silently degrades to the slower upstream cache, and on Linux ARM the build fails. Use `mode=max` for multi-stage Dockerfiles so intermediate stages are exported — the `mode=min` default re-runs the build stage every time. Add `scope=<name>` when a repository builds several images. Also add `.git` to `.dockerignore`: with `COPY . .`, differing timestamps under `.git/` bust the cache on every run even at the same commit.

Xcode compilation caching requires Xcode 26+ and macOS runners, and covers only your own sources — SwiftPM dependencies still need explicit `actions/cache` on `~/Library/Caches/org.swift.swiftpm/`, as described in `references/swift-xcode.md`.

## Package cache

Pre-configured for npm/yarn/pnpm/bun, pip, Go modules, Cargo, Maven/Gradle, NuGet/.NET, Chocolatey, and RubyGems/Bundler. `uv` requires manual setup.

For Node, the proxy is exposed through `npm_config_registry="https://cache.avrea.com:8443/npm/"`, honored by npm, pnpm, yarn v1, and bun. Yarn Berry (v2+) ignores the variable and needs `npmRegistryServer` in `.yarnrc.yml`.

`cache.avrea.com` resolves only inside Avrea runners. Do not commit it into `.npmrc`, `turbo.json`, or any config shared with developer machines or another CI provider — it will fail to resolve there. This is the most likely way to break local development while optimizing CI.

The docs do not document integrity/lockfile behavior for proxied packages. Keep `--frozen-lockfile` / `npm ci` semantics as the determinism guarantee, per `references/typescript-toolchain.md`, rather than relying on the proxy for it.

## Quota and eviction

One quota per repository shared across all three layers; default 25 GB (observed as 26843545600 bytes). LRU eviction once over quota, and entries unused for more than 7 days are eligible for eviction regardless of quota.

```bash
avr cache usage --repo org/app --json '*'
avr cache list --repo org/app -L 200 --json key,cache_type,size_bytes,hit_count,last_accessed_at
```

`hit_count` is the field that turns cache work into evidence. On a real repository (2026-07-28), a 247.7 MB entry showed 0 hits alongside a same-key 307 MB entry with 12 hits — bytes consuming quota and upload time while returning nothing. Look for large-and-cold entries before adding any new cache: they push useful entries toward eviction and make every save slower.

Zero hits can also mean the key changes on every run. Check whether the key includes something volatile before deleting anything.

### The package proxy can make a store cache redundant

The Actions store cache and the package proxy solve the same problem for
dependency installs, and on Avrea the proxy alone is often enough. Measure the
install step cold and warm before keeping the store cache:

| Observation | Reading |
|---|---|
| install is equally fast cold and warm | the proxy is doing the work; the store cache adds bytes, not speed |
| install is materially slower cold | the store cache is earning its quota |

Measured on a real repository (2026-07-28): a pnpm install took 3.3 s on a cold
runner and 2.5 s warm, while the 300 MB store entry recorded 0 hits and the
save step cost ~0 s. Removing `cache: pnpm` freed 1.2 % of the 25 GiB quota and
cost nothing in wall-clock. The correct default on Avrea is to start without a
package-store cache and add one only if cold installs measurably hurt.

## Diagnosing and changing caches

```bash
avr settings list --prefix cache.          # what is enabled and where it resolved from
avr settings set cache.sccache.enabled false
avr settings reset cache.sccache.enabled
```

Cache toggles and `avr cache delete` are shared-state mutations. `avr cache delete --all` clears every entry for the repository and will slow the next runs for everyone touching it. Confirm before running either, and prefer a targeted `--type`/`--key`/`--ref` deletion when testing a suspected poisoned or stale entry.

## Sources

- Cache overview: https://docs.avrea.com/cache/overview/ (accessed 2026-07-28)
- Managing cache: https://docs.avrea.com/cache/managing/ (accessed 2026-07-28)
- GitHub Actions cache: https://docs.avrea.com/cache/github-actions/ (accessed 2026-07-28)
- Build cache overview: https://docs.avrea.com/cache/build-cache/overview/ (accessed 2026-07-28)
- Turborepo: https://docs.avrea.com/cache/build-cache/turborepo/ (accessed 2026-07-28)
- Xcode: https://docs.avrea.com/cache/build-cache/xcode/ (accessed 2026-07-28)
- Docker: https://docs.avrea.com/cache/build-cache/docker/ (accessed 2026-07-28)
- Package cache overview: https://docs.avrea.com/cache/packages/overview/ (accessed 2026-07-28)
- npm/yarn/pnpm/bun: https://docs.avrea.com/cache/packages/npm/ (accessed 2026-07-28)
- Storage and eviction: https://docs.avrea.com/cache/storage/ (accessed 2026-07-28)
- Quota and hit-count values verified via `avr cache usage` / `avr cache list` on `avr` 0.1.6 (2026-07-28)
