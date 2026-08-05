# Lock-in and reversibility — what the skill may not undo

Every task carries a `Reversibility:` field. Its value decides whether the autonomous
executor may apply the change at all. This file supplies the value.

**Classification (three values):**

- **`fully-reversible`** — delete a config line, a prop, or an import and the repo is
  exactly as before. Auto-apply allowed.
- **`component-level-revert`** — bounded code replacement or dependency unwind; a revert
  touches known files but is mechanical. Auto-apply allowed when the task is single-domain
  and its verification passes.
- **`migration-required`** — a one-way door: cross-route, URL-visible, persistent-data, or
  behavioural-model change. **Never auto-applied.** The task is written with
  `Status: blocked-needs-human` and a pre-flight checklist. See
  `references/workflow/safety-rails.md`.

## One-way doors, ranked

Highest exit cost first. If a task matches one of these, it is `migration-required` — no
exceptions, regardless of how small the diff looks.

| # | Technique | Why it is a door | Named exit cost |
|---|---|---|---|
| 1 | 15.x `experimental.ppr` adoption | Removed in 16, no shim | Stay pinned to a 15.x canary, or full Cache Components rewrite |
| 2 | Public URL / locale-routing policy | Externally persistent once indexed, linked, cached | Full redirect map, canonical/hreflang/sitemap rewrite, recrawl delay, ranking risk |
| 3 | `cacheComponents: true` after code depends on it | Inverts caching semantics; removes old segment configs; requires Node runtime; changes navigation lifecycle via automatic `<Activity>` | Re-audit every route, restore segment configs/`unstable_cache`, rewrite state-reset assumptions |
| 4 | Edge → Node runtime migration | 16.3 no longer supports Edge for pages/routes; Node-only APIs accrete | Runtime/API rewrite plus placement revalidation |
| 5 | 15.x `unstable_ViewTransition` UI | Import renamed, flag removed; codemod does not promise this case | Transition-by-transition manual migration |
| 6 | Mixed client-cache + RSC data ownership | SWR/TanStack owning truth alongside Server Actions creates two sources | Resource-by-resource ownership redesign |
| 7 | `"use cache: remote"` / custom `cacheHandlers` | Provider, network latency, deployment-keyed cache identity | Decommission provider, replace handler, accept cold cache |
| 8 | Canonical URL and 308 redirects | Persist in search engines and client caches | Another migration plus recrawl |
| 9 | Hard-coded `experimental.staleTimes` | Config reverts easily, but behaviour is experimental and may change without a deprecation window | Retest navigation freshness on every upgrade |
| 10 | CMS/schema or toolchain commitments (remote blur metadata, repo-wide barrel refactor, TypeScript 7) | Reversible only through migration labour | Schema cleanup, broad import churn, dependency downgrade |

## Fully reversible — safe to auto-apply

Config keys and props that delete cleanly: `next/font` options, `next/script` strategy
changes, `<Image>` prop corrections (`priority` → `fetchPriority`/`loading`), `sizes`
authoring, `images.*` allowlist entries, `next/dynamic` wrapping, `metadata` field
additions, JSON-LD blocks, `<Link>` prefetch tuning, 16.x `<ViewTransition>` wrappers and
their CSS, React hook adoption (`useTransition`, `useDeferredValue`, `useOptimistic`),
Suspense boundary placement, Turbopack config and cache flags, Web Vitals instrumentation.

## Component-level revert

`next-themes` provider architecture, theme attribute convention (`class` vs `data-*`),
locale-aware navigation wrappers at call sites, `@next/third-parties` wrappers, image
loader choice, React Compiler whole-app adoption *after* manual memoization was deleted,
`middleware.ts` → `proxy.ts` rename (codemod-assisted, forward-expected).

## Before flipping `cacheComponents` — pre-flight checklist

Emit this verbatim inside any task proposing Cache Components adoption. The task stays
`blocked-needs-human` until a human confirms these.

- [ ] Baseline p75 CWV and key navigation behaviour recorded (an observable before-state)
- [ ] Repo already on Next.js 16.0+ **without** Cache Components enabled in the same step
- [ ] Searched for `experimental.ppr`, `experimental_ppr`, `experimental.dynamicIO`,
      `experimental.useCache` — a 15.x PPR project is a separate go/no-go migration
- [ ] Every `runtime = 'edge'` export removed; route logic migrated to Node.js
- [ ] Inventoried `export const revalidate` / `dynamic` / `fetchCache`, `unstable_cache`,
      and `unstable_`-prefixed cache imports — these error or are superseded under the flag
- [ ] Located `cookies()`, `headers()`, `params`, `searchParams`, and uncached data above
      Suspense; static-shell vs dynamic-hole boundaries planned
- [ ] Decided how root `<html>` theme/locale attributes are produced — cookie-dependent
      root attributes **cannot** be Suspense-wrapped (`references/gating/conflicts.md` §6)
- [ ] Audited unmount-dependent UI: dropdowns, dialogs, mounted-form init, media,
      subscriptions, timers, post-submit resets, scroll restoration, E2E selectors
- [ ] Identified routes whose hidden DOM is too large to preserve (up to 3 routes retained)
- [ ] Decided whether cross-instance cache reuse is genuinely required before designing
      `"use cache: remote"` (provider failure, latency, purge, decommissioning)
- [ ] Confirmed static-shell data is reachable at request time — bots skip the shell and
      get a full request-time render
- [ ] Audited `generateMetadata`/`generateViewport` for the same runtime constraints
- [ ] Ready to use `instant = false` per failing route to regain a buildable app
- [ ] Not stacking new doors: `partialPrefetching`, custom `staleTimes`, experimental
      offline/testing flags, remote cache providers all stay off until the base is stable
- [ ] Skew Protection and rollback eligibility verified before changing RSC/Server Action
      contracts or navigation lifecycle in production

## Safe adoption order (keeps doors open longest)

**Greenfield:** fix public identity (origin, locale URL policy, canonical) → measurement +
rollback → reversible config/component wins → framework-native data ownership → confirm
Node runtime and data placement → Cache Components deliberately → navigation gains →
provider/experimental surfaces last.

**Mature production:** freeze external contracts (indexed URLs, canonicals, redirects,
image URLs, action payloads) → instrument and secure rollback → land fully reversible wins
→ resolve deprecations independently (Edge→Node, middleware→proxy, image/metadata renames,
`revalidateTag` arity) → clarify data ownership → migrate Cache Components as its own
program → only then Partial Prefetching and remote cache → change URL policy last, alone.

**Pinned-canary 15.x PPR adopter:** do not casually upgrade. Choose explicitly between
staying pinned and a full migration; while pinned, add no new dead-path surface.
