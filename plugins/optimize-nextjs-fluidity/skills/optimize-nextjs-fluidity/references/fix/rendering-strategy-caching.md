# Fix: rendering-strategy-caching

**Corpus lineage:** rendering-strategy-caching/04-implementation-use-cache-directives.md,
rendering-strategy-caching/05-implementation-cachelife-revalidation-migration.md,
rendering-strategy-caching/06-suspense-pattern-tradeoffs.md, rendering-strategy-caching/08-version-lockin-seo-vercel.md
**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 docs. Confirm any
config key against the installed package first — see `references/gating/capability-probe.md`.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| Enable Cache Components | Next.js ≥16.0.0, Node.js runtime everywhere | `migration-required` | `cacheComponents` absent, project would benefit from static-shell/dynamic-hole model |
| `"use cache"` + `cacheLife` | `cacheComponents: true` | `fully-reversible` | Scope missing explicit `cacheLife`; uncached shareable data above `<Suspense>` |
| `"use cache: private"` | `cacheComponents: true` | `fully-reversible` | Function needs `cookies()`/`headers()`/`searchParams` inside a cached scope |
| `"use cache: remote"` | `cacheComponents: true`, `cacheHandlers.remote` configured | `component-level-revert` | "works locally, nothing on Vercel" pitfall; serverless cold-start cache misses |
| `cacheTag` + `revalidateTag`/`updateTag`/`refresh` | `cacheComponents: true` | `fully-reversible` | Single-arg `revalidateTag(tag)` calls; missing invalidation after a mutation |
| Static shell + `<Suspense>` dynamic-hole pattern | `cacheComponents: true` | `fully-reversible` | `blocking-route` build/dev error; uncached data read above `<Suspense>` |
| 15→16 migration (legacy flags, segment exports, `unstable_cache`) | Next.js ≥16.0.0 | `component-level-revert` | `experimental.ppr`/`dynamicIO`/`useCache` present; legacy segment exports; `unstable_cache(...)` |
| `instant = false` escape hatch | `cacheComponents: true` | `fully-reversible` | A route fails to prerender mid-migration, needs to build now |

## Enable Cache Components — requires Next.js ≥16.0.0, Node.js runtime

**When to apply:** `cacheComponents` absent on an install ≥16.0.0 and the repo's data shape
(per `references/gating/priority-matrix.md` archetype scoring) benefits from a static shell.

**Status: `migration-required` — never auto-apply.** This inverts the caching model from
cached-by-default to dynamic-by-default, requires the Node.js runtime everywhere, and
auto-wires React `<Activity>` navigation-state preservation — silently changing dropdown,
dialog, and post-submit-form behavior that assumed unmount-based reset. The full pre-flight
checklist lives in `references/gating/lockin-reversibility.md` (`## Before flipping
cacheComponents`). Emit that checklist verbatim inside the task and leave it
`Status: blocked-needs-human`; do not attempt to satisfy it programmatically.

```ts
// next.config.ts — Next.js 16.0.0+
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  cacheComponents: true,
}

export default nextConfig
```

**Why each non-obvious line exists:**
- `cacheComponents: true` is the single master switch — unifies the old standalone `ppr`,
  `useCache`, and `dynamicIO` flags. It is repo-wide; there is no partial per-route enable.
- Setting this flag makes `runtime = 'edge'` a hard build blocker — resolve every Edge route
  first (dependency graph: Edge-runtime removal precedes `cacheComponents`).

**Verify after applying:** `next build` completes. Any route still exporting `dynamic`,
`revalidate`, or `fetchCache` now **errors** — documented, expected; resolve with the 15→16
migration recipe before declaring this step done.

**Lock-in / reversibility:** `migration-required`. Exit cost: re-audit every route for
removed segment-config errors, re-add `unstable_cache` wrappers, lose `partialPrefetching`/
auto-`<Activity>`. A project that adopted `experimental.ppr` on a 15.x canary cannot use this
recipe at all — one-way door, no in-place path (stay pinned, or full rewrite); see
`references/gating/lockin-reversibility.md` #1.

**Rollback:** delete the `cacheComponents: true` line. Re-add whichever route segment
exports and `unstable_cache` wrappers were removed during migration — the pre-16 model is a
fully supported, coexisting path, not deprecated.

## "use cache" + `cacheLife` — requires Next.js ≥16.0.0, `cacheComponents: true`

