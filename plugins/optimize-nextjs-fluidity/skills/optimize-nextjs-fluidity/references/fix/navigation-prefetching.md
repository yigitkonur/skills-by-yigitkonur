# Fix: navigation-prefetching

**Corpus lineage:** navigation-prefetching/04-implementation-link-prefetch-patterns.md,
navigation-prefetching/05-implementation-instant-navigations.md,
navigation-prefetching/08-vercel-cost-practitioner-evidence.md
**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 docs. Confirm any
config key against the installed package first — see `references/gating/capability-probe.md`.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| `<Link>` prefetch strategy tuning | Next.js ≥1.0.0 | fully-reversible | Undifferentiated `prefetch` usage across nav/table/footer link types |
| Disabling prefetch on large/low-click link lists | Next.js ≥1.0.0 | fully-reversible | `<Link>` density inside `.map()` list/table renders with default prefetch |
| Programmatic `router.prefetch` + hover/intent prefetch | Next.js ≥1.0.0 (`onInvalidate` ≥15.4.0) | fully-reversible | Need for prefetch outside `<Link>`, or intent-based deferral |
| `useLinkStatus` inline pending affordance | Next.js ≥15.3.0 | fully-reversible | Links to latent routes with no inline pending UI |
| Partial Prefetching enablement — requires Next.js ≥16.3.0 AND cacheComponents | 16.3.0 + `cacheComponents` | migration-required (global adoption), fully-reversible (per-flag) | `partialPrefetching` absent/unset while `cacheComponents` is already on |
| `export const instant` / Stream-Cache-Block decision — requires Next.js ≥16.3.0 AND cacheComponents | 16.3.0 + `cacheComponents` | fully-reversible | Dev insight naming a blocking route, or a route needing deliberate Block |
| Migrating off hard-coded `staleTimes` to `cacheLife({ stale })` | Next.js ≥16.0.0 + `cacheComponents` | fully-reversible | `experimental.staleTimes` set in config under a `cacheComponents`-enabled app |
| `instant()` Playwright regression test — requires Next.js ≥16.3.0 AND cacheComponents | 16.3.0 + `@next/playwright` package | component-level-revert | No regression coverage for instant-navigation behavior |

## `<Link>` prefetch strategy tuning — requires Next.js ≥1.0.0

**When to apply:** repo mixes primary navigation, table-row, and footer links under one
undifferentiated default `prefetch` value.

```tsx
// app/ui/nav-link.tsx — Next.js 16.3.0
import Link from 'next/link'

export default function NavExamples() {
  return (
    <>
      {/* Primary nav item, high click-through: default 'auto' is enough. */}
      <Link href="/dashboard">Dashboard</Link>

      {/* High-intent, low-cardinality destination (checkout CTA): runtime
          prefetch is worth the server-invocation cost here. */}
      <Link href="/checkout" prefetch={true}>Checkout</Link>

      {/* Rarely clicked, low-value destination: never prefetch. */}
      <Link href="/terms" prefetch={false}>Terms</Link>
    </>
  )
}
```

**Why each non-obvious line exists:**
- `prefetch={true}` is reserved for high-intent, low-cardinality destinations — every
  visible instance costs "a server invocation per prefetchable link," so it must be scoped.
- `prefetch={false}` on `/terms` matches the documented low-click-destination guidance.
- The default is left as-is for `/dashboard` — it already prefetches static routes in full
  and dynamic routes down to the nearest `loading.js` boundary.

**Verify after applying:** open the Network tab in a production build (`next build && next
start` — prefetching is disabled in `next dev`). Confirm no request fires for
`prefetch={false}` links on scroll or hover, and `prefetch={true}` fires on viewport entry.

**Lock-in / reversibility:** fully-reversible — a per-link prop, revert any time.

**Rollback:** remove the explicit `prefetch` prop (or set back to `null`/omit).

## Disabling prefetch on large/low-click link lists — requires Next.js ≥1.0.0

**When to apply:** `<Link>` rendered inside `.map()` over a large or infinite-scroll
list/table with default prefetch active and no scoping.

```tsx
// app/ui/product-table-row.tsx — Next.js 16.3.0
import Link from 'next/link'

type Product = { id: string; slug: string; name: string }

export function ProductTableRows({ products }: { products: Product[] }) {
  return (
    <>
      {products.map((product) => (
        <tr key={product.id}>
          <td>
            {/* Large table: default viewport-triggered prefetch on every row
                multiplies request/bandwidth cost with no click-through
                guarantee. Disable entirely. */}
            <Link href={`/products/${product.slug}`} prefetch={false}>
              {product.name}
            </Link>
          </td>
        </tr>
      ))}
    </>
  )
}
```

