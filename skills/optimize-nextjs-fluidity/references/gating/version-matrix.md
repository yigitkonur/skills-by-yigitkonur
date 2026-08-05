# Version matrix — removed, renamed, and version-gated surfaces

Knowledge baseline: verified 2026-08-05 against Next.js 16.3.0 docs. **Always confirm a
key's real status with `references/gating/capability-probe.md` before acting on a row
here** — this file says what the docs record; the probe says what the repo has.

Three headline flags were **removed, not stabilized**, in the 15→16 window
(`experimental.ppr`, `experimental.viewTransition`, `experimental.dynamicIO`). Any source
dated before October 2025 — including accepted answers on GitHub — is suspect.

## The graveyard: dead, renamed, or superseded

`Action` is what a task should propose **after** the probe confirms the key's state.

| Surface | Status in 16.x | Action | Recipe |
|---|---|---|---|
| `experimental.ppr` / `experimental_ppr` | Removed in 16.0 | Migrate to `cacheComponents`; a 15.x PPR adopter is a go/no-go migration, not a cleanup | `fix/rendering-strategy-caching.md` |
| `experimental.dynamicIO` | Removed/renamed 16.0 | Replace with `cacheComponents: true` | `fix/rendering-strategy-caching.md` |
| `experimental.useCache` | Folded into Cache Components 16.0 | Replace with `cacheComponents: true`; use stable `"use cache"` | `fix/rendering-strategy-caching.md` |
| `unstable_cacheLife` / `unstable_cacheTag` | Prefix dropped 16.0 | Mechanical rename to `cacheLife` / `cacheTag` from `next/cache` | `fix/rendering-strategy-caching.md` |
| `unstable_cache` | Superseded **when `cacheComponents` is on**; still valid without it | Migrate to `"use cache"` only if Cache Components is enabled | `fix/rendering-strategy-caching.md` |
| `export const revalidate` / `dynamic` / `fetchCache` | Incompatible under `cacheComponents` | Remove; express via `"use cache"` + `cacheLife` + Suspense | `fix/rendering-strategy-caching.md` |
| `revalidateTag(tag)` single-arg | Deprecated; TS error | `revalidateTag(tag, 'max')`, or `updateTag(tag)` in Server Actions | `fix/data-fetching-patterns.md` |
| `experimental.viewTransition` | Recorded removed in 16.x — **probe first, some 16.2.x installs still accept it** | If probe says `absent`: delete. If `present`: leave, note for the ≥16.3 upgrade | `fix/page-transitions-view-transitions.md` |
| `unstable_ViewTransition` import | Superseded | `import { ViewTransition } from 'react'` | `fix/page-transitions-view-transitions.md` |
| `middleware.ts` / exported `middleware()` | Deprecated + renamed 16.0 | `npx @next/codemod@canary middleware-to-proxy .` → `proxy.ts` / `proxy()`; Node runtime is fixed | `fix/vercel-platform-deployment.md` |
| `export const runtime = 'edge'` | Deprecated for pages/layouts/route handlers in 16.3 | Remove; Node.js is the default. **Prerequisite for `cacheComponents`** | `fix/vercel-platform-deployment.md` |
| `export const preferredRegion` | Deprecated 16.3 | Move placement to `vercel.json` `regions` | `fix/vercel-platform-deployment.md` |
| `images.domains` | Deprecated since 14 | Replace with narrow `images.remotePatterns` entries | `fix/image-optimization.md` |
| `<Image priority>` | Deprecated 16.0 — **still functional** | `fetchPriority="high"` / `loading="eager"`; `preload` only for one known LCP image | `fix/image-optimization.md` |
| `next/legacy/image` | Deprecated in 16 | Migrate to `next/image`; re-audit dimensions and `sizes` | `fix/image-optimization.md` |
| Build output `Size` / `First Load JS` table | **Removed from `next build` in 16.0** | Use `next experimental-analyze` or `@next/bundle-analyzer --webpack`. Never instruct reading the old table | `fix/bundle-code-splitting.md` |
| `serverComponentsExternalPackages` | Renamed 15.0 | `serverExternalPackages` | `fix/bundle-code-splitting.md` |
| `experimental.turbo` | Moved by 16 | Top-level `turbopack` key | `fix/build-performance-turbopack.md` |
| `@next/font` | Superseded 13.2 | Built-in `next/font/google` / `next/font/local` | `fix/font-script-optimization.md` |
| `strategy="worker"` / `experimental.nextScriptWorkers` | **Unsupported on App Router**, Pages-only, experimental | Do not enable. Use `lazyOnload`, `@next/third-parties`, or manual deferral | `fix/font-script-optimization.md` |
| `i18n` block in `next.config` | Pages-Router-only | Not an App Router path — use `[locale]` segment + `proxy.ts` | `fix/instant-i18n-locale-switching.md` |
| `unstable_setRequestLocale` → `setRequestLocale` | Renamed; the stable name is now **legacy** | Prefer `generateStaticParams` + `next/root-params` (16.3+) | `fix/instant-i18n-locale-switching.md` |
| `useFormState` | Renamed in React 19 | `useActionState` | `fix/data-fetching-patterns.md` |
| `ImageResponse` from `next/server` | Moved in 14.0 | Import from `next/og` | `fix/seo-metadata.md` |
| `themeColor` / `colorScheme` / `viewport` inside `metadata` | Deprecated location since 14 | `export const viewport` / `generateViewport` | `fix/seo-metadata.md` |
| Sync `params` / `searchParams` / metadata-file params | Breaking async change in 16 | `await` them; update signatures | `fix/seo-metadata.md` |
| AMP APIs/config | Removed in 16 | Remove AMP config/components | (upgrade-only; no perf recipe) |
| `next lint` / linting during `next build` | Removed in 16 | Run ESLint directly in CI | (tooling-only; no perf recipe) |