**When to apply:** a `"use cache"` scope has no explicit `cacheLife`, or shareable data (DB
query, upstream API with no per-user variance) is fetched with no cache directive.

```tsx
// app/lib/data.ts — Next.js 16.0.0+
import { cacheLife, cacheTag } from 'next/cache'

export async function getProducts() {
  'use cache'
  cacheTag('products')
  cacheLife('hours')
  const res = await fetch('/api/products')
  return res.json()
}
```

The directive is valid at file, component, or function level — place it at the **function**
level, closest to the data fetch, unless caching an entire route (then apply `"use cache"`
to *both* `layout.tsx` and `page.tsx`; each segment caches independently). Every function or
component carrying `"use cache"` must be `async` — a sync function with the directive is a
build error.

**Why each non-obvious line exists:**
- `cacheTag('products')` — enables targeted invalidation via `revalidateTag`/`updateTag`
  instead of clearing the whole cache.
- `cacheLife('hours')` — makes the lifetime explicit at the call site. Omitting it silently
  applies `default` (5 min stale / 15 min revalidate / never expires): "We recommend setting
  a `cacheLife` in every `use cache` scope so its behavior is clear at the call site."

Built-in `cacheLife` profiles (pick by data volatility):

| Profile | Use case | `stale` | `revalidate` | `expire` |
|---|---|---|---|---|
| `default` | Standard content | 5 min | 15 min | never |
| `seconds` | Real-time data | 30 sec | 1 sec | 1 min |
| `minutes` | Frequently updated | 5 min | 1 min | 1 hour |
| `hours` | Updated multiple times/day | 5 min | 1 hour | 1 day |
| `days` | Updated daily | 5 min | 1 day | 1 week |
| `weeks` | Updated weekly | 5 min | 1 week | 30 days |
| `max` | Stable, rarely changes | 5 min | 30 days | 1 year |

A custom named profile can be defined once in `next.config.ts` under a `cacheLife` object
(e.g. `biweekly: { stale, revalidate, expire }`) and referenced everywhere by name
(`cacheLife('biweekly')`); or pass an object directly to `cacheLife({ stale, revalidate,
expire })` for a one-off — omitted properties inherit from `default`.

**Prerendering thresholds — what decides static-shell membership:** `revalidate: 0` or
`expire` under 5 minutes excludes a scope from prerendering (it becomes a dynamic hole,
resolved at request time). `stale` under 30 seconds also excludes it — a prefetch would
expire before the user could click. `stale` between 30 seconds and 5 minutes is included in
prerenders but excluded from the App Shell. Of the presets, only `seconds` crosses the
5-minute `expire` threshold.

**Verify after applying:** in dev, set `NEXT_PRIVATE_DEBUG_CACHE=1` — cached-function console
output shows a `Cache` prefix. `next build` succeeds with no `blocking-route` insight naming
this function.

**Lock-in / reversibility:** `fully-reversible`. Delete the `"use cache"` line, `cacheLife`
call, and `cacheTag` call to return the function to plain dynamic execution.

**Rollback:** remove the `'use cache'` directive, `cacheLife(...)`, and `cacheTag(...)`
calls; remove the now-unused `next/cache` import.

## "use cache: private" — requires Next.js ≥16.0.0, `cacheComponents: true`

**When to apply:** a function needs `cookies()`, `headers()`, or `searchParams` inside a
cached scope — plain `"use cache"` forbids all three.

**What it costs / when to reach for it:** results are never stored on the server — cached
only in the browser's memory, per-client, and don't persist across reloads. Use for
session-scoped personalization where data must never be shared across users. Not available
in Route Handlers. `stale` must be ≥30s for runtime prefetching, ≥5min to join the App Shell.

| API | Allowed in `use cache` | Allowed in `use cache: private` |
|---|---|---|
| `cookies()` | No | Yes |
| `headers()` | No | Yes |
| `searchParams` | No | Yes |
| `connection()` | No | No |

```tsx
// app/product/[id]/page.tsx — Next.js 16.0.0+
import { Suspense } from 'react'
import { cookies } from 'next/headers'
import { cacheLife, cacheTag } from 'next/cache'

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return (
    <div>
      <ProductDetails id={id} />
      <Suspense fallback={<div>Loading recommendations...</div>}>
        <Recommendations productId={id} />
      </Suspense>
    </div>
  )
}

async function Recommendations({ productId }: { productId: string }) {
  return <RecommendationsList items={await getRecommendations(productId)} />
}

async function getRecommendations(productId: string) {
  'use cache: private'
  cacheTag(`recommendations-${productId}`)
  cacheLife({ stale: 60 })
  // Access cookies within a private cache function — NOT allowed in plain "use cache"
  const sessionId = (await cookies()).get('session-id')?.value || 'guest'
  return getPersonalizedRecommendations(productId, sessionId)
}
```