**Why each non-obvious line exists:** `prefetch={false}` here is the documented fix for
exactly this shape — "prevent this to avoid unnecessary resource usage... rendering a large
list of links (e.g. an infinite scroll table)." Route-level `export const prefetch =
'force-disabled'` (see the Partial Prefetching recipe) is the equivalent fix at the
destination route when every link to that route should never prefetch, regardless of caller.

**Verify after applying:** scroll the list into view in the Network tab and confirm zero
prefetch requests for the disabled links; confirm hovering also triggers nothing.

**Lock-in / reversibility:** fully-reversible — remove the prop to restore default behavior.

**Rollback:** delete `prefetch={false}` from the affected `<Link>` elements.

## Programmatic `router.prefetch` + hover/intent prefetch — requires Next.js ≥1.0.0 (`onInvalidate` ≥15.4.0)

**When to apply:** need to prefetch outside a `<Link>`, or defer prefetch until real user
intent instead of viewport entry.

```tsx
// app/ui/hover-prefetch-link.tsx — Next.js 16.3.0
'use client'

import Link from 'next/link'
import { useState } from 'react'

export function HoverPrefetchLink({
  href,
  children,
}: {
  href: string
  children: React.ReactNode
}) {
  const [active, setActive] = useState(false)

  return (
    <Link href={href} prefetch={active ? null : false} onMouseEnter={() => setActive(true)}>
      {children}
    </Link>
  )
}
```

**Why each non-obvious line exists:** `prefetch={active ? null : false}` starts as `false`
(no viewport/hover prefetch from Next.js itself) and flips to `null` (restores default
behavior) only once `active` is true — a deferral, not a permanent disable.
`router.prefetch()` respects the same `static`/`dynamic` `staleTimes` split as `<Link>`; it
is not a separate cache lane. Guard any direct `router.prefetch()` call against re-firing on
every render (ref or effect-once) — an unguarded call in a frequently-rendering component
duplicates prefetch requests.

**Verify after applying:** open the Network tab and confirm the prefetch fires once per
hover, not once per render; check Instant Insights (16.3+) or the Network tab for
duplicate prefetch requests to the same route.

**Lock-in / reversibility:** fully-reversible — remove the wrapper, restore plain `<Link>`.

**Rollback:** delete the custom wrapper and replace call sites with `<Link href="...">`.

## `useLinkStatus` inline pending affordance — requires Next.js ≥15.3.0

**If the capability probe reports this key absent, do not emit this recipe — recommend a
version upgrade as its own separate task instead.**

**When to apply:** a link navigates to a route with real network latency and the UI gives no
feedback between click and the shell appearing.

```tsx
// app/ui/loading-link.tsx — Next.js 16.3.0
'use client'

import Link, { useLinkStatus } from 'next/link'

function LinkPendingIndicator() {
  const { pending } = useLinkStatus()
  return pending ? <span className="spinner" role="status" aria-label="Loading" /> : null
}

export function LoadingLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href}>
      {children}
      <LinkPendingIndicator />
    </Link>
  )
}
```

**Why each non-obvious line exists:** `useLinkStatus` must be called from a component
rendered *inside* the `<Link>` — it reports the pending state of its nearest ancestor
`<Link>`, not an arbitrary one. Not supported in the Pages Router — it always returns
`{ pending: false }` there, so this recipe is App Router only.

**Verify after applying:** throttle the network in DevTools, click the link, and confirm
the spinner renders between click and navigation completion, then disappears.

**Lock-in / reversibility:** fully-reversible — remove the hook and the indicator component.

**Rollback:** delete `LinkPendingIndicator` and its usage inside `<Link>`.

## Partial Prefetching enablement — requires Next.js ≥16.3.0 AND cacheComponents

**If the capability probe reports this key absent, do not emit this recipe — recommend a
version upgrade as its own separate task instead.**

**When to apply:** `cacheComponents: true` is already set (confirmed via probe, not this
domain's own recommendation) and `partialPrefetching` is absent or `false`, or the repo needs
incremental per-route adoption before the global flip.

```ts
// next.config.ts — Next.js 16.3.0
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  cacheComponents: true, // must already be true — prerequisite, not enabled by this recipe
  partialPrefetching: true,
}