## Version floors — never recommend below these

| Feature | Floor | Also requires |
|---|---|---|
| `cacheComponents`, `"use cache"`, `cacheLife`, `cacheTag`, `updateTag`, `refresh` | 16.0.0 | Node.js runtime (no `runtime = 'edge'`) |
| `"use cache: private"` / `"use cache: remote"` | 16.0.0 | `cacheComponents` |
| `partialPrefetching`, `export const instant`, `export const prefetch` | 16.3.0 | `cacheComponents` |
| Instant Insights / Navigation Inspector | 16.3.0 | `cacheComponents` |
| `instant()` Playwright helper (`@next/playwright`) | 16.3.0 | separate package install |
| `next/root-params` | 16.3.0 | Server Components only |
| `<Link transitionTypes>` | 16.2.0 | — |
| `experimental.turbopackRustReactCompiler` | 16.3.0 | `reactCompiler: true` |
| `reactCompiler` (stable opt-in) | 16.0.0 | `babel-plugin-react-compiler` |
| `<Activity>`, `useEffectEvent` | React 19.2 | — |
| Streaming metadata + `htmlLimitedBots` | 15.2.0 | — |
| `images.localPatterns` query enforcement | 16.0.0 | — |
| Turbopack default for dev **and** build | 16.0.0 | — |

## Stability tiers

Classify every feature a task touches into one of four tiers, and say which in the task:

1. **Stable, default-on** — safe to rely on (Turbopack in 16, layout-deduplicated prefetch).
2. **Stable, opt-in** — safe to adopt deliberately (`cacheComponents`, `reactCompiler`,
   `partialPrefetching` on 16.3+).
3. **Experimental, production-discouraged** — never a *default* recommendation, never a
   correctness dependency (`staleTimes`, `useOffline`, `prefetchInlining`,
   `cachedNavigations`, `optimizePackageImports` — formally experimental despite wide use).
4. **Removed / superseded** — the graveyard above.

A task adopting a tier-3 feature must state the tier in its body and carry
`Reversibility: fully-reversible`. If it cannot be trivially removed, do not propose it.

## Watch list — re-check on every Next.js major

`cacheComponents` and `partialPrefetching` are both stated to become default in a future
major. `middleware.ts` will be removed (no version named). `runtime = 'edge'` removal is
likely. `staleTimes` may change or be absorbed without a normal deprecation window.
React `<ViewTransition>` and `addTransitionType` remain canary-channel. `<Activity>` is
expected to gain modes. `next/root-params` is expected to widen beyond Server Components.

## Support policy

Each Next.js major gets **two years of Maintenance LTS from its release date**. 15.x
released 2024-10-21 → computed support end **2026-10-21**. The support page does not print
that date; it is a computation from the stated policy, so phrase it that way in any task
that cites it.