**Why each non-obvious line exists:**
- `'use cache: private'` on `getRecommendations` (not the page) keeps the request-API read
  as narrow as possible so the rest of `ProductPage` can still prerender.
- `cacheLife({ stale: 60 })` clears the 30s runtime-prefetching floor but stays under the
  5min App-Shell floor — correct, since this data must not join the shared shell.

**Verify after applying:** confirm the function executes on every server render (excluded
from static-shell generation by design) and `next build` raises no server-persistence error.

**Lock-in / reversibility:** `fully-reversible`. Switching back to `'use cache'` requires
first removing every `cookies()`/`headers()`/`searchParams` read from the function body.

**Rollback:** change the directive to `'use cache'` only after removing request-API reads;
otherwise the build errors.

## "use cache: remote" — requires Next.js ≥16.0.0, `cacheComponents: true`, `cacheHandlers.remote`

**When to apply:** the "works locally, does nothing on Vercel production" pitfall signature
matches, or a `"use cache"` function backs a shared upstream hit by many serverless instances.

**What it costs / when to reach for it:** stores entries in a durable, shared remote handler
(Redis/KV/etc.) so they survive across serverless instances. Costs: infrastructure (storage,
network) and lookup latency. Necessary because the default `"use cache"` in-memory handler
does not persist across serverless instances — a cold instance is always a cache miss (Next.js
collaborator, GitHub Discussion vercel/next.js#87842). This is documented, expected
behavior — not a bug to route around with `unstable_cache`.

```tsx
// app/dashboard/page.tsx — Next.js 16.0.0+
import { Suspense } from 'react'
import { connection } from 'next/server'
import { cacheLife, cacheTag } from 'next/cache'

export default function DashboardPage() {
  return (
    <Suspense fallback={<div>Loading stats...</div>}>
      <DashboardStats />
    </Suspense>
  )
}

async function DashboardStats() {
  await connection() // defers to request time — appropriate for live aggregate stats
  return <StatsDisplay stats={await getGlobalStats()} />
}

async function getGlobalStats() {
  'use cache: remote'
  cacheTag('global-stats')
  cacheLife({ expire: 60 }) // 1 min — bounds staleness, collapses concurrent hits into one/min
  return db.analytics.aggregate({ total_users: 'count', active_sessions: 'count', revenue: 'sum' })
}
```

**Why each non-obvious line exists:**
- `await connection()` in `DashboardStats` defers it to request time so it doesn't join the
  static shell — live aggregate stats shouldn't be prerendered.
- `'use cache: remote'` (not `'use cache'`) on `getGlobalStats` — this is the function that
  hits the shared upstream database; it needs cross-instance persistence. Result: "your
  upstream database sees at most one request per minute, regardless of how many users visit."

| Feature | `use cache` | `use cache: remote` | `use cache: private` |
|---|---|---|---|
| Cache scope | Shared, all users | Shared, all users | Per-client (browser) |
| Cookies/headers direct access | No | No | Yes |
| Cache utilization | Low outside static shell | High (shared instances) | N/A |
| Extra cost | None | Infra (storage, network) | None |

Nesting: remote **can** nest inside other remote caches and inside `"use cache"`; remote and
private **cannot** nest inside each other. Configure via `cacheHandlers.remote` in
`next.config.ts` (self-hosted); on Vercel this is expected to be platform-provided — the
exact managed-handler name is unconfirmed, so verify by observing cross-instance cache hits
directly, don't assume.

**Verify after applying:** run 2+ local instances or restarts and confirm entries survive.
Call `revalidateTag`/`updateTag` on one instance and confirm invalidation propagates — this
requires distributed coordination logic; the default in-memory handler does not do this.

**Lock-in / reversibility:** `component-level-revert`. Exit cost: standing up (and later
decommissioning) the backing store; cached data becomes unreachable once unreferenced, no
forced migration to revert.

**Rollback:** change the directive back to `'use cache'` (accepting in-memory,
per-instance-only caching); remove the `cacheHandlers.remote` config entry if unused elsewhere.

## `cacheTag` + `revalidateTag`/`updateTag`/`refresh` — requires Next.js ≥16.0.0, `cacheComponents: true`

**When to apply:** a single-argument `revalidateTag(tag)` call is present, or a mutation
(Server Action) has no invalidation path for the data it just changed.

`cacheTag('tag-one', 'tag-two')` accepts multiple tags per call; up to 128 tags, 256
characters each — over either limit, extras are silently skipped with a console warning.

**`revalidateTag` — the breaking arity change (deprecated single-arg form):**

```ts
// app/actions.ts — Next.js 16.0.0+
'use server'
import { revalidateTag } from 'next/cache'

export default async function submit() {
  await addPost()
  // Before (deprecated, TS error on 16): revalidateTag('posts')
  revalidateTag('posts', 'max') // 'max' = stale-while-revalidate; recommended default
}
```

Signature: `revalidateTag(tag: string, profile: string | { expire?: number }): void`. It
does not invalidate everywhere immediately — "the invalidation only happens when any page
using that tag is next visited." For webhooks needing immediate expiration, pass
`revalidateTag(tag, { expire: 0 })` instead of `'max'`; otherwise prefer `updateTag`.

**`updateTag` — read-your-own-writes, Server Actions only:**

```ts
// app/actions.ts — Next.js 16.0.0+
'use server'
import { updateTag } from 'next/cache'
import { redirect } from 'next/navigation'

export async function createPost(formData: FormData) {
  const post = await db.post.create({ data: { title: formData.get('title'), content: formData.get('content') } })
  updateTag('posts')            // affects any page listing posts
  updateTag(`post-${post.id}`)  // affects the individual post detail page
  redirect(`/posts/${post.id}`) // user sees fresh data, not cached
}
```

`updateTag` throws outside Server Actions (Route Handlers, Client Components). Unlike
`revalidateTag('tag', 'max')` (stale-while-revalidate), it makes the next request wait for
genuinely fresh data — use it when the user must immediately see their own write.

**`refresh()` — uncached-data-only, Server Actions only:** refreshes genuinely uncached data
displayed elsewhere on the page (a notification count, live metric) — it never touches a
`"use cache"` entry. Call it the same way, from a Server Action, after the mutation
(`import { refresh } from 'next/cache'; refresh()`). If cached data isn't updating after
calling it, that's the wrong function — use `updateTag`/`revalidateTag` instead.

**Verify after applying:** remaining single-arg `revalidateTag(tag)` calls now surface a
TypeScript error. `updateTag`/`refresh` called from a Route Handler or Client Component
throws — confirm this fails loudly in tests, not silently.

**Lock-in / reversibility:** `fully-reversible`. The single-arg form still works today with
TS errors suppressed but is explicitly time-bounded for removal — migrate proactively.

**Rollback:** revert to the single-argument call if truly necessary (not recommended);
revert `updateTag`/`refresh` calls by deleting them and restoring the prior invalidation path.

## Static shell + `<Suspense>` dynamic-hole pattern — requires Next.js ≥16.0.0, `cacheComponents: true`

**When to apply:** the `blocking-route` pitfall signature matches ("Uncached data was
accessed outside of `<Suspense>`"), or a page mixes static, cached, and per-request content.

```tsx
// app/blog/page.tsx — Next.js 16.0.0+
import { Suspense } from 'react'
import { cookies } from 'next/headers'
import { cacheLife, cacheTag } from 'next/cache'
import Link from 'next/link'

export default function BlogPage() {
  return (
    <>
      {/* Static — prerendered automatically, part of the shell */}
      <header><h1>Our Blog</h1><nav><Link href="/">Home</Link></nav></header>

      {/* Cached dynamic — included in the static shell */}
      <BlogPosts />

      {/* Runtime dynamic — streams at request time */}
      <Suspense fallback={<p>Loading your preferences...</p>}>
        <UserPreferences />
      </Suspense>
    </>
  )
}

// Everyone sees the same posts (revalidated hourly)
async function BlogPosts() {
  'use cache'
  cacheLife('hours')
  cacheTag('posts')
  const posts: { id: string; title: string }[] = await (await fetch('https://api.vercel.app/blog')).json()
  return <ul>{posts.map((p) => <li key={p.id}>{p.title}</li>)}</ul>
}

// Genuinely per-request — depends on cookies
async function UserPreferences() {
  const theme = (await cookies()).get('theme')?.value || 'light'
  return <aside><p>Your theme: {theme}</p></aside>
}
```

**Why each non-obvious line exists:**
- `BlogPosts` is called directly (not Suspense-wrapped) — as a `"use cache"` scope it joins
  the static shell without needing a boundary; reading `cookies()` in a *different*
  component doesn't opt the whole route into dynamic rendering the way pre-16 did.
- `UserPreferences` is Suspense-wrapped because it reads `cookies()` directly — this
  boundary is what lets the header and posts still ship in the initial HTML.

**Maximizing the shell — push runtime reads as deep as possible.** A layout that destructures
a dynamic `params` value at the top blocks the *whole* layout from prerendering. Fix: pass
the promise down and resolve it only inside a Suspense-wrapped leaf component instead of
`await`-ing `params` directly in the layout body. The same principle applies to `cookies()`,
`headers()`, `searchParams`, and any data fetch — push the async read as far down the tree
as possible before wrapping in `<Suspense>`.

**Random values / timestamps under prerendering:** `Math.random()`, `Date.now()`, and
`crypto.randomUUID()` require either `await connection()` + `<Suspense>` (genuinely unique
per request) or a `"use cache"` wrap (same value for every user until revalidation).
`performance.now()` does not require this treatment — it's telemetry, not guarded.

**Verify after applying:** in the network tab, confirm the initial HTML already contains the
static/cached content; confirm the fallback appears briefly before the streamed swap. A
`blocking-prerender-random`/`-current-time`/`-crypto` build error names the missing guard.

**Lock-in / reversibility:** `fully-reversible`. Removing a `<Suspense>` boundary and
inlining the component reverts the structure — the route may then fail to build under
`cacheComponents` if the component reads a request-time API, which is expected.

**Rollback:** remove the `<Suspense>` wrapper and inline the component directly. If this
reintroduces a `blocking-route` error, that confirms the boundary was load-bearing.

## 15→16 migration — legacy flags, segment exports, `unstable_cache` — requires Next.js ≥16.0.0

**When to apply:** `experimental.ppr`/`experimental_ppr`, `experimental.dynamicIO`,
`experimental.useCache`, `unstable_cacheLife`/`unstable_cacheTag`, legacy `export const
revalidate`/`dynamic`/`fetchCache`, or `unstable_cache(...)` present on a project on or
adopting Next.js 16.

**`experimental.ppr` is the sharpest one-way door in this domain.** Confirm via the
capability probe that this project never adopted `experimental.ppr` on a 15.x canary before
touching it. If it did, this is **not** a mechanical cleanup: "PPR in Next.js 16 works
differently than in Next.js 15 canaries. If you are using PPR today, stay in the current
Next.js 15 canary you are using." No flag, codemod, or shim reproduces 15.x PPR semantics
under 16.x. Route this case to a human go/no-go decision, not this recipe.

```js
// next.config.js — Before (14.x/15.x, EXPERIMENTAL, REMOVED in 16)
module.exports = { experimental: { ppr: true } } // or experimental_ppr: true at route level
```

```ts
// next.config.ts — After (Next.js 16.0.0+)
const nextConfig: NextConfig = {
  cacheComponents: true, // PPR is now the default behavior of this flag, not a separate opt-in
}
export default nextConfig
```

Codemods remove the dead route-segment exports automatically:

```bash
npx @next/codemod@canary cache-components-instant-false ./app
```

**Legacy segment exports.** `export const dynamic = 'force-dynamic'` needs no replacement —
just delete it, all pages are dynamic by default under `cacheComponents`. `export const
revalidate = 3600` and inline `fetch(url, { cache: 'force-cache', next: { revalidate: 3600,
tags: ['data'] } })` both collapse into a cached function:

```tsx
// app/lib/data.ts — Next.js 16.0.0+
import { cacheLife, cacheTag } from 'next/cache'

async function getData() {
  'use cache'
  cacheLife('hours')
  cacheTag('data')
  const res = await fetch('https://api.example.com/data')
  return res.json()
}
```

**`unstable_cache` migration** — the key-parts array (e.g. `['user']`) is no longer needed;
Next.js derives cache keys automatically from serializable arguments:

```tsx
// app/lib/data.ts — Next.js 16.0.0+, replaces
// unstable_cache(fn, ['user'], { tags: ['users'], revalidate: 3600 })
import { cacheLife, cacheTag } from 'next/cache'

export async function getUser(id: string) {
  'use cache'
  cacheLife('hours')
  cacheTag('users')
  return db.query.users.findFirst({ where: eq(users.id, id) })
}
```

**`unstable_noStore()`** is simply deleted — dynamic is already the default under
`cacheComponents`, so the opt-out call has nothing left to opt out of.

**Important nuance — not purely mechanical:** the classic `fetch` Data Cache persists across
deployments and serverless instances; `"use cache"` defaults to in-memory storage, scoped to
a single deployment. Migrating `fetch(..., { cache: 'force-cache' })` to a bare `"use cache"`
function on Vercel is a real behavior change, not a rename — evaluate whether it needs
`"use cache: remote"` instead.

**Verify after applying:** `rg -n "experimental_ppr|ppr\s*:"` returns nothing; `next build`
no longer warns about the deprecated flag or errors on any legacy segment export.

**Lock-in / reversibility:** `component-level-revert`. Each call site reverts mechanically
(restore the old export or `unstable_cache` wrapper), but the sweep touches every affected
route — treat it as one coordinated task per the "cluster, don't enumerate" rule, not N tasks.

**Rollback:** restore the deleted segment-config exports, re-wrap in `unstable_cache(...)`
with its original key-parts array, and (if reverting `cacheComponents` itself) set the flag
back to `false`.

## `instant = false` escape hatch — requires Next.js ≥16.0.0, `cacheComponents: true`

**When to apply:** a route fails to prerender mid-migration (`blocking-route` or similar)
and the app needs to build and ship before that route's caching strategy is fully resolved.

```tsx
// app/dashboard/layout.tsx — Next.js 16.0.0+
export const instant = false
```

```bash
npx @next/codemod@canary cache-components-instant-false ./app
```

**Why this line exists:** `instant = false` marks a segment as *allowed to block* — it does
not force the route to become fully dynamic, and it does not silence synchronous-IO build
errors (`new Date()`, `Math.random()`, `crypto.randomUUID()` still fail the prerender). It is
narrowly a release valve for the `blocking-route` error class, not a general escape hatch.

**Verify after applying:** `next build` succeeds; the dev overlay shows no more
`blocking-route` insights on production-critical routes. Track every `instant = false`
segment as an open item — the migration isn't complete while any remain.

**Lock-in / reversibility:** `fully-reversible`. Remove the export once the segment's
caching strategy is resolved via the `"use cache"` or Suspense recipes above.

**Rollback:** delete `export const instant = false`. If the underlying `blocking-route`
cause was never fixed, the build fails again immediately — that's the correct signal.

## Ordering within this domain

1. **Clear the Node.js-runtime prerequisite first.** Remove every `runtime = 'edge'` export
   before touching `cacheComponents` — never bundle this into the same task as the flag.
2. **Resolve the `experimental.ppr` go/no-go decision before any other step**, if it applies.
3. **Enable `cacheComponents` only after** the pre-flight checklist in
   `references/gating/lockin-reversibility.md` is confirmed by a human — never auto-applied.
4. **Use `instant = false` to regain a buildable app** immediately after flipping the flag.
5. **Migrate routes one at a time:** legacy segment exports and `unstable_cache` first
   (mechanical), then `"use cache"`/`cacheLife`/`cacheTag` deliberately, removing
   `instant = false` as each route is verified.
6. **Add `"use cache: remote"` and `partialPrefetching` only after** the base migration is
   stable — both are additive, not required for `cacheComponents` itself.

## Conflicts to watch

- **Root `<html>` attributes depending on `cookies()`/`headers()` (theme, locale) cannot be
  Suspense-wrapped.** Don't propose wrapping the root layout in `<Suspense>` for a
  `blocking-route` error originating there — resolve via `dark-light-theme-switching` /
  `instant-i18n-locale-switching` recipes instead.
- **A View Transition added to a route that still suspends animates into a loading
  fallback** — polished but wrong. Make the destination cache-hot (this domain) before
  layering `page-transitions-view-transitions` work on top.
- **Automatic `<Activity>` wiring changes the baseline for `micro-interactions-react19-fluidity`
  findings** — any task there proposing unmount-based state reset is invalid once
  `cacheComponents` is on; route those findings back to this domain's pre-flight checklist.
