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

Nx needs no wiring on Avrea runners (Nx 20.8 and newer): tasks pick up the
colocated remote cache as written, and because the cache is shared, a result
computed once is reused by the next CI run, other branches, and teammates on
the same commit. That sharing is exactly the trust boundary
`references/monorepos.md` describes — a shared task cache means a poisoned
entry travels; the read/write scoping questions below apply here too.

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

`url_v2` is required. Without it, BuildKit talks to GitHub's cache service: on Linux amd64 it silently degrades to the slower upstream cache, and on Linux ARM the build fails. The amd64 fallback is invisible in outcomes — the build succeeds and layers still print `CACHED`; the tell is the log line `exporting to GitHub Actions Cache` in a build running on an Avrea runner, plus import/export step timings (a measured 2.6× delta on the warm build *step* — compare the step, not the job total, since fixed job cost dominates). Use `mode=max` for multi-stage Dockerfiles so intermediate stages are exported — the `mode=min` default re-runs the build stage every time. Add `scope=<name>` when a repository builds several images. Also add `.git` to `.dockerignore`: with `COPY . .`, differing timestamps under `.git/` bust the cache on every run even at the same commit.

Xcode compilation caching requires Xcode 26+ and macOS runners, and covers only your own sources. SwiftPM *dependencies* are handled by the Swift Package Registry below rather than by an explicit `actions/cache` on `~/Library/Caches/org.swift.swiftpm/` — that manual cache is still what covers private packages, branch- or commit-pinned dependencies, and runners on older Xcode, as described in `references/swift-xcode.md`.

### Swift Package Registry (macOS)

SwiftPM's default fetch is a full git clone of each dependency's repository,
history included, repeated on every fresh runner. Avrea's macOS runners
resolve **public** packages through a hosted registry instead — each version
is a small checksummed archive from colocated storage — and it is **on by
default with Xcode 26 and newer**. Once a version is cached, resolving it
does not touch GitHub at all.

What does *not* change: private packages and branch- or commit-pinned
dependencies keep resolving via git, in the same build. Runners on older
Xcode keep resolving via git even when the setting is enabled, so a mixed
fleet will not behave uniformly — check the Xcode version before attributing
a resolve-time difference to the registry.

The one real consequence to plan for: registry resolution changes how
`Package.resolved` records pins (registry identities and checksums rather
than git URLs and revisions), so the **first resolve rewrites the file**.
A repository that must keep git-form pins can turn the registry off per
organization or repository:

```bash
avr settings set cache.swift-registry.enabled false
```

`cache.swift-registry.enabled` is documented by Avrea (2026-07-29) but is
newer than the `avr settings schema` snapshot taken for this reference on
2026-07-28 — confirm it with `avr settings schema` before relying on it, and
treat disabling it as the shared-state mutation it is.

Avrea's published benchmark resolving vapor's 28-package graph on a fresh
runner shows where the win actually comes from:

| Setup | Resolve time |
|---|---|
| git, no lockfile | 23s |
| Registry, no lockfile | 11s |
| Registry, committed lockfile + `--force-resolved-versions` | 4s |

Most of the remaining time after the registry is version *exploration*, not
download — which is why the committed-lockfile discipline in
`references/swift-xcode.md` is worth more than the transport change.


## Package cache

Pre-configured for npm/yarn/pnpm/bun, pip, Go modules, Cargo, Maven/Gradle, NuGet/.NET, Chocolatey, and RubyGems/Bundler. `uv` requires manual setup.

Two coverage details worth knowing before you diagnose a "direct fetch":

- **Gradle resolves through a targeted rewrite, not a global mirror.** Maven's
  mirror config does not govern Gradle's resolver, so `mavenCentral()` is
  rewritten through the Avrea cache while `google()`, `gradlePluginPortal()`,
  JitPack, corporate Maven, and `mavenLocal()` are left exactly as written.
  Seeing those repositories go direct is expected, not a misconfiguration.
- **.NET on Linux is proxied** through the Avrea NuGet cache (it previously
  went straight to `api.nuget.org`, unlike Windows), and the Go build cache is
  active on Windows rather than a silent no-op.

For Node, the proxy is exposed through `npm_config_registry="https://cache.avrea.com:8443/npm/"`, honored by npm, pnpm, yarn v1, and bun. Yarn Berry (v2+) ignores the variable and needs `npmRegistryServer` in `.yarnrc.yml`.