export default nextConfig
```

Incremental per-route alternative, adopted before flipping the global flag, then cleaned up:

```tsx
// app/products/[slug]/page.tsx — Next.js 16.3.0
export const prefetch = 'partial' // opt this route in without the global flag
```

```bash
npx @next/codemod@canary remove-partial-prefetch ./app
```

**Why each non-obvious line exists:** `cacheComponents: true` is commented because it is a
**prerequisite check**, not something this recipe turns on — without it, `next dev`/`next
build` throw at config validation. The per-route `export const prefetch = 'partial'` step
lets a team adopt route-by-route and deploy incrementally instead of flipping the global
flag (and its blast radius) all at once. The codemod removes now-redundant per-route exports
once the global flag covers the same routes — skipping it leaves dead, confusing exports.

**Verify after applying:** open Next.js DevTools → Navigation Inspector → toggle "Pause on
navigations" → click a link; the panel should show "Loading shell" labeled "Client nav" with
source and target URLs. Confirm `next dev` throws a config-validation error if
`partialPrefetching: true` is set without `cacheComponents: true` (negative-path check).

**Lock-in / reversibility:** the global flag is a component/route-level revert during
incremental adoption but requires re-auditing every `<Link prefetch={true}>` call site
touched during rollout for a full rollback; per-route `export const prefetch` is
fully-reversible (delete the export).

**Rollback:** set `partialPrefetching: false` (or delete the key); re-add `prefetch={true}`
at any call site removed during adoption if dynamic content must still deliver pre-click.

## `export const instant` / Stream-Cache-Block decision — requires Next.js ≥16.3.0 AND cacheComponents

**If the capability probe reports this key absent, do not emit this recipe — recommend a
version upgrade as its own separate task instead.**

**When to apply:** a dev insight names a route as failing instant-navigation validation, or
a route (e.g. a blog post) must deliberately keep pre-16.3 blocking behavior.

```tsx
// app/dashboard/layout.tsx — Next.js 16.3.0
export const instant = false // Block: this segment is allowed to block on navigation
```

```tsx
// app/products/[slug]/page.tsx — Next.js 16.3.0
import { Suspense } from 'react'
import { ProductPrice } from './product-price'

async function getProductShell(slug: string) {
  'use cache' // Cache: ships as part of the instant shell
  return fetch(`https://api.example.com/products/${slug}/shell`).then((r) => r.json())
}

export default async function ProductPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const shell = await getProductShell(slug)

  return (
    <div>
      <h1>{shell.name}</h1>
      <img src={shell.image} alt={shell.name} />
      {/* Stream: dynamic price is not cached, wrapped so it doesn't block the shell above */}
      <Suspense fallback={<span>Loading price…</span>}>
        <ProductPrice slug={slug} />
      </Suspense>
    </div>
  )
}
```

**Why each non-obvious line exists:** `instant = false` set higher in the tree takes
precedence over any deeper `true` for the static-shell check — Block is a hard opt-out of
validation for that scope, and only works when `cacheComponents` is enabled (throws in
Client Components). `<Suspense>` wraps only the genuinely dynamic `<ProductPrice>`, not the
whole page — an over-broad boundary technically passes validation while replacing nearly all
real content with a single fallback on every navigation. `'use cache'` on `getProductShell`
is what actually ships inside the instant App Shell; without a cache or Suspense boundary,
the route has "nothing to prefetch" and behaves like pre-16.3 regardless of `instant`.

**Verify after applying:** in `next dev`, the dev overlay surfaces a blocking-route insight
naming the offending component; setting `instant = false` on that segment/its ancestor makes
the insight disappear for that scope. Re-navigate and check the Navigation Inspector shows
the expected shell content (name/image instantly, price behind a fallback).

**Lock-in / reversibility:** fully-reversible — delete the export, validation reverts to the
app-wide default.

**Rollback:** remove `export const instant = ...` from the affected page/layout.

## Migrating off hard-coded `staleTimes` to `cacheLife({ stale })` — requires Next.js ≥16.0.0 AND cacheComponents

**When to apply:** `experimental.staleTimes` is set in `next.config` on a repo that already
has `cacheComponents: true`. This is a stability-tier finding, not an availability one —
`staleTimes` still works, it has simply been experimental and production-discouraged since
v14.2.0, and `cacheLife`'s `stale` is the documented, recommended per-function replacement.

```js
// next.config.js — BEFORE: experimental, global, not recommended for production
/** @type {import('next').NextConfig} */
const nextConfig = {
  cacheComponents: true,
  experimental: { staleTimes: { dynamic: 30, static: 180 } },
}
module.exports = nextConfig
```

```tsx
// lib/data.ts — AFTER: per-function, stable, opt-in; staleTimes removed from config
import { cacheLife } from 'next/cache'

