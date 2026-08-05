# Fix: build-performance-turbopack

**Corpus lineage:** build-performance-turbopack/03-implementation-cache-migration.md,
build-performance-turbopack/04-implementation-speed-flags.md,
build-performance-turbopack/05-diagnostics-slow-build-recipe.md,
build-performance-turbopack/08-version-lockin-seo-vercel.md
**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 docs. Confirm any
config key against the installed package first — see `references/gating/capability-probe.md`.

**Stability arc, restated once:** `next dev` Turbopack reached stable in v15.0. `next
build --turbopack` was alpha v15.3, beta v15.5, and became **stable + default for both dev
and build in v16.0**. `--webpack` remains a fully documented opt-out in 16.x, not a
deprecated fallback.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| Verify/keep Turbopack defaults | Next.js ≥16.0.0 | `fully-reversible` | Confirms nothing blocks the default path |
| Filesystem cache flags (dev + build) | ≥15.5 (dev) / ≥16.0 (build) | `fully-reversible` | Cache not restored in CI; ambiguous-default version |
| CI cache preservation | Any non-Vercel CI running `next build` | `fully-reversible` | Missing `.next/cache` restore/save step |
| Webpack config migration | Next.js ≥15.3 (`turbopack` location) | `component-level-revert` | `webpack()` block or `experimental.turbo` present |
| `--webpack` escape hatch | Any | `fully-reversible` | A confirmed, named blocker with no Turbopack alternative |
| Rust React Compiler + TS7 opt-ins | Next.js ≥16.3.0 | `component-level-revert` | Trialing experimental compile/type-check levers |
| Dev memory eviction | Next.js ≥16.3.0 | `fully-reversible` | Long dev sessions climbing in memory |
| Bound `generateStaticParams` | App Router, any version | `fully-reversible`, product-visible at runtime | Unbounded catalog-scale static param generation |
| Vercel Build Cache and `vercel build` | Vercel platform | `fully-reversible` | External CI builds outside Vercel's own step |
| Ordered slow-build diagnosis recipe | Next.js ≥16.0.0 (phase timings) | n/a — diagnostic | "Build is slow" with no isolated cause yet |

## Verify/keep Turbopack defaults — requires Next.js ≥16.0.0

**When to apply:** repo targets 16.0+ and no `webpack()` block or plugin blocks the
default — confirm it's active, don't restate it.

```jsonc
// package.json — Next.js 16.3
{ "scripts": { "dev": "next dev", "build": "next build", "start": "next start" } }
```

No `--turbo`/`--turbopack` flag is needed — "Turbopack is now the default bundler... No
configuration is needed." An explicit flag on ≥16.0.0 is a no-op that only obscures this.