`cache.avrea.com` resolves only inside Avrea runners. Do not commit it into `.npmrc`, `turbo.json`, or any config shared with developer machines or another CI provider — it will fail to resolve there. This is the most likely way to break local development while optimizing CI.

The docs do not document integrity/lockfile behavior for proxied packages. Keep `--frozen-lockfile` / `npm ci` semantics as the determinism guarantee, per `references/typescript-toolchain.md`, rather than relying on the proxy for it.

## Write behavior and integrity

Three platform behaviors that change how you read cache symptoms:

- **Concurrent writes converge.** When parallel jobs produce the same cached
  artifact, they reuse the completed write instead of reporting the overlap as
  a failure, and large build-cache/package-cache uploads take a more reliable
  path. This applies automatically, including to sccache. A cache-write error
  under fan-out is therefore a real defect to investigate now, not the
  expected cost of parallelism.
- **Writes are checked before reuse.** A successful write is verified before it
  becomes available, so "wrote it last run, missed it this run" is no longer
  the routine explanation for a cold second run — look at the key instead.
- **The index is pre-warmed across every scope.** The first cached build of the
  day used to pay a cold-start cost while the index loaded; it no longer does.
  Do not attribute a slow first-of-day build to index warm-up — that excuse is
  retired, and the cause is elsewhere.
- **Entries carry end-to-end integrity checks** (native checksums plus
  compressed-frame checks) on package and GitHub Actions cache.

None of this changes the trust model in `references/caching.md`: integrity
checking proves an entry arrived intact, not that it was written by something
you trust.


## Quota and eviction

One quota per repository shared across all three layers; default 25 GB (observed as 26843545600 bytes). LRU eviction once over quota, and entries unused for more than 7 days are eligible for eviction regardless of quota.

```bash
avr cache usage --repo org/app --json '*'
avr cache list --repo org/app -L 200 --json key,cache_type,size_bytes,hit_count,last_accessed_at
```

`hit_count` is the field that turns cache work into evidence. On a real repository (2026-07-28), a 247.7 MB entry showed 0 hits alongside a same-key 307 MB entry with 12 hits — bytes consuming quota and upload time while returning nothing. Look for large-and-cold entries before adding any new cache: they push useful entries toward eviction and make every save slower.

Zero hits can also mean the key changes on every run. Check whether the key includes something volatile before deleting anything.

## Diagnosing and changing caches

```bash
avr settings list --prefix cache.          # what is enabled and where it resolved from
avr settings set cache.sccache.enabled false
avr settings reset cache.sccache.enabled
```

Cache toggles and `avr cache delete` are shared-state mutations. `avr cache delete --all` clears every entry for the repository and will slow the next runs for everyone touching it. Confirm before running either, and prefer a targeted `--type`/`--key`/`--ref` deletion when testing a suspected poisoned or stale entry.

## Sources

- Cache overview: https://docs.avrea.com/cache/overview/ (accessed 2026-07-28)
- Managing cache: https://docs.avrea.com/cache/managing/ (accessed 2026-07-29)
- GitHub Actions cache: https://docs.avrea.com/cache/github-actions/ (accessed 2026-07-28)
- Build cache overview: https://docs.avrea.com/cache/build-cache/overview/ (accessed 2026-07-28)
- Turborepo: https://docs.avrea.com/cache/build-cache/turborepo/ (accessed 2026-07-28)
- Xcode: https://docs.avrea.com/cache/build-cache/xcode/ (accessed 2026-07-29)
- Swift Package Registry: https://docs.avrea.com/cache/packages/swift/ (accessed 2026-07-29)
- Docker: https://docs.avrea.com/cache/build-cache/docker/ (accessed 2026-07-29)
- Package cache overview: https://docs.avrea.com/cache/packages/overview/ (accessed 2026-07-28)
- npm/yarn/pnpm/bun: https://docs.avrea.com/cache/packages/npm/ (accessed 2026-07-28)
- Storage and eviction: https://docs.avrea.com/cache/storage/ (accessed 2026-07-28)
- Changelog (Swift registry, Nx cache, write reliability, coverage additions, index pre-warm, integrity): https://docs.avrea.com/changelog/ (accessed 2026-07-29)
- Quota and hit-count values verified via `avr cache usage` / `avr cache list` on `avr` 0.1.6 (2026-07-28)
