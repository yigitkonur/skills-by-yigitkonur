# Detect: navigation-prefetching

**Corpus lineage:** navigation-prefetching/00-overview-feature-inventory.md,
navigation-prefetching/03-when-to-use.md, navigation-prefetching/07-pitfalls-stability-lockin-seo.md,
navigation-prefetching/08-vercel-cost-practitioner-evidence.md

## Applicability gate

Most headline features in this domain shipped in **16.3.0** and do not exist on earlier
installs — a real probe against a 16.2.9 target returned `partialPrefetching → absent` and
`useOffline → absent` while `prefetchInlining`/`cachedNavigations` were `present`. Never
reason from the version string alone; always run
`scripts/probe-capabilities.py <repo-root>` first per `references/gating/capability-probe.md`.
This domain is the hardest gating case in the whole skill: a repo one 16.2.x patch behind
16.3.0 satisfies every documented prerequisite (`cacheComponents` on) and still cannot run
half the recipes in `references/fix/navigation-prefetching.md` — the probe, not arithmetic
on the version string, is the only thing that knows this.

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| `<Link>` `prefetch` prop (`'auto'`/`null`, `true`, `false`) | v1.0.0 (`'auto'` alias v15.4.0) | — | n/a | Always available on any supported Next.js version. No probe needed. |
| `router.prefetch()` (`useRouter`, `next/navigation`) | Pre-App-Router baseline; `onInvalidate` option added v15.4.0 | — | n/a | Always available. `onInvalidate` requires ≥15.4.0 — omit that option below the floor; verify installed version before recommending it. |
| `useLinkStatus` hook | v15.3.0 | — | n/a | Available ≥15.3.0. Below the floor: NOT APPLICABLE, no task. In the Pages Router it always returns `{ pending: false }` — do not recommend it there even on a qualifying version. |
| Layout-deduplicated prefetching | 16.0.0 | — | n/a | Default-on, automatic, ≥16.0.0. Nothing to configure — informational only, never a task by itself. |
| Incremental prefetching (fetch-only-what's-missing) | 16.0.0 | — | n/a | Default-on, automatic, ≥16.0.0. Informational only, never a task by itself. |
| `cacheComponents` (prerequisite flag) | 16.0.0 | Node.js runtime | n/a | **Prerequisite row.** Every row below this one is BLOCKED if `cacheComponents` is `absent` from the installed config schema or not set `true` in `next.config`. Full adoption mechanics are owned by `rendering-strategy-caching` — this domain only checks the gate, never recommends turning it on. |
| `partialPrefetching` (top-level `next.config.ts` key) | 16.3.0 | `cacheComponents: true` | n/a | Probe `node_modules/next/dist/server/config-schema.js` for `partialPrefetching`. `absent` → NOT APPLICABLE, emit no task (propose a version-upgrade task as its own separate item instead, never bundled into this one). `present` but `cacheComponents` unset → BLOCKED, emit the prerequisite finding first. |
| `export const instant` (route segment config) | 16.3.0 | `cacheComponents`; Server Components only | n/a | Probe installed version for 16.3.0 support. `absent` → NOT APPLICABLE, no task. Found in a `'use client'` file → this is itself a `critical` finding regardless of version (throws). |
| `export const prefetch` (route segment config: `'auto'`\|`'partial'`\|`'force-disabled'`) | 16.3.0 | `cacheComponents`; Server Components only | n/a | Same probe rule as `export const instant`. `absent` → NOT APPLICABLE, no task. |
| Instant Insights / Navigation Inspector (Next.js DevTools) | 16.3.0 | `cacheComponents` | n/a | Dev-only tool, not a code change — but still gated on the installed version. `absent` → NOT APPLICABLE; do not tell an agent to "check the Navigation Inspector" on a pre-16.3 install, it does not exist. |
| `experimental.instantInsights.validationLevel` | 16.3.0 | `cacheComponents` | n/a | Probe schema. `absent` → NOT APPLICABLE, no task. |
| `instant()` test helper (`@next/playwright`) | 16.3.0 | Next.js ≥16.3.0 AND the separate `@next/playwright` package | n/a | Probe both the installed Next.js version and whether `@next/playwright` is a declared dependency. Either `absent` → NOT APPLICABLE, no task. |
| `experimental.exposeTestingApiInProductionBuild` | 16.3.0 | Next.js ≥16.3.0 | n/a | Probe schema. `absent` → NOT APPLICABLE, no task. |
| `experimental.useOffline` config + `useOffline()` hook (`next/offline`) | 16.3.0 | Next.js ≥16.3.0 | n/a | Probe schema for `useOffline`. `absent` → NOT APPLICABLE, no task. Without the flag the hook always returns `false` — a repo importing it pre-16.3 has a dead import, not a working feature; flag that separately as a broken-import finding, not a "feature not adopted" finding. |
| `experimental.staleTimes` (`.dynamic`, `.static`) | 14.2.0 (introduced); dynamic default 30s→0s in 15.0.0 | — | n/a | Not a version-availability gate — a **stability-tier** gate. `present` and set to a non-default value → emit a `minor` migration finding per the staleness rule below. The justification is the experimental/production-discouraged tier, never absence. |
| `experimental.prefetchInlining` | 16.2.0 | — | n/a | Probe schema for the version floor. `absent` below 16.2.0 → NOT APPLICABLE. `present` and set → experimental-tier informational note, not a correctness issue. |
| `experimental.cachedNavigations` | 16.2.0 | `cacheComponents` | n/a | Probe schema. `absent` → NOT APPLICABLE. `present` without `cacheComponents` → BLOCKED. |

## Detection commands

Read-only only. Prefer `rg`; fall back to `grep -rn` if needed. Every command maps 1:1 to a
gate row or a pitfall signature below. Replace `<repo-root>` with the actual path.

```bash
# 1. <Link prefetch={true}> usage — candidate runtime-prefetching cost sites
rg -n 'prefetch=\{true\}' --glob '*.{tsx,jsx}' <repo-root>

# 2. <Link prefetch={false}> usage — review for correctness, not automatic findings
rg -n 'prefetch=\{false\}' --glob '*.{tsx,jsx}' <repo-root>

# 3. Density of <Link> inside list/table renders — flags unscoped prefetch at scale
rg -n -B2 '<Link\b' --glob '*.{tsx,jsx}' <repo-root> | rg -B2 '\.map\('

# 4. experimental.staleTimes hard-coded in config
rg -n 'staleTimes' --glob 'next.config.*' <repo-root>

# 5. partialPrefetching set (or absent) in the actual config file
rg -n 'partialPrefetching' --glob 'next.config.*' <repo-root>

# 6. cacheComponents state — determines whether every 16.3 row above is even reachable
rg -n 'cacheComponents' --glob 'next.config.*' <repo-root>

# 7. Programmatic prefetch call sites (and whether onInvalidate is used)
rg -n 'router\.prefetch\(' --glob '*.{ts,tsx}' <repo-root>

# 8. useLinkStatus adoption (or its absence on slow-network-prone links)
rg -n 'useLinkStatus' --glob '*.{ts,tsx}' <repo-root>

# 9. Existing route-segment adoption of the 16.3 config surface
rg -n "export const (instant|prefetch) *=" --glob '*.{ts,tsx}' <repo-root>

# 10. experimental.useOffline import/usage — must be paired with the config flag
rg -n "useOffline|from 'next/offline'" --glob '*.{ts,tsx}' <repo-root>
```

## Domain severity rubric

- **critical** — `partialPrefetching: true` set without `cacheComponents: true` (config
  validation throws at `next dev`/`next build`); `export const instant` or `export const
  prefetch` used inside a `'use client'` file (throws); hundreds of `<Link>`s in an
  infinite-scroll list left at default prefetch with no scoping and no `loading.js`
  boundary, on a route with genuinely dynamic content below the shell (unbounded
  request/bandwidth growth, user-visible or billing-visible breakage); a build hanging then
  failing with "Filling a cache during prerender timed out" traced to prefetch-adjacent
  `'use cache'` scopes.
- **major** — `<Link prefetch={true}>` applied broadly across a large/low-cardinality list
  (e.g. every row of a 50-item data table) instead of scoped to high-traffic nav — pays "a
  server invocation per prefetchable link" with no click-through to justify it; a route
  reached via `prefetch={true}` that hasn't opted into Partial Prefetching under
  `cacheComponents` (triggers the "dynamic data during prefetching" dev insight, ships
  slower/more expensive prefetches); analytics/tracking calls placed directly in a page or
  layout body (fires on prefetch, not visit — silently inflates counts); `params`/
  `searchParams` read outside a `<Suspense>` boundary on a route meant to share an App
  Shell across many links (breaks shell-sharing, triggers the "URL data outside of
  Suspense" insight).
- **minor** — `experimental.staleTimes` hard-coded under an app that already has
  `cacheComponents: true` (should migrate to `cacheLife({ stale })` — stability-tier issue,
  not a breakage); no `useLinkStatus` affordance on links to routes with real network
  latency (quality gap, not breakage); `experimental.prefetchInlining` or
  `cachedNavigations` set without any accompanying rationale comment; a custom `<Link>`
  wrapper duplicating built-in prefetch/hover logic instead of composing the default.
- **informational** — `prefetch={false}` on a large/low-click link list (this is the
  *correct* pattern, not a finding by itself — note it as confirmation the repo already
  applies the recommended mitigation); `cacheComponents` already `true` (note it, do not
  re-recommend enabling it — owned by `rendering-strategy-caching`); `experimental.viewTransition`
  present alongside prefetching code (belongs to `page-transitions-view-transitions`,
  cross-reference only); `router.bfcacheId`-based component keying present (belongs
  primarily to `micro-interactions-react19-fluidity`, note only).

## False-positive filters

- `prefetch={false}` on a long or infinite-scroll list is **correct** — a deliberate
  bandwidth optimization per the docs' own troubleshooting guidance ("You might want to
  prevent this to avoid unnecessary resource usage, such as when rendering a large list of
  links"). Do not flag it as a finding; log it as informational confirmation instead.
- Comments/docstrings mentioning `prefetch`, `staleTimes`, `partialPrefetching`, or
  `router.prefetch` do not count as live usage — grep matches inside `//` or `/* */` blocks
  are excluded.
- Test files (`*.test.tsx`, `*.spec.tsx`, `e2e/**`) are excluded from detection, except when
  auditing for the `instant()` Playwright recipe's own coverage (that check targets
  `e2e/**` deliberately, as the presence check, not a usage-violation check).
- A repo already on `cacheComponents: true` should not be told to enable it — that
  recommendation belongs to `rendering-strategy-caching`. This domain only checks whether
  it's on before gating the 16.3 rows above.
- A wrapper (native hover-defer pattern or a third-party library like ForesightJS) that sets
  `prefetch={false}` on every `<Link>` it wraps is a deliberate hand-off, not a finding —
  confirm the wrapper actually calls `router.prefetch()` (or an equivalent) itself before
  flagging anything as "prefetch disabled with no replacement."
- `prefetch` simply omitted (default `'auto'`/`null`) is normal, expected usage on ordinary
  content links — not itself a finding.
- `experimental.staleTimes` present in config with **default values only** (no explicit
  `dynamic`/`static` override, or values matching the framework defaults) is not a finding
  — the migration recipe targets non-default, load-bearing overrides.

## Evidence format — what each finding file must contain

Every finding the audit subagent writes under `findings/navigation-prefetching/` must
include:
- `file:line` (exact)
- literal matched text (copied from the `rg`/`grep` output)
- which gate row or pitfall signature it maps to
- severity
- one-line why-this-matters (verbatim or near-verbatim from the corpus-derived prose above)
- suggested fix recipe section name from `references/fix/navigation-prefetching.md`

## Pitfall signatures

| Failure signature | Cause | Fix direction | Recipe section |
|---|---|---|---|
| `next dev`/`next build` throws at config validation | `partialPrefetching: true` set without `cacheComponents: true` | Add `cacheComponents: true` first (owned by `rendering-strategy-caching`), then re-enable `partialPrefetching` | Partial Prefetching enablement |
| Dev overlay: "dynamic data during prefetching," naming a route reached via `<Link prefetch={true}>` | Route hasn't opted into Partial Prefetching under Cache Components; `prefetch={true}` reverts to legacy full prefetch, pulling dynamic data with the shell | Opt the route in (`export const prefetch = 'partial'` or the global flag), remove `prefetch={true}`, or `export const instant = false` | Partial Prefetching enablement / `export const instant` decision |
| Dev insight: "URL data outside of Suspense" | `params`/`searchParams` read outside a `<Suspense>` boundary, tying the shell to one specific URL | Move the read into a child component wrapped in `<Suspense>`, keep the parent static | `export const instant` / Stream-Cache-Block decision |
| Build hangs ~50s then: "Filling a cache during prerender timed out" | A `'use cache'` scope awaits a Promise that resolves to uncached/runtime data (e.g. an unresolved `cookies()` Promise) created outside the cache boundary | Await runtime-data Promises in the dynamic component before passing resolved values (not Promises) into the cached scope | `export const instant` / Stream-Cache-Block decision |
| Suspense fallback replaces nearly the whole page on every navigation, even though validation passes | `<Suspense>` boundary placed too high in the tree (wraps the entire page) | Push the boundary down to wrap only the genuinely dynamic subtree | `export const instant` / Stream-Cache-Block decision |
| Analytics event count inflated vs actual visits | Side-effect (e.g. `trackPageView()`) placed directly in a page/layout body — fires on prefetch, not on visit | Move the call into `useEffect`, or a Server Action triggered from a Client Component | `<Link>` prefetch strategy tuning |
| Outgoing bandwidth spikes on a link-heavy static page | Default viewport-triggered prefetch fires for every visible link, unscoped | `prefetch={false}` on low-click links, hover-deferred prefetch, or `export const prefetch = 'force-disabled'` at the destination | Disabling prefetch on large/low-click link lists |
| Navigation Inspector shows stale/frozen state across unrelated local Next.js projects | The `next-instant-navigation-testing` cookie is scoped to the domain, not the port, so multiple `localhost` projects share it | Clear the cookie or close the Navigation Inspector panel when switching projects | (informational only — no recipe; note for the fixer) |

## Cross-domain interactions

1. If `cacheComponents` is `absent` or unset, skip every Partial Prefetching finding
   (`partialPrefetching`, `export const instant`, `export const prefetch`, Instant Insights,
   `instantInsights.validationLevel`) and downgrade them to NOT APPLICABLE — never recommend
   turning `cacheComponents` on from this domain; that belongs to `rendering-strategy-caching`.
2. `<Link transitionTypes>` (v16.2.0) feeds `page-transitions-view-transitions` — note its
   presence/absence only as informational context for that domain, not as a finding here.
3. `<Activity>`-based Client Component state preservation across navigations (enabled by
   `cacheComponents`) is owned by `micro-interactions-react19-fluidity`. This domain only
   notes `router.bfcacheId` as the router-cache-adjacent API; it does not own the full
   preservation mechanism.

## Reference pointer

Fix recipes for this domain live in `references/fix/navigation-prefetching.md`.