**Verify after applying:** `next build` opens with `▲ Next.js 16.x (Turbopack)` and lists
timed phases; smoke tests pass (a compiler pass alone doesn't prove loader/plugin parity).

**Lock-in / reversibility:** `fully-reversible`. Add `--webpack` to fall back.

**Rollback:** append `--webpack` to the `dev`/`build` scripts.

## Filesystem cache flags (dev + build) — requires Next.js ≥15.5 (dev) / ≥16.0 (build)

**When to apply:** CI/self-hosted build never restores `.next/cache`, or the install sits
in the ambiguous-default version window and the flags should be explicit.

Default-on by version: 16.0 both beta, undocumented default · 16.1 dev **default**, build
not yet · 16.3 **both default `true`**.

```ts
// next.config.ts — Next.js 16.3, explicit for policy visibility
import type { NextConfig } from 'next'
const nextConfig: NextConfig = {
  experimental: { turbopackFileSystemCacheForDev: true, turbopackFileSystemCacheForBuild: true },
}
export default nextConfig
```

Paths: dev `.next/dev/cache/turbopack`; build `.next/cache/turbopack`. On ≥16.3 both
already default `true` (redundant, not wrong, to set explicitly); on 16.0–16.2 the build
flag's default is undocumented — probe the installed schema first.

**If the environment never restores `.next/cache`:** set
`turbopackFileSystemCacheForBuild: false` — docs explicitly recommend this when the build
environment can't preserve the cache; an unrestored cache has no value, only write cost.

**Verify after applying:** compare two builds of the same commit, or one source edit;
confirm `.next/cache/turbopack` exists after the first build and the second compile phase
is measurably lower — three Vercel-measured cases showed 1.4×, 2.3×, and 5.5×.

**Lock-in / reversibility:** `fully-reversible`. Delete the cache directory or set the
flag `false` — no architectural coupling.

**Rollback:** remove the `turbopackFileSystemCache{ForDev,ForBuild}` keys.

## CI cache preservation — requires any non-Vercel CI running `next build`

**When to apply:** `.github/workflows/*` runs `next build` with no `.next/cache`
restore/save step — every build behaves like a cold build.

```yaml
# .github/workflows/build.yml excerpt — Next.js 16.3
- uses: actions/cache@v4
  with:
    path: |
      ~/.npm
      ${{ github.workspace }}/.next/cache
    key: ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-${{ hashFiles('**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx') }}
    restore-keys: |
      ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-
```

This is the official non-Vercel-CI example. **On Vercel itself this is unnecessary** —
"Next.js caching is automatically configured for you." `restore-keys` lets a partial hit
(matching lockfile, different source hash) restore something rather than starting cold.

**Verify after applying:** cache-restore step succeeds in CI logs; `.next/cache/turbopack`
exists after the first run; second build's compile phase is lower.

**Lock-in / reversibility:** `fully-reversible`. Remove the step; builds return to
cold-every-time.

**Rollback:** delete the `actions/cache@v4` step.

## Webpack config migration — requires Next.js ≥15.3 for the `turbopack` config location

**When to apply:** `experimental.turbo` present on an install ≥16.0.0 (dead location,
probe first), or a `webpack()` block has loaders/aliases needing a Turbopack equivalent.

```diff
- experimental: { turbo: { rules: { /* ... */ } } }
+ turbopack: { rules: { /* ... */ } }
```

```bash
npx @next/codemod@latest next-experimental-turbo-to-turbopack .
```

```ts
// next.config.ts — Next.js 16.3
import type { NextConfig } from 'next'
const nextConfig: NextConfig = {
  turbopack: {
    resolveAlias: { underscore: 'lodash', mocha: { browser: 'mocha/browser-entry.js' } },
    resolveExtensions: ['.mdx', '.tsx', '.ts', '.jsx', '.js', '.mjs', '.json'],
    rules: { '*.svg': { loaders: [{ loader: '@svgr/webpack', options: { icon: true } }], as: '*.js' } },
  },
}
export default nextConfig
```

`rules` only supports loaders returning JavaScript with plain primitive/object/array
options — unsupported APIs include `importModule`, `loadModule`, `emitFile`, `utils`,
most of `resolve`; `fs` only supports `readFile`. `resolveAlias` is Turbopack's own
mechanism, distinct from webpack's `resolve.alias` — hand-port, don't copy. **Webpack
plugins have no migration path** — "Turbopack does not support webpack plugins… find
Turbopack-compatible alternatives or continue using webpack." A repo with a required
plugin stays fully on `--webpack`, not a partial config.

**Verify after applying:** import an SVG by relative path and alias in dev and prod, test
HMR. A known 16.0 bug dropped `resourceQuery` for aliased custom-loader imports (GitHub
Issue #85317) — import by relative path if the loader depends on it. Also test CSS import
order and decimal-sensitive values — Turbopack follows import order strictly and Lightning
CSS uses 5-digit precision vs. webpack's 10-digit.

**Lock-in / reversibility:** `component-level-revert`. Config-only; revert each
`turbopack.rules`/`resolveAlias` entry, or restore the `webpack()` callback.

**Rollback:** restore the removed `webpack()` block, or run with `--webpack` while
migration is incomplete.

## `--webpack` escape hatch — requires any Next.js version

**When to apply:** a confirmed, named blocker — required plugin, custom Sass function
(`sassOptions.functions`), Yarn PnP — with no Turbopack alternative yet.

```jsonc
{ "scripts": { "dev": "next dev --webpack", "build": "next build --webpack" } }
```

Fully supported, documented opt-out in 16.x, not deprecated. Record the specific blocker
in an adjacent comment so the opt-out can be revisited.

**Verify after applying:** both scripts run, plugin output exists, and no Turbopack-only
API (`import.meta.glob`, import attributes) is used anywhere — mixing those with
`--webpack` breaks the build.

**Lock-in / reversibility:** `fully-reversible`. Remove the flag once the blocker resolves.

**Rollback:** delete `--webpack` from the scripts.

## Rust React Compiler + TS7 opt-ins — requires Next.js ≥16.3.0

**When to apply:** `reactCompiler: true` is already adopted and the team wants to trial
the experimental Rust compile path; or the project can move to `typescript@^7`.

**Status: both experimental, current-docs "not recommended for production."** Trial on a
branch with functional tests before any default rollout.

```bash
pnpm add -D babel-plugin-react-compiler   # required by the stable Babel path
```

```ts
// next.config.ts — Next.js 16.3, experimental
import type { NextConfig } from 'next'
const nextConfig: NextConfig = {
  reactCompiler: true,
  experimental: { turbopackRustReactCompiler: true },
}
export default nextConfig
```

16.3 reports "the Rust path cut the time from `next dev` to a ready page by 34% on a cold
build and 46% on a warm one. These gains assume you've moved off Babel entirely."
`turbopackRustReactCompiler` is a strict dependent of `reactCompiler` — nothing to
accelerate if that's absent/`false`; leftover Babel-only transforms mean "mixed
Babel/Rust," a smaller gain than the vendor claim.

```bash
pnpm add -D typescript@^7   # Next.js 16.3
```

No enabling config is required — `experimental.useTypeScriptCli` defaults `true`.
Diagnostics come from `tsc` directly, not Next's code-frame rewriting; the whole
configured project is checked including tests; `--debug-build-paths` does **not** limit
the type-check set; `typescript.ignoreBuildErrors` skips the entire step. For type-only CI
jobs: `next typegen && tsc --noEmit`.

**Verify after applying (Rust compiler):** record cold/warm `next dev`-ready times on
stable Babel, enable the Rust flag, repeat on identical commit/machine/cache; run
functional tests of compiler-transformed components; revert if behavior or time regresses.

**Verify after applying (TS7):** run the exact CI build before/after on the same
dependency state, comparing only "Finished TypeScript" time. Never set
`ignoreBuildErrors` to manufacture a faster build — that corrupts the check.

**Lock-in / reversibility:** both `component-level-revert`. Rust compiler requires the app
already runs cleanly on stable Babel; TS7 is a real dependency change across the repo, and
`useTypeScriptCli: false` errors outright while TS7 is installed.

**Rollback:** delete `turbopackRustReactCompiler` (Babel remains via `reactCompiler:
true`). Downgrade the `typescript` dependency to revert TS7.

## Dev memory eviction — requires Next.js ≥16.3.0

**When to apply:** a long `next dev` session climbs in memory (a documented case showed
21.5GB→2GB after enabling eviction at 50 compiled routes), or the dev filesystem cache is
confirmed enabled and the default should be made explicit.

```ts
// next.config.ts — explicit diagnostic configuration, Next.js 16.3
import type { NextConfig } from 'next'
const nextConfig: NextConfig = {
  experimental: { turbopackFileSystemCacheForDev: true, turbopackMemoryEviction: 'auto' },
}
export default nextConfig
```

Values: `false` (never evict), `'auto'` (default — evict on allocation/OS-pressure
feedback), `'full'` (evict all possible data on every snapshot). This option "only has an
effect in `next dev` sessions when the FileSystem Cache is enabled" — with the dev cache
disabled, or on `next build`, it does nothing.

**Verify after applying:** compile a representative route set, record dev process RSS
after a long session, restart and repeat with identical route order. Don't use the
vendor's ~90%/~82% figures as a pass criterion — results depend on route graph size.

**Lock-in / reversibility:** `fully-reversible`. Config-only, dev-only.

**Rollback:** remove the key, or set it back to `false`.

## Bound `generateStaticParams` — requires App Router, any version

**When to apply:** an unbounded `generateStaticParams` return over a catalog-scale data
source — "Every page you prerender increases build work and produces output that has to
be stored and deployed."

```tsx
// app/blog/[slug]/page.tsx — Next.js 16.3
export async function generateStaticParams() {
  const posts: Array<{ slug: string; popularity: number }> = await fetch(
    'https://example.com/api/posts'
  ).then((response) => response.json())

  return posts.sort((a, b) => b.popularity - a.popularity).slice(0, 100).map(({ slug }) => ({ slug }))
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  return <article>{slug}</article>
}
```

```ts
// Only generated params are valid; every omitted route returns 404.
export const dynamicParams = false
```

`dynamicParams` stays at its default `true` in the base recipe — omitted params still
render later, so narrowing the build set doesn't remove the long tail from being served,
only from being pre-built. Setting `dynamicParams = false` is a separate, product-visible
decision (every unlisted route 404s).

**Verify after applying:** build output's "Generating static pages" count/time falls;
visit a param inside and outside the list in production and confirm the intended behavior.

**Lock-in / reversibility:** `fully-reversible` at config level. **Product-visible at
runtime** — coordinate with `rendering-strategy-caching` before narrowing scope on a live
app, per `references/gating/priority-matrix.md`.

**Rollback:** remove the `.slice(0, N)` bound; delete `dynamicParams = false` if added.

## Vercel Build Cache and `vercel build` — requires Vercel platform

**When to apply:** a build needs to run outside Vercel's own build step (external CI,
prebuilt pipeline), or the Build Cache needs bypassing as a diagnostic.

```bash
vercel pull
vercel build
vercel deploy --prebuilt
```

Artifacts land in `.vercel/output`; combined with `--prebuilt` this creates a deployment
without sharing source with Vercel. To clear caches as a **diagnostic, not a permanent
fix**: Build Cache — redeploy with **Use existing Build Cache** unchecked, `vercel
--force`, or `VERCEL_FORCE_NO_BUILD_CACHE=1`; Turborepo Remote Cache — `TURBO_FORCE=true`.

"The previous Build's cache is restored prior to the Install/Build command" on Vercel
automatically — no repo-side action needed there; this recipe is only for the
external-CI/prebuilt-deploy path. The cache key derives from
account/project/preset/root/Node/package-manager/branch — a "corrupt cache" symptom is
often a cache-key change (e.g. branch switch), needing no manual clearing.

**The Turborepo/Turbopack cache contradiction — carry both sides.** Vercel's Turborepo
Remote Caching page says: "You can avoid caching the `.next/cache` folder since it is only
used for development and will not speed up your production builds." Next.js 16.3's own
FileSystem Cache docs directly contradict this, documenting `.next/cache/turbopack` **as
the production build cache**, with repeat builds 1.4×–5.5× faster once it persists.
**Bounded synthesis:** let Vercel's Build Cache restore `.next/cache` automatically; do
**not** additionally add `.next/cache` to a Turborepo task's Remote Cache `outputs` until
Vercel reconciles the two pages. The caches are architecturally distinct regardless —
Remote Cache stores task-level output artifacts; the filesystem cache stores
compiler-internal, function-level results inside one `next build`. A monorepo can use
both; disabling one doesn't disable the other.

**Verify after applying:** compare build wall time and per-phase timing with cache
restored vs. force-disabled on the same commit; confirm `TURBO_FORCE` and Vercel's
force-no-cache flags weren't both silently masking each other during the comparison.

**Lock-in / reversibility:** `fully-reversible`. Billing/CI-config only.

**Rollback:** remove the force-no-cache environment variables; re-check the Build Cache
checkbox on redeploy.

## Ordered slow-build diagnosis recipe — requires Next.js ≥16.0.0 for phase timings

**When to apply:** any "the build is slow" report with no isolated cause yet. Read the
build output as a phase profile before touching any lever:

```text
▲ Next.js 16 (Turbopack)
✓ Compiled successfully in 615ms
✓ Finished TypeScript in 1114ms
✓ Collecting page data in 208ms
✓ Generating static pages in 239ms
✓ Finalizing page optimization in 5ms
```

**Do not apply a compiler fix to a prerender or postbuild bottleneck.**

| Step | Symptom | Likely cause | Lever |
|---|---|---|---|
| 1 | Deployment slow, unclear where | Queue/install/build/domain assignment may differ | Vercel Build Diagnostics, per-step duration |
| 2 | "Compiled" dominates, repeat as slow as cold | `.next/cache` not restored or broadly invalidated | Confirm cache restore, preserve `.next/cache`, compare cold/warm |
| 3 | Cache restored but no compile gain | Change invalidates graph, or overhead outweighs reuse | Test one-file edit; disable build cache writes if never preserved |
| 4 | "Finished TypeScript" dominates | Large TS project / current compiler | Trial `typescript@^7`; `next typegen && tsc --noEmit` for type-only jobs |
| 5 | "Collecting page data" dominates | Expensive data calls, large param enumeration | Inspect `generateStaticParams`; memoize identical `fetch` |
| 6 | "Generating static pages" dominates | Too many routes, heavy per-page rendering | Bound `generateStaticParams` to a popular subset |
| 7 | Memory climbs / Vercel cancels | Source maps, large graph, cache pressure | Keep source maps off; inspect system report; profile before upsizing |
| 8 | Custom postbuild dominates | App scripts, image pre-generation | Time each script — **`next/image` is on-demand, never build-time**; image count is never a valid slow-build cause |
| 9 | Turbopack fails or output differs | Webpack plugin/loader/CSS-order gap | Port a supported loader or use `--webpack`; file a minimal repro |
| 10 | CPU-bound after code/cache fixes | Too little compute | Elastic right-sizing, or benchmark Enhanced/Turbo only after diagnosis |

**Narrow diagnostic commands:** `next build --debug` (rewrites/redirects/headers, general
output) · `next build --debug-prerender` (readable stack traces — **never deploy this
build**, it disables minification and prerender early exit) · `next build
--debug-build-paths="app/**/page.tsx"` (isolate a route/glob) · `next build
--experimental-cpu-prof` (V8 profiles to `.next-profiles/`) · `next dev --internal-trace`
(Turbopack trace to `.next-profiles/trace-turbopack.bin`).

**Vercel resource diagnostics:** set `VERCEL_BUILD_SYSTEM_REPORT=1` temporarily — can
reveal hidden OOM events and file sizes. Standard machine: 8GB memory, 4 CPUs, 32GB disk;
Vercel cancels builds exceeding these limits.

**Cold/warm experiment protocol:** pin commit/lockfile/Node/machine tier → cold build
(cache skipped) → warm build (cache restored) → one representative edit, run again →
compare each phase, not only wall time → note whether Turborepo Remote Cache and Vercel
Build Cache were both on (either can mask the other; use `TURBO_FORCE=true` and `vercel
--force` to isolate them) → restore normal caching after.

**What is explicitly insufficient:** no official percentage tells an agent when to
upgrade machine tiers; `staticGeneration*` docs publish no defaults; no documented "cache
hit" log line exists — verify via restored paths plus phase-time comparison only.

**Verify after applying:** re-run the cold/warm protocol after each lever change; confirm
the specific phase named in the symptom row improved, not just overall wall time.

**Lock-in / reversibility:** n/a — diagnostic only, no config of its own.

**Rollback:** n/a.

## Ordering within this domain

1. **Confirm no `webpack()` block or plugin blocks the default path first** — resolve the
   webpack boundary decision before anything else.
2. **Verify/keep Turbopack defaults**, then **filesystem cache flags** — establish
   baseline cache behavior before diagnosing anything as "slow."
3. **Run the ordered slow-build diagnosis recipe** to identify which phase dominates
   before applying any single lever.
4. **Apply the one lever the diagnosis names** — never stack multiple experimental levers
   at once (`turbopackMemoryEviction`, `turbopackRustReactCompiler`, `useTypeScriptCli`,
   `staticGeneration*` each carry independent experimental status).
5. **CI cache preservation and Vercel Build Cache/`vercel build`** are independent and can
   land at any point once the build path is otherwise stable.

## Conflicts to watch

- **`generateStaticParams` scope reduction is product-visible at runtime** — coordinate
  with `rendering-strategy-caching` before narrowing scope on a live app.
- **A build-cost finding can masquerade as a Fluid Compute or ISR cost finding.** Confirm
  the build machine tier before routing a "bill went up" report to
  `vercel-platform-deployment` — see `references/gating/cost-model.md`.
- **Enabling every experimental speed flag at once makes regressions unattributable** —
  change one, verify, then move to the next.