async function getData() {
  'use cache'
  cacheLife({ stale: 180 }) // matches the old static value, scoped to this function only
  return fetch('https://api.example.com/data').then((r) => r.json())
}
```

**Why each non-obvious line exists:** `cacheLife({ stale: 180 })` is called per-function,
not globally — the entire point of the migration. The value must be **≥30 seconds** to take
effect — the client router enforces a hard, non-configurable 30-second minimum stale time; a
`stale` value under 30s is excluded from prerenders entirely rather than silently rounded up,
because a prefetch would expire before the user could click. Leaving `staleTimes` unset
(deleted from config, not just changed) is intentional — it still acts as the fallback
default for any `cacheLife` profile that omits `stale`.

**Verify after applying:** in a production build, prefetch the route, wait less than the
configured `stale` window, and confirm a repeat client navigation reuses the cached router
entry (no new network request); wait past the window and confirm a fresh prefetch fires.

**Lock-in / reversibility:** fully-reversible — `cacheLife` is scoped to the function;
deleting the call and re-adding `experimental.staleTimes` restores the prior behavior.

**Rollback:** remove `cacheLife({ stale: N })` and re-add the equivalent
`experimental.staleTimes` block to `next.config`.

## `instant()` Playwright regression test — requires Next.js ≥16.3.0 AND cacheComponents

**If the capability probe reports this key absent, do not emit this recipe — recommend a
version upgrade as its own separate task instead.**

**When to apply:** no regression coverage exists for instant-navigation behavior — a future
change (an over-broad `<Suspense>` boundary, or a removed `'use cache'`) could silently
reintroduce a blocking navigation with no test catching it.

```bash
npm install -D @next/playwright @playwright/test
```

```ts
// e2e/navigation.test.ts — Next.js 16.3.0
import { test, expect } from '@playwright/test'
import { instant } from '@next/playwright'

test('is instant on a client navigation', async ({ page }) => {
  await page.goto('/store/shoes')
  await instant(page, async () => {
    await page.click('a[href="/store/hats"]')
    await page.waitForURL((url) => url.pathname === '/store/hats')
    await expect(page.locator('h1')).toContainText('Baseball Cap')
    await expect(page.getByText('In stock')).toHaveCount(0)
  })
  await expect(page.getByText('In stock')).toBeVisible()
})
```

```ts
// next.config.ts — Next.js 16.3.0 — required to run this test against a prod build in CI
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  cacheComponents: true,
  experimental: { exposeTestingApiInProductionBuild: true },
}

export default nextConfig
```

**Why each non-obvious line exists:** the `'In stock'` assertion checks zero-count *inside*
the `instant()` callback — proving it wasn't part of the instant shell — then asserts it
visible outside the callback, proving it eventually streams in. `exposeTestingApiInProductionBuild`
is required only for running this test against `next start` in CI — the testing API is
auto-enabled in `next dev`, but a production-build CI run needs the flag to expose it too.

**Verify after applying:** run the suite once BEFORE any instant-nav fix lands to confirm it
fails red — a test written after the fix proves nothing. Apply the fix, re-run to confirm
green.

**Lock-in / reversibility:** component-level-revert — remove the test file and the
`@next/playwright` dependency.

**Rollback:** `npm uninstall @next/playwright`; delete `e2e/navigation.test.ts`; remove
`experimental.exposeTestingApiInProductionBuild` from `next.config.ts`.

## Ordering within this domain

1. **Confirm `cacheComponents` is already on** (via probe) before proposing any 16.3-gated
   recipe here — Partial Prefetching enablement, `export const instant`/`prefetch`, or the
   `instant()` test. Never propose enabling `cacheComponents` from this domain; that belongs
   to `rendering-strategy-caching`.
2. **`cacheComponents` precedes Partial Prefetching**, which precedes per-route `export const
   instant`/`prefetch` fine-tuning, which precedes the `instant()` Playwright test — write
   the test against behavior that already exists, not behavior a later step will add.
3. **Tune `<Link>` prefetch strategy and disable-on-large-lists first** — always available
   (no version gate), and reduce cost immediately, independent of any 16.3 decision.
4. **Migrate `staleTimes` → `cacheLife` only after `cacheComponents` is confirmed on** — the
   recipe is invalid without it.

See `references/gating/priority-matrix.md` for how this domain's tasks sequence against
`rendering-strategy-caching` and `micro-interactions-react19-fluidity` at the plan level.

## Conflicts to watch

- **Runtime prefetching (`prefetch={true}`) cost vs Vercel billing.** Each visible
  `prefetch={true}` link under Partial Prefetching triggers a server invocation — scoping it
  broadly directly increases Active CPU / Edge Request cost. Cross-reference
  `references/gating/priority-matrix.md`'s SaaS/e-commerce guidance before recommending
  broad `prefetch={true}` adoption.
- **`export const instant = false` (Block) vs Partial Prefetching's intended payoff.**
  Applying Block liberally defeats the purpose of enabling `partialPrefetching` — reserve it
  for routes with a genuine product reason to stay server-bound, not as a default escape
  hatch from fixing Suspense/cache boundaries.
- **A View Transition layered on a route that still blocks/suspends.** If
  `page-transitions-view-transitions` is also in scope, sequence content-availability fixes
  (this domain) before choreography — see `references/gating/conflicts.md` §1.
